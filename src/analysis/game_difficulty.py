"""
Game difficulty calculator focusing on decision complexity with tactical depth consideration.
"""

import math
import chess
import numpy as np

class GameDifficultyCalculator:
    """Calculates the decision complexity of a chess game with tactical depth adjustments."""
    
    def __init__(self, engine_manager):
        """
        Initialize the difficulty calculator.
        
        Args:
            engine_manager: An instance of EngineManager
        """
        self.engine_manager = engine_manager
        # Material values for calculating tactical gains
        self.piece_values = {
            chess.PAWN: 1.0,
            chess.KNIGHT: 3.0,
            chess.BISHOP: 3.0,
            chess.ROOK: 5.0,
            chess.QUEEN: 9.0
        }
    
    def calculate_game_difficulty(self, analysis_results):
        """
        Calculate the difficulty of a chess game with separate metrics for each player,
        considering tactical opportunities that may reduce complexity.
        
        Args:
            analysis_results: Dictionary containing game analysis results
            
        Returns:
            Dictionary with overall difficulty and player-specific difficulties
        """
        move_evaluations = analysis_results["move_evaluations"]
        
        # Split moves by player
        white_evals = [eval for eval in move_evaluations if eval["side"] == "White"]
        black_evals = [eval for eval in move_evaluations if eval["side"] == "Black"]
        
        # Calculate raw decision difficulty for each player
        white_decision_difficulty = self._calculate_decision_difficulty(white_evals)
        black_decision_difficulty = self._calculate_decision_difficulty(black_evals)
        
        # Calculate precision bonuses for high-quality play
        white_precision_bonus = self._calculate_precision_bonus(white_evals)
        black_precision_bonus = self._calculate_precision_bonus(black_evals)
        
        # Apply tactical complexity nerf based on OPPONENT's blunders
        # White's difficulty is reduced by Black's blunders and vice versa
        white_tactical_nerf = self._calculate_tactical_nerf(black_evals, opponent_side="White")
        black_tactical_nerf = self._calculate_tactical_nerf(white_evals, opponent_side="Black")
        
        # Apply the nerf to the decision difficulty and add precision bonus
        white_difficulty_value = (white_decision_difficulty * white_tactical_nerf) + white_precision_bonus
        black_difficulty_value = (black_decision_difficulty * black_tactical_nerf) + black_precision_bonus
        
        # Cap at maximum difficulty of 10
        white_difficulty_value = min(10.0, white_difficulty_value)
        black_difficulty_value = min(10.0, black_difficulty_value)
        
        # Calculate overall game difficulty (weighted average)
        overall_difficulty = (white_difficulty_value + black_difficulty_value) / 2
        
        # Create structured difficulty data for white and black
        white_difficulty = {
            "overall_difficulty": round(white_difficulty_value, 1),
            "decision_difficulty": round(white_decision_difficulty, 1),
            "tactical_nerf": round(white_tactical_nerf, 2),
            "precision_bonus": round(white_precision_bonus, 2)
        }
        
        black_difficulty = {
            "overall_difficulty": round(black_difficulty_value, 1),
            "decision_difficulty": round(black_decision_difficulty, 1),
            "tactical_nerf": round(black_tactical_nerf, 2),
            "precision_bonus": round(black_precision_bonus, 2)
        }
        
        return {
            "overall_difficulty": round(overall_difficulty, 1),
            "white_difficulty": white_difficulty,
            "black_difficulty": black_difficulty,
            "factors": {
                "white_decision_difficulty": round(white_decision_difficulty, 1),
                "white_tactical_nerf": round(white_tactical_nerf, 2),
                "white_precision_bonus": round(white_precision_bonus, 2),
                "black_decision_difficulty": round(black_decision_difficulty, 1),
                "black_tactical_nerf": round(black_tactical_nerf, 2),
                "black_precision_bonus": round(black_precision_bonus, 2)
            }
        }
    
    def _calculate_decision_difficulty(self, player_evals):
        """
        Calculate decision difficulty based on the entropy of candidate move evaluations,
        with a higher baseline for positions with narrow evaluation differences.
        
        Args:
            player_evals: List of move evaluation dictionaries for a specific player
            
        Returns:
            Decision difficulty score (1-10) based on adjusted normalized entropy.
        """
        if not player_evals:
            return 5  # Default medium difficulty if no moves available

        # Count best move selections
        best_moves = sum(1 for eval in player_evals if eval.get("player_move_rank", -1) == 0)
        total_moves = len(player_evals)
        best_move_ratio = best_moves / total_moves if total_moves > 0 else 0
        
        # Best move selection bonus (selecting the best move in difficult positions is harder)
        best_move_bonus = best_move_ratio * 1.5
        
        move_entropies = []
        position_difficulties = []
        T = 0.3          # Temperature for softmax; lower T makes evaluation differences more pronounced.
        
        # Logistic scaling parameters:
        # When abs(best_eval) is below 'threshold', scaling_factor is close to 1.
        # As abs(best_eval) exceeds 'threshold', scaling_factor decays smoothly.
        beta = 0.1       # Controls the steepness of the logistic curve.
        threshold = 50   # Evaluation threshold (in centipawns) for a balanced position.

        for eval in player_evals:
            # Skip moves without sufficient candidate moves information
            if "top_moves" not in eval or len(eval["top_moves"]) < 2:
                continue

            candidates = eval["top_moves"]
            best_eval = candidates[0].get("score", 0)
            
            # Check if this is a "narrow margin" position where top moves are very close
            if len(candidates) >= 2:
                top_diff = abs(candidates[0].get("score", 0) - candidates[1].get("score", 0))
                # Smaller differences between top moves = harder position
                narrow_margin = max(0, 1.0 - (top_diff / 0.3))  # Scale to 0-1
                position_difficulties.append(5 + (narrow_margin * 4))  # Scale to 5-9
            
            # Calculate evaluation differences for candidate moves
            evals = [move.get("score", best_eval - 3.0) for move in candidates]
            
            # Compute softmax probabilities for each candidate move
            softmax_denom = sum(math.exp(-((best_eval - e) / T)) for e in evals)
            probs = [math.exp(-((best_eval - e) / T)) / softmax_denom for e in evals]
            
            # Calculate entropy of the probability distribution
            entropy = -sum(p * math.log(p) if p > 0 else 0 for p in probs)
            
            # Normalize entropy by the maximum possible entropy (logarithm of the number of candidates)
            max_entropy = math.log(len(candidates))
            norm_entropy = entropy / max_entropy if max_entropy > 0 else 0
            
            # Compute logistic scaling factor based on game dominance.
            # When abs(best_eval) is low, scaling_factor is near 1. When it is high, scaling_factor decreases.
            scaling_factor = 1 / (1 + math.exp(beta * (abs(best_eval) - threshold)))
            
            # Adjust the normalized entropy with the scaling factor.
            adjusted_entropy = scaling_factor * norm_entropy
            move_entropies.append(adjusted_entropy)
        
        # Calculate decision difficulty based on entropy
        if move_entropies:
            avg_entropy = sum(move_entropies) / len(move_entropies)
            entropy_difficulty = 1 + (avg_entropy * 9)
        else:
            entropy_difficulty = 5  # Default if no entropy data
        
        # Calculate position difficulty based on narrow margins
        if position_difficulties:
            avg_position_difficulty = sum(position_difficulties) / len(position_difficulties)
        else:
            avg_position_difficulty = 5  # Default if no position difficulty data
        
        # Combine entropy-based and position-based difficulty with best move bonus
        combined_difficulty = (entropy_difficulty * 0.5) + (avg_position_difficulty * 0.5) + best_move_bonus
        
        # Cap at maximum of 10
        return min(combined_difficulty, 10.0)
    
    def _calculate_precision_bonus(self, player_evals):
        """
        Calculate a bonus to add to game difficulty based on high-precision play.
        High-quality play should result in higher difficulty scores.
        
        Args:
            player_evals: List of move evaluation dictionaries for a specific player
            
        Returns:
            Precision bonus (0.0-3.0)
        """
        if not player_evals or len(player_evals) < 5:
            return 0.0
        
        # Calculate precision (average move quality)
        move_qualities = [eval.get("move_quality", 0) for eval in player_evals]
        avg_quality = sum(move_qualities) / len(move_qualities) if move_qualities else 0
        precision = avg_quality
        
        # Count move classifications
        excellent_count = sum(1 for eval in player_evals if eval.get("classification", "") == "Excellent")
        good_count = sum(1 for eval in player_evals if eval.get("classification", "") == "Bon coup")
        mistake_count = sum(1 for eval in player_evals if eval.get("classification", "") in ["Erreur", "Grosse erreur"])
        
        excellent_ratio = excellent_count / len(player_evals) if player_evals else 0
        good_ratio = good_count / len(player_evals) if player_evals else 0
        mistake_ratio = mistake_count / len(player_evals) if player_evals else 0
        
        # Calculate bonus based on excellent moves
        # High ratio of excellent moves = high bonus
        excellent_bonus = excellent_ratio * 2.5
        
        # Penalty for mistakes
        # Even a few mistakes should significantly reduce the bonus
        mistake_penalty = mistake_ratio * 4.0
        
        # Calculate length bonus - longer games with high precision are harder
        length_factor = min(1.0, len(player_evals) / 25)
        length_bonus = length_factor * 0.5
        
        # Calculate quality-based bonus with penalty for mistakes
        quality_bonus = max(0, (precision * 3.0) - mistake_penalty + length_bonus)
        
        # Combine bonuses - removed special engine bonus
        total_bonus = excellent_bonus + quality_bonus
        
        # Cap bonus at 3.0 (which would allow a 7.0 base difficulty to reach 10.0)
        return min(total_bonus, 3.0)
    
    def _calculate_tactical_nerf(self, player_evals, opponent_side=""):
        """
        Calculate a tactical complexity nerf factor based on the presence of easy tactics.
        Easy tactics (low depth with high material gain) should significantly reduce complexity.
        
        Args:
            player_evals: List of move evaluation dictionaries for a specific player
            opponent_side: Side of the opponent ("White" or "Black")
            
        Returns:
            Nerf factor between 0.1 and 1.0 (1.0 = no nerf, 0.1 = maximum nerf)
        """
        if not player_evals:
            return 1.0  # No nerf if no moves
        
        # Look for massive blunders that benefit the opponent
        massive_blunders = []
        for eval in player_evals:
            score_change = eval.get("score_change", 0)
            # Major blunder detected (negative score change of 3+ points)
            # This is a blunder by the current player that benefits their opponent
            if score_change <= -3.0:
                # Calculate how severe the blunder is - more negative = worse
                blunder_severity = min(abs(score_change) / 3.0, 3.0)  # Cap at 3.0
                # More severe blunders by player make game easier for opponent
                nerf_factor = max(0.1, 1.0 - (blunder_severity * 0.3))
                massive_blunders.append(nerf_factor)
        
        # If we found any massive blunders, apply strongest nerf immediately
        if massive_blunders:
            return min(massive_blunders)  # Use the strongest nerf (lowest value)
        
        # Continue with regular critical position analysis
        critical_positions = [eval for eval in player_evals if eval.get("is_critical", False)]
        if not critical_positions:
            return 1.0  # No nerf if no critical positions
        
        # Calculate tactical nerf factors for each critical position
        nerf_factors = []
        for position in critical_positions:
            # Only consider critical positions where the player makes a mistake
            # (negative score change means player's position got worse = opponent's got better)
            score_change = position.get("score_change", 0)
            if score_change >= 0:
                continue  # Skip positions where player improved their position
                
            tactical_depth = position.get("tactical_depth", 0)
            if tactical_depth <= 0:
                # Even with no tactical depth, check for big eval changes
                if score_change <= -1.5:  # Significant negative score change
                    nerf_value = max(0.3, 1.0 - (abs(score_change) / 10.0))
                    nerf_factors.append(nerf_value)
                continue
            
            # Calculate material gain from tactical sequence if available
            material_gain = self._estimate_material_gain(position)
            
            # Calculate nerf factor - higher gain with lower depth = bigger nerf
            depth_factor = max(1, tactical_depth * tactical_depth)
            scaling = 4.0  # Lower scaling constant for stronger nerfs
            
            # Apply revised formula with stronger nerf potential
            raw_nerf = material_gain / (depth_factor * scaling)
            nerf_factor = 1.0 - min(0.9, raw_nerf)  # Allow up to 90% reduction
            
            # Extra penalty for obvious tactics
            if tactical_depth == 1:
                if material_gain >= 9.0:  # Queen in one move
                    nerf_factor = min(nerf_factor, 0.2)  # 80% reduction in difficulty
                elif material_gain >= 5.0:  # Rook in one move
                    nerf_factor = min(nerf_factor, 0.3)  # 70% reduction in difficulty
                elif material_gain >= 3.0:  # Minor piece in one move
                    nerf_factor = min(nerf_factor, 0.4)  # 60% reduction in difficulty
            
            nerf_factors.append(nerf_factor)
            
            # Also check score change as an alternative indicator
            if score_change <= -2.0:  # Significant negative score change
                # Use score-based nerf if it's stronger
                score_based_nerf = max(0.15, 1.0 - (abs(score_change) / 8.0))
                nerf_factors.append(score_based_nerf)
        
        # If any significant nerfs were found, use the minimum (strongest) nerf
        if nerf_factors:
            # Always use the strongest nerf (don't average)
            return min(nerf_factors)  # Min value = strongest nerf
        
        return 1.0  # No nerf if no tactical sequences analyzed
    
    def _estimate_material_gain(self, position):
        """
        Estimate material gain from a tactical sequence.
        
        Args:
            position: Move evaluation dictionary with tactical sequence
            
        Returns:
            Estimated material gain in pawn units
        """
        # Get the direct score change as a baseline
        score_change = abs(position.get("score_change", 0))
        
        # If the score change is very dramatic, assume it's a major piece
        if score_change >= 6.0:
            return 9.0  # Assume queen-level gain/loss
        elif score_change >= 3.0:
            return 5.0  # Assume rook-level gain/loss
        
        tactical_sequence = position.get("tactical_sequence", [])
        if not tactical_sequence:
            # If no sequence available, use score change as a proxy
            return min(score_change * 2.5, 10.0)  # More aggressive scaling
        
        # Count material gain from captures in the sequence
        material_gain = 0.0
        for move in tactical_sequence:
            if move.get("is_capture", False):
                # We don't have the exact piece captured, so use score change
                # as a proxy, with diminishing returns for later captures
                material_gain += 1.5  # Increased from 1.0 for stronger effect
        
        # If sequence ends in checkmate, add a large value
        if tactical_sequence and "score" in tactical_sequence[-1]:
            final_score = tactical_sequence[-1]["score"]
            if abs(final_score) > 900:  # Likely checkmate
                material_gain += 10.0
        
        # If no captures detected but score improved, estimate from score change
        if material_gain == 0 and len(tactical_sequence) > 0:
            try:
                initial_score = position.get("score_before", 0)
                final_score = tactical_sequence[-1].get("score", initial_score)
                score_diff = abs(final_score - initial_score)
                material_gain = min(score_diff * 2.5, 10.0)  # More aggressive scaling
            except (KeyError, IndexError):
                pass
        
        return material_gain

# Extend GameAnalyzer class with difficulty calculation
def add_difficulty_analysis_to_game_analyzer(game_analyzer):
    """
    Extend GameAnalyzer with game difficulty calculation functionality.
    
    Args:
        game_analyzer: Instance of GameAnalyzer to extend
    """
    # Create difficulty calculator with the same engine manager
    difficulty_calculator = GameDifficultyCalculator(game_analyzer.engine_manager)
    
    # Store original analyze_game method
    original_analyze_game = game_analyzer.analyze_game
    
    # Create new analyze_game method that adds difficulty metrics
    def extended_analyze_game(*args, **kwargs):
        # Call original method
        results = original_analyze_game(*args, **kwargs)
        
        # Add difficulty metrics
        difficulty_metrics = difficulty_calculator.calculate_game_difficulty(results)
        results["difficulty_metrics"] = difficulty_metrics
        
        return results
    
    # Replace method
    game_analyzer.analyze_game = extended_analyze_game
    
    # Add the difficulty calculator as an attribute
    game_analyzer.difficulty_calculator = difficulty_calculator
    
    return game_analyzer