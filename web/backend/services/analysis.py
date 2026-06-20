from typing import Any, Dict, List, Optional
import chess

from src.core.chess_game import ChessGame
from src.analysis.move_classifier import MoveClassifier
from ..managers.engine_manager import EngineManager

# Singleton instances for helpers can be created here
move_classifier = MoveClassifier()

def compute_move_insight(
    game: ChessGame,
    move: chess.Move,
    board_before: chess.Board,
    side: str
) -> Dict[str, Any]:
    """
    Analyzes a single move to determine quality, score change, etc.
    """
    engine_instance = EngineManager.get_instance()
    
    move_num = (len(board_before.move_stack) // 2) + 1
    san = board_before.san(move)
    opening_info = game.get_current_opening()

    if engine_instance is None:
        return {
            "move_num": move_num,
            "side": side,
            "san": san,
            "uci": move.uci(),
            "classification": "Inconnu",
            "move_quality": 0.5,
            "score_before": 0.0,
            "score_after": 0.0,
            "opening": opening_info,
        }

    # Analyze position before move to get context
    alt_info = engine_instance.analyze_position(board_before, depth=16, multipv=3)
    if isinstance(alt_info, dict):
        alt_info = [alt_info]

    # Analyze position after move
    after_info = engine_instance.analyze_position(game.board, depth=16, multipv=1)
    if isinstance(after_info, list):
        after_info = after_info[0]

    # Calculate score change (mate_score=10000 matches original desktop config)
    prev_score_white = alt_info[0]["score"].white().score(mate_score=10000) / 100
    score_after_white = after_info["score"].white().score(mate_score=10000) / 100

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
        top_score_white = alt_info[0]["score"].white().score(mate_score=10000) / 100
        best_score = top_score_white if side == "White" else -top_score_white

        for idx, analysis in enumerate(alt_info):
            if "pv" in analysis and analysis["pv"] and analysis["pv"][0] == move:
                player_move_rank = idx
                move_score_white = analysis["score"].white().score(mate_score=10000) / 100
                player_move_score = move_score_white if side == "White" else -move_score_white
                break

        if len(alt_info) > 1:
            top = alt_info[0]["score"].white().score(mate_score=10000) / 100
            second = alt_info[1]["score"].white().score(mate_score=10000) / 100
            top_moves_eval_drop = abs(top - second)
            position_complexity = max(0.0, min(1.0, 1.0 - (top_moves_eval_drop / 2)))

    # Opening logic
    detector = game.opening_detector
    current_index = len(game.board.move_stack) - 1
    is_opening_move = (
        opening_info is not None
        and getattr(detector, "last_theoretical_move_index", -1) >= current_index
    )

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
