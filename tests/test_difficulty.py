"""Caractérisation du calcul de difficulté (web/backend/services/difficulty.py)."""
from web.backend.services.difficulty import calculate_difficulty


def _eval(**over):
    base = {
        "position_complexity": 0.5, "score_before": 0.0,
        "top_moves_eval_drop": 0.4, "player_move_rank": 0,
        "move_quality": 0.9, "classification": "Excellent",
        "score_change": 0.0, "move_num": 1, "side": "White",
    }
    base.update(over)
    return base


def test_empty_is_neutral():
    assert calculate_difficulty([], []) == {"overall": 5.0, "white": 5.0, "black": 5.0}


def test_shape_and_bounds():
    white = [_eval(side="White") for _ in range(8)]
    black = [_eval(side="Black", score_before=-0.1, classification="Bon coup") for _ in range(8)]
    r = calculate_difficulty(white, black)
    assert set(r) == {"overall", "white", "black"}
    for v in r.values():
        assert 1.0 <= v <= 10.0
    assert r["overall"] == round((r["white"] + r["black"]) / 2, 1)


def test_deterministic():
    evals = [_eval() for _ in range(6)]
    assert calculate_difficulty(evals, []) == calculate_difficulty(evals, [])
