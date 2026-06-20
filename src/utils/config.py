"""
Analysis configuration for the chess engine core (shared with the web backend).

The Tkinter desktop app was removed; this module is intentionally UI-free
(no tkinter import, no colors/fonts) so it can be imported by the web backend.
"""
import os

# Engine analysis settings
ENGINE_ANALYSIS = {
    "default_depth": 15,          # Standard depth for position analysis
    "detailed_depth": 20,         # Deeper analysis for detailed evaluations
    "tactical_depth": 16,         # Depth for tactical sequences
    "multipv": 3,                 # Number of alternative moves to consider
    "mate_score": 10000,          # Score value assigned to checkmate
    "analysis_threads": max(1, min(os.cpu_count() // 2, 4)),  # half the cores, capped at 4
    "engine_threads_per_instance": 1,  # threads used by each Stockfish instance
}

# Expected Points move classification thresholds (loss of expected points).
# Note: "Meilleur coup" is decided by rank == 0 and "Grosse erreur" is the
# fallback (else), so neither has a threshold key here.
MOVE_CLASSIFICATION = {
    "excellent_threshold": 0.02,
    "bon_coup_threshold": 0.05,
    "imprecision_threshold": 0.10,
    "erreur_threshold": 0.20,
    "position_improvement_threshold": 0.15,  # for "Super coup"
    "only_move_eval_drop": 0.4,              # for "only good move" detection
    "sacrifice_threshold": 1,                # material value counted as a sacrifice
    "winning_position_threshold": 0.85,      # win probability considered "winning"
}
