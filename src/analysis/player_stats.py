"""
Chess player statistics calculation functionality.
Handles statistics, accuracy metrics, and performance evaluation for player moves.
"""

import math

class PlayerStats:
    """Calculates statistics and metrics for player performance."""
    
    def __init__(self):
        """Initialize the player statistics calculator."""
        pass
    
    def calculate_player_stats(self, evaluations):
        """
        Calculate player statistics focusing on move quality and accuracy.

        Args:
            evaluations: List of move evaluation dictionaries

        Returns:
            Dictionary with player statistics
        """
        if not evaluations:
             # Return default zero/empty stats
            return {
                "precision": 0.0,
                "accuracy": 0.0,
                "avg_expected_points_loss": 0.0,
                "best_move_percentage": 0.0,
                "critical_accuracy": 0.0,
                "counts": {
                    "Meilleur coup": 0, "Excellent": 0, "Bon coup": 0,
                    "Imprécision": 0, "Erreur": 0, "Grosse erreur": 0,
                    "Super coup": 0, "Coup brillant": 0
                },
                "total_moves": 0
            }

        # --- Calculate Counts ---
        counts = {
            "Meilleur coup": 0, "Excellent": 0, "Bon coup": 0,
            "Imprécision": 0, "Erreur": 0, "Grosse erreur": 0,
            "Super coup": 0, "Coup brillant": 0
        }
        for eval in evaluations:
            classification = eval["classification"]
            if classification in counts:
                counts[classification] += 1
            else:
                counts["Erreur"] += 1 # Fallback

        # --- Calculate Accuracy based on Average Expected Points Loss ---
        move_qualities = [eval.get("move_quality", 0) for eval in evaluations]
        expected_points_losses = [1.0 - q for q in move_qualities]

        if expected_points_losses:
            avg_loss = sum(expected_points_losses) / len(expected_points_losses)
            # Exponential decay conversion: 100 * e^(-k * avg_loss)
            # The constant 'k' determines sensitivity. k=3 is a reasonable starting point.
            # Higher k = more sensitivity to errors.
            k = 6.0
            accuracy = 100.0 * math.exp(-k * avg_loss)
        else:
            avg_loss = 0.0
            accuracy = 100.0

        # --- Calculate Precision (Simple Average Quality) ---
        avg_quality = sum(move_qualities) / len(move_qualities) if move_qualities else 0
        precision = avg_quality * 100

        # --- Calculate Best Move Percentage ---
        best_moves = sum(1 for eval in evaluations if eval.get("player_move_rank", -1) == 0)
        total_moves = len(evaluations)
        best_move_percentage = best_moves / total_moves * 100 if total_moves > 0 else 0

        # --- Calculate Critical Accuracy ---
        critical_evals = [eval for eval in evaluations if eval.get("is_critical", False)]
        critical_qualities = [eval.get("move_quality", 0) for eval in critical_evals]
        critical_losses = [1.0 - q for q in critical_qualities]

        if critical_losses:
             avg_critical_loss = sum(critical_losses) / len(critical_losses)
             critical_accuracy = 100.0 * math.exp(-k * avg_critical_loss) # Use same k
        else:
             critical_accuracy = 100.0

        return {
            # Precision is the old linear average quality
            "precision": round(precision, 1),
            # Accuracy is the new exponential conversion of average loss
            "accuracy": round(accuracy, 1),
            "avg_expected_points_loss": round(avg_loss, 3),
            "best_move_percentage": round(best_move_percentage, 1),
            # Critical accuracy uses the same exponential conversion on critical moves
            "critical_accuracy": round(critical_accuracy, 1),
            "counts": counts,
            "total_moves": total_moves
        }
    
    def calculate_phase_stats(self, move_evaluations):
        """
        Calculate statistics for different game phases.
        
        Args:
            move_evaluations: List of move evaluation dictionaries
            
        Returns:
            Dictionary with statistics for opening, middlegame, and endgame phases
        """
        if not move_evaluations:
            return {
                "opening": self.calculate_player_stats([]),
                "middlegame": self.calculate_player_stats([]),
                "endgame": self.calculate_player_stats([])
            }
            
        # Split the game into phases
        opening_evals = move_evaluations[:min(10, len(move_evaluations))]
        middlegame_evals = move_evaluations[min(10, len(move_evaluations)):max(20, len(move_evaluations)-10)]
        endgame_evals = move_evaluations[max(20, len(move_evaluations)-10):]
        
        # Calculate statistics for each phase
        opening_stats = self.calculate_player_stats(opening_evals)
        middlegame_stats = self.calculate_player_stats(middlegame_evals)
        endgame_stats = self.calculate_player_stats(endgame_evals)
        
        return {
            "opening": opening_stats,
            "middlegame": middlegame_stats,
            "endgame": endgame_stats
        }