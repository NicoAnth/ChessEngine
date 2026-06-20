"""Caractérisation d'OpeningDetector après P-04 (cache partagé) / P-03 (index O(1))."""
import chess

from src.analysis import opening_detector as od
from src.analysis.opening_detector import OpeningDetector


def _board(*sans):
    b = chess.Board()
    for s in sans:
        b.push_san(s)
    return b


def test_known_openings():
    d = OpeningDetector()
    assert d.detect_opening(_board("e4"))["name"] == "King's Pawn Game"
    ruy = d.detect_opening(_board("e4", "e5", "Nf3", "Nc6", "Bb5"))
    assert ruy["eco"] == "C60" and ruy["name"] == "Ruy Lopez"
    assert d.detect_opening(_board("e4", "c5"))["name"] == "Sicilian Defense"


def test_eco_tables_are_loaded_and_shared():
    # P-04: a single read-only ECO table shared by all instances.
    d1 = OpeningDetector()
    d1.detect_opening(_board("e4"))
    d2 = OpeningDetector()
    assert d1.openings_by_fen is d2.openings_by_fen
    assert d1.openings_by_position is d2.openings_by_position
    assert len(od._ECO_BY_FEN) > 1000


def test_mutable_state_is_per_instance():
    d1 = OpeningDetector()
    d2 = OpeningDetector()
    d1.detect_opening(_board("e4", "c5"))  # Sicilian
    d2.detect_opening(_board("d4"))         # Queen's Pawn
    assert d1.current_opening != d2.current_opening


def test_detection_is_deterministic():
    b = _board("e4", "e5", "Nf3")
    assert OpeningDetector().detect_opening(b) == OpeningDetector().detect_opening(b)
