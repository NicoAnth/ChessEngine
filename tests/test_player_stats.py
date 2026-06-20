"""Caractérisation de PlayerStats.calculate_player_stats (pur, déterministe)."""
import pytest

from src.analysis.player_stats import PlayerStats

ps = PlayerStats()


def test_empty_returns_zeros():
    r = ps.calculate_player_stats([])
    assert r["total_moves"] == 0
    assert r["accuracy"] == 0.0
    assert r["acpl"] == 0.0
    assert r["counts"]["Meilleur coup"] == 0


def test_perfect_game():
    evals = [
        {"classification": "Meilleur coup", "move_quality": 1.0,
         "player_move_rank": 0, "score_before": 0.3, "score_after": 0.3}
        for _ in range(5)
    ]
    r = ps.calculate_player_stats(evals)
    assert r["accuracy"] == 100.0
    assert r["precision"] == 100.0
    assert r["best_move_percentage"] == 100.0
    assert r["acpl"] == 0.0
    assert r["consistency"] == 100.0
    assert r["counts"]["Meilleur coup"] == 5
    assert r["total_moves"] == 5


def test_mixed_known_values():
    # 1 coup parfait + 1 erreur ; valeurs calculées à la main.
    evals = [
        {"classification": "Meilleur coup", "move_quality": 1.0,
         "player_move_rank": 0, "score_before": 0.2, "score_after": 0.2},
        {"classification": "Erreur", "move_quality": 0.5,
         "player_move_rank": 3, "score_before": 0.5, "score_after": -0.5,
         "is_critical": True},
    ]
    r = ps.calculate_player_stats(evals)
    assert r["precision"] == 75.0                              # avg quality 0.75 * 100
    assert r["best_move_percentage"] == 50.0                   # 1/2 rank-0
    assert r["accuracy"] == pytest.approx(10.5, abs=0.1)       # 100*e^(-9*0.25)
    assert r["acpl"] == pytest.approx(50.0, abs=0.1)           # mean cp loss 0.5 * 100
    assert r["consistency"] == pytest.approx(50.0, abs=0.1)    # std 0.25 -> 50 %
    assert r["critical_accuracy"] == pytest.approx(1.1, abs=0.1)  # 100*e^(-9*0.5)
    assert r["avg_expected_points_loss"] == pytest.approx(0.25, abs=0.001)
    assert r["counts"]["Meilleur coup"] == 1
    assert r["counts"]["Erreur"] == 1
    # Aucune position avec score_before strictement > 0.5 ou < -0.5.
    assert r["t1_accuracy"] == 0.0
    assert r["t2_accuracy"] == 0.0
