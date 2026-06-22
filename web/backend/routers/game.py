from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io
import json
import logging
import chess
import chess.pgn
from datetime import datetime
from typing import Dict, Any, List

from ..schemas import (
    GameResponse, MoveRequest, MoveResponse, ImportPgnRequest, 
    ImportPgnResponse, AnalysisResponse
)
from ..managers.game_manager import game_manager
from ..managers.profile_manager import profile_manager
from ..managers.engine_manager import EngineManager
from ..services.analysis import (
    compute_move_insight,
    analyze_pgn,
    replay_and_snapshot,
    snapshot_fens,
    build_one_insight,
    iter_analyze_fens,
)
from ..services.difficulty import calculate_difficulty

from src.core.chess_game import ChessGame
from src.analysis.player_stats import PlayerStats

logger = logging.getLogger(__name__)

router = APIRouter()
player_stats = PlayerStats()

@router.post("/game/new", response_model=GameResponse)
def create_new_game():
    session_id = game_manager.create_game()
    game = game_manager.get_game(session_id)
    game_manager.reset_move_evaluations(session_id)
    return {
        "session_id": session_id,
        "fen": game.board.fen(),
        "turn": "white" if game.board.turn == chess.WHITE else "black",
        "is_game_over": game.board.is_game_over(),
    }

@router.post("/game/move", response_model=MoveResponse)
def make_move(request: MoveRequest):
    game = game_manager.get_game(request.session_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found")

    try:
        move = chess.Move.from_uci(request.uci)
        if move in game.board.legal_moves:
            board_before = game.board.copy()
            side = "White" if game.board.turn == chess.WHITE else "Black"
            game.make_move(move)

            try:
                insight = compute_move_insight(game, move, board_before, side)
                game_manager.append_move_evaluation(request.session_id, insight)
            except Exception as insight_error:
                logger.warning("Insight computation failed: %s", insight_error)

            return {
                "success": True,
                "fen": game.board.fen(),
                "is_check": game.is_check(),
                "is_checkmate": game.is_checkmate(),
                "played_uci": request.uci,
            }

        return {
            "success": False,
            "fen": game.board.fen(),
            "is_check": game.is_check(),
            "is_checkmate": game.is_checkmate(),
            "message": "Illegal move",
            "played_uci": None,
        }
    except ValueError:
        return {
            "success": False,
            "fen": game.board.fen(),
            "is_check": game.is_check(),
            "is_checkmate": game.is_checkmate(),
            "message": "Invalid UCI format",
            "played_uci": None,
        }

@router.post("/game/bestmove", response_model=MoveResponse)
def play_best_move(request: MoveRequest):
    session_id = request.session_id
    game = game_manager.get_game(session_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found")

    engine_instance = EngineManager.get_instance()
    if not engine_instance:
        raise HTTPException(status_code=503, detail="Chess engine not available")

    try:
        best_move = engine_instance.get_best_move(game.board, depth=15)

        if best_move and best_move in game.board.legal_moves:
            board_before = game.board.copy()
            side = "White" if game.board.turn == chess.WHITE else "Black"
            game.make_move(best_move)

            try:
                insight = compute_move_insight(game, best_move, board_before, side)
                game_manager.append_move_evaluation(request.session_id, insight)
            except Exception as insight_error:
                logger.warning("Insight computation failed: %s", insight_error)

            return {
                "success": True,
                "fen": game.board.fen(),
                "is_check": game.is_check(),
                "is_checkmate": game.is_checkmate(),
                "message": f"Engine played {best_move.uci()}",
                "played_uci": best_move.uci(),
            }

        return {
            "success": False,
            "fen": game.board.fen(),
            "is_check": game.is_check(),
            "is_checkmate": game.is_checkmate(),
            "message": "Engine could not find a legal move",
            "played_uci": None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/game/analyze", response_model=AnalysisResponse)
def analyze_game(request: MoveRequest):
    game = game_manager.get_game(request.session_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found")

    engine_instance = EngineManager.get_instance()
    if not engine_instance:
        raise HTTPException(status_code=503, detail="Chess engine not available")

    try:
        info = engine_instance.analyze_position(game.board, depth=15)
        score_str = "0.00"

        pov_score = info.get("score")
        if pov_score is not None:
            white_score = pov_score.white()
            mate = white_score.mate()
            if mate is not None:
                score_str = f"#{mate}"
            else:
                cp = white_score.score(mate_score=10000)
                if cp is not None:
                    score_str = f"{cp / 100:.2f}"

        pv = info.get("pv")
        best_move = pv[0].uci() if pv else ""

        return {
            "score": score_str,
            "best_move": best_move,
            "depth": info.get("depth", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/game/import", response_model=ImportPgnResponse)
def import_pgn_game(request: ImportPgnRequest):
    session = game_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")

    pgn_text = (request.pgn or "").strip()
    if not pgn_text:
        raise HTTPException(status_code=400, detail="PGN content is empty")

    try:
        parsed = chess.pgn.read_game(io.StringIO(pgn_text))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid PGN: {e}")

    if parsed is None:
        raise HTTPException(status_code=400, detail="Unable to parse PGN")

    # Parallel analysis: phase 1 sequential replay (freezes opening context) →
    # phase 2 concurrent analysis on the engine pool → phase 3 in-order rebuild.
    try:
        imported_game, imported_evaluations = analyze_pgn(parsed)
    except ValueError as illegal:
        raise HTTPException(status_code=400, detail=f"Illegal move in PGN: {illegal}")

    session["game"] = imported_game
    session["move_evaluations"] = imported_evaluations

    # Extract PGN headers
    pgn_headers = {k: v for k, v in parsed.headers.items() if v and v != "?"}
    session["headers"] = pgn_headers

    white_evals = [ev for ev in imported_evaluations if ev.get("side") == "White"]
    black_evals = [ev for ev in imported_evaluations if ev.get("side") == "Black"]
    white_stats = player_stats.calculate_player_stats(white_evals)
    black_stats = player_stats.calculate_player_stats(black_evals)
    difficulty = calculate_difficulty(white_evals, black_evals)

    if request.profile_username:
        try:
            profile_manager.add_imported_game(
                username=request.profile_username,
                headers=pgn_headers,
                move_evaluations=imported_evaluations,
                white_stats=white_stats,
                black_stats=black_stats,
                difficulty=difficulty,
            )
        except Exception as e:
            logger.warning("Failed to attach imported game to profile '%s': %s", request.profile_username, e)
            
    # Format headers for response
    response_headers = pgn_headers.copy()
    if "TimeControl" in response_headers:
        response_headers["TimeControl"] = profile_manager.format_time_control(response_headers["TimeControl"])

    return {
        "success": True,
        "fen": imported_game.board.fen(),
        "turn": "white" if imported_game.board.turn == chess.WHITE else "black",
        "is_game_over": imported_game.board.is_game_over(),
        "imported_moves": len(imported_evaluations),
        "headers": response_headers,
        "message": "PGN imported successfully",
    }


# ── SSE streaming import ──

@router.post("/game/import/stream")
def import_pgn_stream(request: ImportPgnRequest):
    """Stream analysis progress via Server-Sent Events while importing a PGN."""

    session = game_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")

    pgn_text = (request.pgn or "").strip()
    if not pgn_text:
        raise HTTPException(status_code=400, detail="PGN content is empty")

    try:
        parsed = chess.pgn.read_game(io.StringIO(pgn_text))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid PGN: {e}")

    if parsed is None:
        raise HTTPException(status_code=400, detail="Unable to parse PGN")

    pgn_headers = {k: v for k, v in parsed.headers.items() if v and v != "?"}

    def event_stream():
        # Phase 1 (sequential): replay + freeze each ply's opening context.
        try:
            imported_game, snapshots = replay_and_snapshot(parsed)
        except ValueError as illegal:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Illegal move: {illegal}'})}\n\n"
            return

        # Phase 2 (parallel): analyse the unique positions on the engine pool and,
        # as each completes, emit every move that just became "ready" (both its
        # before/after positions analysed) — in move order, with classification, so
        # the progress bar stays smooth AND informative. We never yield from a worker
        # thread: the as_completed loop runs in this (the generator's) thread.
        pool = EngineManager.get_pool()
        total_moves = len(snapshots)
        analyses: Dict[str, Any] = {}
        evaluations: List[Any] = [None] * total_moves
        next_move = 0

        if pool is not None:
            completed = iter_analyze_fens(pool, snapshot_fens(snapshots))
        else:
            # No engine: every unique position "resolves" instantly to None (degraded).
            uniq = list(dict.fromkeys(snapshot_fens(snapshots)))
            completed = ((fen, None, i + 1, len(uniq)) for i, fen in enumerate(uniq))

        for fen, info, _done, _total in completed:
            analyses[fen] = info
            while next_move < total_moves:
                s = snapshots[next_move]
                if s["before_fen"] in analyses and s["after_fen"] in analyses:
                    insight = build_one_insight(s, analyses)
                    evaluations[next_move] = insight
                    yield f"data: {json.dumps({'type': 'progress', 'current': next_move + 1, 'total': total_moves, 'side': s['side'], 'san': insight.get('san', ''), 'classification': insight.get('classification', '')})}\n\n"
                    next_move += 1
                else:
                    break

        # Safety net: build any move not yet flushed (shouldn't happen once every FEN
        # has been processed, since all positions are then available).
        while next_move < total_moves:
            evaluations[next_move] = build_one_insight(snapshots[next_move], analyses)
            next_move += 1
        imported_evaluations = evaluations

        # Finalize session
        session["game"] = imported_game
        session["move_evaluations"] = imported_evaluations
        session["headers"] = pgn_headers

        white_evals = [ev for ev in imported_evaluations if ev.get("side") == "White"]
        black_evals = [ev for ev in imported_evaluations if ev.get("side") == "Black"]
        white_stats = player_stats.calculate_player_stats(white_evals)
        black_stats = player_stats.calculate_player_stats(black_evals)
        difficulty = calculate_difficulty(white_evals, black_evals)

        if request.profile_username:
            try:
                profile_manager.add_imported_game(
                    username=request.profile_username,
                    headers=pgn_headers,
                    move_evaluations=imported_evaluations,
                    white_stats=white_stats,
                    black_stats=black_stats,
                    difficulty=difficulty,
                )
            except Exception as e:
                logger.warning("Failed to attach imported game to profile: %s", e)

        response_headers = pgn_headers.copy()
        if "TimeControl" in response_headers:
            response_headers["TimeControl"] = profile_manager.format_time_control(response_headers["TimeControl"])

        done_data = {
            "type": "done",
            "success": True,
            "fen": imported_game.board.fen(),
            "turn": "white" if imported_game.board.turn == chess.WHITE else "black",
            "is_game_over": imported_game.board.is_game_over(),
            "imported_moves": len(imported_evaluations),
            "headers": response_headers,
        }
        yield f"data: {json.dumps(done_data)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

@router.get("/game/{session_id}/insights")
def get_game_insights(session_id: str):
    game = game_manager.get_game(session_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found")

    move_evaluations = game_manager.get_move_evaluations(session_id)
    white_evals = [ev for ev in move_evaluations if ev.get("side") == "White"]
    black_evals = [ev for ev in move_evaluations if ev.get("side") == "Black"]

    session = game_manager.get_session(session_id)
    headers = session.get("headers", {}) if session else {}
    
    # Format TimeControl for display
    if "TimeControl" in headers:
        # Create a copy to avoid modifying the session storage if we want to keep it raw there
        headers = headers.copy()
        headers["TimeControl"] = profile_manager.format_time_control(headers["TimeControl"])

    white_stats = player_stats.calculate_player_stats(white_evals)
    black_stats = player_stats.calculate_player_stats(black_evals)

    eval_chart = []
    for i, ev in enumerate(move_evaluations):
        score = ev.get("score_after", 0.0)
        if ev.get("side") == "Black":
            score = -score
        eval_chart.append({"ply": i + 1, "score": round(float(score), 2)})

    difficulty = calculate_difficulty(white_evals, black_evals)

    return {
        "initial_fen": game.board.root().fen(),
        "opening": game.get_current_opening(),
        "last_opening": game.opening_detector.get_last_theoretical_move_opening(),
        "moves": move_evaluations,
        "white_stats": white_stats,
        "black_stats": black_stats,
        "headers": headers,
        "eval_chart": eval_chart,
        "difficulty": difficulty,
    }
