"""Caractérisation de MoveClassifier (fonctions pures, sans Stockfish)."""
import math

from src.analysis.move_classifier import MoveClassifier

mc = MoveClassifier()


def test_win_probability_equal_position():
    assert mc.score_to_win_probability(0.0) == 0.5


def test_win_probability_symmetry_and_bounds():
    # P(score) + P(-score) == 1, et une avance donne > 50 %.
    for s in (0.5, 1.0, 2.5, 5.0):
        p = mc.score_to_win_probability(s)
        q = mc.score_to_win_probability(-s)
        assert 0.0 < q < 0.5 < p < 1.0
        assert math.isclose(p + q, 1.0, abs_tol=1e-9)


def test_win_probability_monotonic():
    vals = [mc.score_to_win_probability(s) for s in (-3, -1, 0, 1, 3)]
    assert vals == sorted(vals)


def test_opening_move_is_theory():
    cls, _q = mc.classify_move(
        player_move_rank=0, score_diff_from_best=0.0,
        position_complexity=0.0, is_opening_move=True,
    )
    assert cls == "Théorie"


def test_best_move():
    cls, q = mc.classify_move(
        player_move_rank=0, score_diff_from_best=0.0, position_complexity=0.0,
    )
    assert cls == "Meilleur coup"
    assert q == 1.0


def test_blunder():
    # Rang non optimal + chute d'évaluation forte -> "Grosse erreur", qualité basse.
    cls, q = mc.classify_move(
        player_move_rank=3, score_diff_from_best=-10.0, position_complexity=0.0,
        prev_score=5.0, score_after=-5.0, best_score=5.0,
    )
    assert cls == "Grosse erreur"
    assert q < 0.2
