"""
Analysis package for the chess engine core (shared with the web backend).

Desktop-only modules (game_analyzer, game_difficulty, move_analyzer,
tactical_analyzer) were removed with the Tkinter app; the web backend
reimplements that orchestration in web/backend/services.
"""

from src.analysis.move_classifier import MoveClassifier
from src.analysis.player_stats import PlayerStats
from src.analysis.opening_detector import OpeningDetector

__all__ = [
    'MoveClassifier',
    'PlayerStats',
    'OpeningDetector',
]
