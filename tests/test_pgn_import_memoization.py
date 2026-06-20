"""
Caractérisation de la mémoïsation FEN de l'import PGN (P-02).

Avec un moteur DÉTERMINISTE (score fonction du seul FEN), le cache doit :
- réduire le nombre d'analyses (1 par position au lieu de 2 par coup),
- produire EXACTEMENT la même sortie qu'sans cache.

(Le léger décalage de score observé en production vient du fait que le vrai
Stockfish renvoie des scores différents en multipv=1 vs multipv=3 ; c'est le
compromis assumé de P-02, hors périmètre de ce test déterministe.)
"""
import io

import chess
import chess.engine
import chess.pgn

from src.core.chess_game import ChessGame
from web.backend.services import analysis as A
from web.backend.managers import engine_manager as EM

PGN = "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6"  # 8 demi-coups


class _DeterministicEngine:
    """analyze_position renvoie un score qui ne dépend QUE de la position."""

    def __init__(self):
        self.calls = 0

    def analyze_position(self, board, depth=None, multipv=None):
        self.calls += 1
        legal = list(board.legal_moves)
        score = sum(ord(c) for c in board.board_fen()) % 200 - 100
        out = []
        for i in range(multipv or 1):
            mv = legal[i % len(legal)] if legal else None
            out.append({
                "score": chess.engine.PovScore(chess.engine.Cp(score), chess.WHITE),
                "pv": [mv] if mv else [],
            })
        return out


def _run(use_cache, monkeypatch):
    engine = _DeterministicEngine()
    monkeypatch.setattr(EM.EngineManager, "get_instance",
                        classmethod(lambda cls: engine))
    parsed = chess.pgn.read_game(io.StringIO(PGN))
    g = ChessGame()
    g.reset()
    g.board = parsed.board().copy(stack=False)
    g.opening_detector.reset()
    g.current_opening = None
    cache = {} if use_cache else None
    evals = []
    for move in parsed.mainline_moves():
        bb = g.board.copy()
        side = "White" if g.board.turn == chess.WHITE else "Black"
        g.make_move(move)
        evals.append(A.compute_move_insight(g, move, bb, side, cache))
    return evals, engine.calls


def test_cache_reduces_engine_calls(monkeypatch):
    _, n_nocache = _run(False, monkeypatch)
    _, n_cache = _run(True, monkeypatch)
    assert n_nocache == 16   # 2 analyses * 8 demi-coups
    assert n_cache == 9      # 1 analyse par position (8 + position initiale)


def test_cache_is_lossless_with_deterministic_engine(monkeypatch):
    e_nocache, _ = _run(False, monkeypatch)
    e_cache, _ = _run(True, monkeypatch)
    assert e_nocache == e_cache
