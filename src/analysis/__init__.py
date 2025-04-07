"""
Analysis package for the chess application.

This package contains modules for analyzing chess games, moves, and player performance.
"""

# Main components
from src.analysis.game_analyzer import GameAnalyzer
from src.analysis.game_difficulty import add_difficulty_analysis_to_game_analyzer
from src.analysis.move_analyzer import MoveAnalyzer
from src.analysis.move_classifier import MoveClassifier
from src.analysis.tactical_analyzer import TacticalAnalyzer
from src.analysis.player_stats import PlayerStats

__all__ = [
    'GameAnalyzer',
    'add_difficulty_analysis_to_game_analyzer',
    'MoveAnalyzer',
    'MoveClassifier',
    'TacticalAnalyzer',
    'PlayerStats'
]