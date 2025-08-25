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
                    "Super coup": 0, "Coup brillant": 0, "Théorie": 0
                },
                "total_moves": 0
            }

        # --- Calculate Counts ---
        counts = {
            "Meilleur coup": 0, "Excellent": 0, "Bon coup": 0,
            "Imprécision": 0, "Erreur": 0, "Grosse erreur": 0,
            "Super coup": 0, "Coup brillant": 0, "Théorie": 0
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
            # The constant 'k' determines sensitivity.
            # Higher k = more sensitivity to errors.
            k = 9.0
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
        # Empty -> zero stats
        if not move_evaluations:
            return {
                "opening": self.calculate_player_stats([]),
                "middlegame": self.calculate_player_stats([]),
                "endgame": self.calculate_player_stats([])
            }

        # --- Dynamic phase boundary detection ---
        # We rely on full move numbers ("move_num" field) present in each evaluation (full move index, starting at 1)
        # and the presence of an opening tag per move (eval.get("opening")).
        # 1) Opening ends at the last move still tagged as belonging to a known opening line (book)
        #    If none tagged, fallback to a conventional baseline (full move 12).
        # 2) Endgame starts near the last quarter of the game OR at least 5 full moves after opening end, whichever is later.
        #    Heuristic: endgame_start = max(opening_end + 5, total_full_moves - max(10, total_full_moves // 4)).
        #    This gives ~ last 10 moves for long games, proportionally fewer for shorter ones.
        # 3) Everything between is middlegame.

        # Collect move numbers of this side's moves
        move_nums = [ev.get("move_num") for ev in move_evaluations if isinstance(ev.get("move_num"), int)]
        if not move_nums:
            return {
                "opening": self.calculate_player_stats([]),
                "middlegame": self.calculate_player_stats(move_evaluations),  # treat all as middlegame if no numbering
                "endgame": self.calculate_player_stats([])
            }

        total_full_moves = max(move_nums)

        # Determine last opening move number for this side (presence of opening tag)
        opening_tagged_moves = [ev.get("move_num") for ev in move_evaluations if ev.get("opening")]
        if opening_tagged_moves:
            opening_end_fullmove = max(opening_tagged_moves)
            # Cap to avoid absurdly long opening phase (e.g., if tagging persisted) -> max 25
            opening_end_fullmove = min(opening_end_fullmove, 25)
        else:
            # Fallback baseline
            opening_end_fullmove = min(12, max(6, total_full_moves // 3))  # adaptive baseline

        # Determine endgame start
        heuristic_tail = max(10, total_full_moves // 4)  # at least last 10 moves or 25% of game
        endgame_start_fullmove = total_full_moves - heuristic_tail + 1
        # Ensure at least 5 moves between phases
        endgame_start_fullmove = max(endgame_start_fullmove, opening_end_fullmove + 5)
        # Avoid overlap; if game too short, collapse to two phases or one phase
        if endgame_start_fullmove >= total_full_moves - 1:
            # Not enough room for distinct endgame; push start earlier but keep ordering
            endgame_start_fullmove = max(opening_end_fullmove + 3, total_full_moves - 5)
        if endgame_start_fullmove <= opening_end_fullmove:
            # Degenerate case -> treat entire game as middlegame to avoid misleading tiny buckets
            opening_evals = []
            middlegame_evals = move_evaluations
            endgame_evals = []
        else:
            opening_evals = [ev for ev in move_evaluations if ev.get("move_num", 0) <= opening_end_fullmove]
            endgame_evals = [ev for ev in move_evaluations if ev.get("move_num", 0) >= endgame_start_fullmove]
            middlegame_evals = [ev for ev in move_evaluations if opening_end_fullmove < ev.get("move_num", 0) < endgame_start_fullmove]

        # Safety: prevent empty middlegame for long games with big gap due to tagging anomalies
        if not middlegame_evals and len(move_evaluations) > 12:
            # Redistribute: if opening covers too much, trim a portion to middlegame
            if len(opening_evals) > len(move_evaluations) * 0.6:
                # Move last 20% of opening_evals into middlegame
                shift = max(2, int(len(opening_evals) * 0.2))
                middlegame_evals = opening_evals[-shift:] + middlegame_evals
                opening_evals = opening_evals[:-shift]
            # Or if endgame too big
            elif len(endgame_evals) > len(move_evaluations) * 0.5:
                shift = max(2, int(len(endgame_evals) * 0.2))
                middlegame_evals = middlegame_evals + endgame_evals[:shift]
                endgame_evals = endgame_evals[shift:]

        # Compute stats
        opening_stats = self.calculate_player_stats(opening_evals)
        middlegame_stats = self.calculate_player_stats(middlegame_evals)
        endgame_stats = self.calculate_player_stats(endgame_evals)

        return {
            "opening": opening_stats,
            "middlegame": middlegame_stats,
            "endgame": endgame_stats,
            # Optionally could expose boundaries if later displayed (kept internal for now)
        }