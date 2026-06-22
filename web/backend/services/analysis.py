from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, Iterable, List, Optional
import io
import chess
import chess.pgn

from src.core.chess_game import ChessGame
from src.analysis.move_classifier import MoveClassifier
from ..managers.engine_manager import EngineManager

# Analysis parameters (single source of truth for both the live and batch paths).
ANALYSIS_DEPTH = 16
ANALYSIS_MULTIPV = 3
MATE_SCORE = 10000

# Singleton instances for helpers can be created here
move_classifier = MoveClassifier()


def degraded_insight(
    move: chess.Move,
    board_before: chess.Board,
    side: str,
    opening_info: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Fallback insight when no engine is available (Stockfish missing)."""
    return {
        "move_num": (len(board_before.move_stack) // 2) + 1,
        "side": side,
        "san": board_before.san(move),
        "uci": move.uci(),
        "classification": "Inconnu",
        "move_quality": 0.5,
        "score_before": 0.0,
        "score_after": 0.0,
        "opening": opening_info,
    }


def build_insight(
    move: chess.Move,
    board_before: chess.Board,
    side: str,
    alt_info: List[Dict[str, Any]],
    after_list: List[Dict[str, Any]],
    opening_info: Optional[Dict[str, Any]],
    is_opening_move: bool,
) -> Dict[str, Any]:
    """Pure insight builder.

    Given the precomputed engine analyses of the position BEFORE the move (multipv,
    `alt_info`) and AFTER the move (`after_list`), plus the opening context, produce
    the move insight. Touches NO engine and NO mutable game state — safe to call
    after a parallel analysis pass and from any thread.
    """
    move_num = (len(board_before.move_stack) // 2) + 1
    san = board_before.san(move)

    # Score change (mate_score matches the engine config).
    prev_score_white = alt_info[0]["score"].white().score(mate_score=MATE_SCORE) / 100
    score_after_white = after_list[0]["score"].white().score(mate_score=MATE_SCORE) / 100

    if side == "White":
        prev_score = prev_score_white
        score_after = score_after_white
    else:
        prev_score = -prev_score_white
        score_after = -score_after_white

    player_move_rank = -1
    player_move_score = score_after
    best_score = None
    top_moves_eval_drop = 0.0
    position_complexity = 0.0

    if alt_info:
        top_score_white = alt_info[0]["score"].white().score(mate_score=MATE_SCORE) / 100
        best_score = top_score_white if side == "White" else -top_score_white

        for idx, analysis in enumerate(alt_info):
            if "pv" in analysis and analysis["pv"] and analysis["pv"][0] == move:
                player_move_rank = idx
                move_score_white = analysis["score"].white().score(mate_score=MATE_SCORE) / 100
                player_move_score = move_score_white if side == "White" else -move_score_white
                break

        if len(alt_info) > 1:
            top = alt_info[0]["score"].white().score(mate_score=MATE_SCORE) / 100
            second = alt_info[1]["score"].white().score(mate_score=MATE_SCORE) / 100
            top_moves_eval_drop = abs(top - second)
            position_complexity = max(0.0, min(1.0, 1.0 - (top_moves_eval_drop / 2)))

    score_diff_from_best = 0.0
    if best_score is not None:
        score_diff_from_best = player_move_score - best_score

    # Detect capture and sacrifice for classification
    is_capture = board_before.is_capture(move)
    is_sacrifice = move_classifier.is_move_sacrifice(board_before, move)

    classification, move_quality = move_classifier.classify_move(
        player_move_rank=player_move_rank if player_move_rank >= 0 else 3,
        score_diff_from_best=score_diff_from_best,
        position_complexity=position_complexity,
        prev_score=prev_score,
        score_after=score_after,
        is_capture=is_capture,
        is_sacrifice=is_sacrifice,
        top_moves_eval_drop=top_moves_eval_drop,
        best_score=best_score,
        is_opening_move=is_opening_move,
    )

    # Compute best alternative move SAN and UCI
    best_move_san = ""
    best_move_uci = ""
    if alt_info and "pv" in alt_info[0] and alt_info[0]["pv"]:
        best_move_obj = alt_info[0]["pv"][0]
        if best_move_obj != move:
            best_move_uci = best_move_obj.uci()
            try:
                best_move_san = board_before.san(best_move_obj)
            except Exception:
                best_move_san = best_move_uci

    score_change = round(float(score_after - prev_score), 2)

    # Determine if this is a critical position (matches original desktop logic)
    is_critical = abs(score_change) >= 0.5 or position_complexity > 0.7

    return {
        "move_num": move_num,
        "side": side,
        "san": san,
        "uci": move.uci(),
        "classification": classification,
        "move_quality": round(float(move_quality), 3),
        "score_before": round(float(prev_score), 2),
        "score_after": round(float(score_after), 2),
        "score_change": score_change,
        "best_move": best_move_san,
        "best_move_uci": best_move_uci,
        "opening": opening_info,
        "player_move_rank": player_move_rank,
        "position_complexity": round(float(position_complexity), 3),
        "top_moves_eval_drop": round(float(top_moves_eval_drop), 3),
        "is_capture": is_capture,
        "is_sacrifice": is_sacrifice,
        "is_critical": is_critical,
    }


def _normalize(info: Any) -> List[Dict[str, Any]]:
    """Stockfish multipv=1 returns a dict; normalize to a list of analyses."""
    if isinstance(info, dict):
        return [info]
    return info


def compute_move_insight(
    game: ChessGame,
    move: chess.Move,
    board_before: chess.Board,
    side: str,
    score_cache: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Analyze a single move (live path). Uses the shared single engine instance,
    memoizing each unique FEN so a position is analysed once per import (P-02)."""
    engine_instance = EngineManager.get_instance()
    opening_info = game.get_current_opening()

    if engine_instance is None:
        return degraded_insight(move, board_before, side, opening_info)

    # Analyze the position BEFORE the move (multipv for the alternatives), memoized
    # by FEN so it can be reused as the previous move's "after" analysis.
    before_fen = board_before.fen()
    alt_info = score_cache.get(before_fen) if score_cache is not None else None
    if alt_info is None:
        alt_info = _normalize(engine_instance.analyze_position(
            board_before, depth=ANALYSIS_DEPTH, multipv=ANALYSIS_MULTIPV))
        if score_cache is not None:
            score_cache[before_fen] = alt_info

    # Analyze the position AFTER the move (also multipv) so it is reused as the NEXT
    # move's "before" context (one analysis per position instead of two).
    after_fen = game.board.fen()
    after_list = score_cache.get(after_fen) if score_cache is not None else None
    if after_list is None:
        after_list = _normalize(engine_instance.analyze_position(
            game.board, depth=ANALYSIS_DEPTH, multipv=ANALYSIS_MULTIPV))
        if score_cache is not None:
            score_cache[after_fen] = after_list

    detector = game.opening_detector
    current_index = len(game.board.move_stack) - 1
    is_opening_move = (
        opening_info is not None
        and getattr(detector, "last_theoretical_move_index", -1) >= current_index
    )

    return build_insight(move, board_before, side, alt_info, after_list, opening_info, is_opening_move)


def iter_analyze_fens(
    pool,
    fens: Iterable[str],
    depth: int = ANALYSIS_DEPTH,
    multipv: int = ANALYSIS_MULTIPV,
):
    """Analyse unique FENs concurrently on the engine pool, yielding
    (fen, analysis_or_None, done, total) as each completes (completion order).

    max_workers is capped at the pool size so no worker ever blocks on lease.
    Because each analysis is TT-independent (see EngineInstance.analyze_position),
    a FEN's result is identical to the sequential path — the invariant is preserved
    regardless of which instance analyses it or in what order.
    """
    unique_fens = list(dict.fromkeys(fens))  # de-dup, keep first-seen order
    total = len(unique_fens)
    if total == 0:
        return

    max_workers = max(1, min(getattr(pool, "size", 1), total))

    def work(fen: str):
        try:
            return _normalize(pool.analyze_position(chess.Board(fen), depth=depth, multipv=multipv))
        except Exception:
            return None

    done = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(work, fen): fen for fen in unique_fens}
        for fut in as_completed(futures):
            done += 1
            yield futures[fut], fut.result(), done, total


def analyze_fens_parallel(
    pool,
    fens: Iterable[str],
    depth: int = ANALYSIS_DEPTH,
    multipv: int = ANALYSIS_MULTIPV,
    progress: Optional[Callable[[int, int], None]] = None,
) -> Dict[str, Any]:
    """Drain iter_analyze_fens into {fen: analysis_list_or_None}."""
    results: Dict[str, Any] = {}
    for fen, info, done, total in iter_analyze_fens(pool, fens, depth, multipv):
        results[fen] = info
        if progress is not None:
            progress(done, total)
    return results


# ── PGN import orchestration: phase 1 (sequential replay) → phase 2 (parallel
#    analysis) → phase 3 (in-order insight reconstruction) ──

def parse_games(text: str) -> List[Any]:
    """Parse ALL games from a (possibly multi-game) PGN string. A single exported
    PGN file usually concatenates many games — read_game only returns the first, so
    we loop until the stream is exhausted."""
    games: List[Any] = []
    if not text or not text.strip():
        return games
    stream = io.StringIO(text)
    while True:
        try:
            g = chess.pgn.read_game(stream)
        except Exception:
            break
        if g is None:
            break
        if list(g.mainline_moves()):  # skip empty/header-only entries
            games.append(g)
    return games


def new_imported_game(parsed) -> ChessGame:
    """Build a ChessGame positioned at the PGN's starting position, opening reset."""
    game = ChessGame()
    game.reset()
    game.board = parsed.board().copy(stack=False)
    game.last_move = None
    game.opening_detector.reset()
    game.current_opening = None
    return game


def replay_and_snapshot(parsed):
    """Phase 1 (sequential): replay the game and freeze each ply's context into an
    immutable snapshot. The order-dependent opening state is read HERE, never from a
    worker thread. Returns (imported_game, snapshots). Raises ValueError(uci) on an
    illegal move.
    """
    game = new_imported_game(parsed)
    snapshots: List[Dict[str, Any]] = []
    for idx, move in enumerate(parsed.mainline_moves()):
        if move not in game.board.legal_moves:
            raise ValueError(move.uci())
        board_before = game.board.copy()
        side = "White" if game.board.turn == chess.WHITE else "Black"
        game.make_move(move)
        opening_info = game.get_current_opening()
        detector = game.opening_detector
        current_index = len(game.board.move_stack) - 1
        is_opening_move = (
            opening_info is not None
            and getattr(detector, "last_theoretical_move_index", -1) >= current_index
        )
        snapshots.append({
            "idx": idx,
            "move": move,
            "side": side,
            "board_before": board_before,
            "before_fen": board_before.fen(),
            "after_fen": game.board.fen(),
            "opening_info": opening_info,
            "is_opening_move": is_opening_move,
        })
    return game, snapshots


def snapshot_fens(snapshots) -> List[str]:
    """All FENs needed by a snapshot list (before + after of each ply)."""
    fens: List[str] = []
    for s in snapshots:
        fens.append(s["before_fen"])
        fens.append(s["after_fen"])
    return fens


def build_one_insight(s, analyses: Dict[str, Any]) -> Dict[str, Any]:
    """Build the insight for ONE snapshot from precomputed analyses, falling back to
    a degraded insight if its position(s) failed or no engine was available."""
    alt = analyses.get(s["before_fen"])
    aft = analyses.get(s["after_fen"])
    if alt is None or aft is None:
        return degraded_insight(s["move"], s["board_before"], s["side"], s["opening_info"])
    try:
        return build_insight(
            s["move"], s["board_before"], s["side"], alt, aft, s["opening_info"], s["is_opening_move"])
    except Exception:
        return degraded_insight(s["move"], s["board_before"], s["side"], s["opening_info"])


def build_evaluations(snapshots, analyses: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Phase 3: reconstruct insights in move order from the precomputed analyses.
    A position with a missing/failed analysis (or no engine) falls back to a
    degraded insight so the move count is preserved."""
    return [build_one_insight(s, analyses) for s in snapshots]


def analyze_pgn(parsed, progress: Optional[Callable[[int, int], None]] = None):
    """Full parallel import of a parsed PGN. Returns (imported_game, evaluations)."""
    game, snapshots = replay_and_snapshot(parsed)
    pool = EngineManager.get_pool()
    analyses = analyze_fens_parallel(pool, snapshot_fens(snapshots), progress=progress) if pool is not None else {}
    evaluations = build_evaluations(snapshots, analyses)
    return game, evaluations
