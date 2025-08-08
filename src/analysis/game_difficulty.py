# --- START OF FILE game_difficulty.py ---

"""
Game difficulty calculator focusing on decision complexity with tactical depth consideration,
including adjustments based on the game phase when blunders occur.
"""

import math
import chess
import numpy as np

class GameDifficultyCalculator:
    """
    Calculates the decision complexity of a chess game with tactical depth adjustments,
    mitigating the impact of blunders based on when they occur in the game.
    """

    def __init__(self, engine_manager):
        """
        Initialize the difficulty calculator.

        Args:
            engine_manager: An instance of EngineManager (or similar analysis provider)
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
        # Define game phase thresholds (using ply count)
        # These values can be adjusted based on desired phase definitions.
        self.EARLY_GAME_END_PLY = 30  # End of move 15
        self.MID_GAME_END_PLY = 80   # End of move 40

    def calculate_game_difficulty(self, analysis_results):
        """
        Calculate the difficulty of a chess game with separate metrics for each player,
        considering tactical opportunities that may reduce complexity, weighted by game phase.

        Args:
            analysis_results: Dictionary containing game analysis results.
                              Crucially, `analysis_results["move_evaluations"]` must be a list
                              of dictionaries, where each dictionary includes a 'ply' key
                              indicating the half-move number.

        Returns:
            Dictionary with overall difficulty and player-specific difficulties, including
            decision difficulty, tactical nerf factor, and precision bonus.
        """
        move_evaluations = analysis_results.get("move_evaluations", [])
        if not move_evaluations:
             # Handle case with no moves or missing data
             default_difficulty = {
                "overall_difficulty": 5.0,
                "decision_difficulty": 5.0,
                "tactical_nerf": 1.0,
                "precision_bonus": 0.0
            }
             return {
                "overall_difficulty": 5.0,
                "white_difficulty": default_difficulty,
                "black_difficulty": default_difficulty,
                "factors": {
                    "white_decision_difficulty": 5.0, "white_tactical_nerf": 1.0, "white_precision_bonus": 0.0,
                    "black_decision_difficulty": 5.0, "black_tactical_nerf": 1.0, "black_precision_bonus": 0.0
                }
            }

        # Split moves by player
        white_evals = [eval for eval in move_evaluations if eval.get("side") == "White"]
        black_evals = [eval for eval in move_evaluations if eval.get("side") == "Black"]

        # Calculate raw decision difficulty for each player
        white_decision_difficulty = self._calculate_decision_difficulty(white_evals)
        black_decision_difficulty = self._calculate_decision_difficulty(black_evals)

        # Calculate precision bonuses for high-quality play
        white_precision_bonus = self._calculate_precision_bonus(white_evals)
        black_precision_bonus = self._calculate_precision_bonus(black_evals)

        # Apply tactical complexity nerf based on OPPONENT's blunders, considering game phase.
        # White's difficulty is reduced by Black's blunders (nerf calculated from black_evals)
        # Black's difficulty is reduced by White's blunders (nerf calculated from white_evals)
        # The nerf function now considers the 'ply' of the blunder within player_evals.
        white_tactical_nerf = self._calculate_tactical_nerf(black_evals, opponent_side="White")
        black_tactical_nerf = self._calculate_tactical_nerf(white_evals, opponent_side="Black")

        # Apply the nerf to the decision difficulty and add precision bonus
        # Difficulty = (Base Decision Difficulty * Nerf Factor) + Precision Bonus
        white_difficulty_value = (white_decision_difficulty * white_tactical_nerf) + white_precision_bonus
        black_difficulty_value = (black_decision_difficulty * black_tactical_nerf) + black_precision_bonus

        # Cap at maximum difficulty of 10
        white_difficulty_value = min(10.0, max(0.0, white_difficulty_value)) # Ensure non-negative
        black_difficulty_value = min(10.0, max(0.0, black_difficulty_value)) # Ensure non-negative

        # Calculate overall game difficulty (simple average)
        overall_difficulty = (white_difficulty_value + black_difficulty_value) / 2

        # Create structured difficulty data for white and black
        white_difficulty = {
            "overall_difficulty": round(white_difficulty_value, 1),
            "decision_difficulty": round(white_decision_difficulty, 1),
            "tactical_nerf": round(white_tactical_nerf, 2), # Nerf applied *to* White's score
            "precision_bonus": round(white_precision_bonus, 2)
        }

        black_difficulty = {
            "overall_difficulty": round(black_difficulty_value, 1),
            "decision_difficulty": round(black_decision_difficulty, 1),
            "tactical_nerf": round(black_tactical_nerf, 2), # Nerf applied *to* Black's score
            "precision_bonus": round(black_precision_bonus, 2)
        }

        return {
            "overall_difficulty": round(overall_difficulty, 1),
            "white_difficulty": white_difficulty,
            "black_difficulty": black_difficulty,
            "factors": {
                "white_decision_difficulty": round(white_decision_difficulty, 1),
                "white_tactical_nerf": round(white_tactical_nerf, 2), # Nerf on White (from Black's blunders)
                "white_precision_bonus": round(white_precision_bonus, 2),
                "black_decision_difficulty": round(black_decision_difficulty, 1),
                "black_tactical_nerf": round(black_tactical_nerf, 2), # Nerf on Black (from White's blunders)
                "black_precision_bonus": round(black_precision_bonus, 2)
            }
        }

    def _calculate_decision_difficulty(self, player_evals):
        """
        Calculate decision difficulty based on the entropy of candidate move evaluations,
        with a higher baseline for positions with narrow evaluation differences. (Unchanged)

        Args:
            player_evals: List of move evaluation dictionaries for a specific player.

        Returns:
            Decision difficulty score (1-10) based on adjusted normalized entropy.
        """
        if not player_evals:
            return 5.0  # Default medium difficulty if no moves available

        # Count best move selections
        best_moves = sum(1 for eval in player_evals if eval.get("player_move_rank", -1) == 0)
        total_moves = len(player_evals)
        best_move_ratio = best_moves / total_moves if total_moves > 0 else 0

        # Best move selection bonus (selecting the best move in difficult positions is harder)
        best_move_bonus = best_move_ratio * 1.5

        move_entropies = []
        position_difficulties = []
        T = 0.3          # Temperature for softmax; lower T makes evaluation differences more pronounced.

        # Logistic scaling parameters for evaluation dominance:
        beta = 0.1       # Controls the steepness of the logistic curve.
        threshold = 50   # Evaluation threshold (in centipawns) for a balanced position.

        for eval in player_evals:
            # Skip moves without sufficient candidate moves information
            if "top_moves" not in eval or len(eval["top_moves"]) < 2:
                position_difficulties.append(5.0) # Assign default if no comparison possible
                continue

            candidates = eval["top_moves"]
            try:
                best_eval_cp = candidates[0].get("score_cp", 0) # Prefer centipawn score
            except (KeyError, IndexError):
                best_eval_cp = 0

            # Check if this is a "narrow margin" position where top moves are very close
            if len(candidates) >= 2:
                try:
                    top_diff_cp = abs(candidates[0].get("score_cp", 0) - candidates[1].get("score_cp", 0))
                    # Normalize difference relative to ~1 pawn (100 cp) for scaling
                    narrow_margin = max(0, 1.0 - (top_diff_cp / 100.0)) # Scale 0-1 based on difference up to 1 pawn
                    # Scale to difficulty range 5-9 (base 5, add up to 4 based on narrowness)
                    position_difficulties.append(5.0 + (narrow_margin * 4.0))
                except (KeyError, IndexError):
                     position_difficulties.append(5.0) # Default if scores missing
            else:
                position_difficulties.append(5.0) # Default if only one move

            # Calculate evaluation differences for entropy (use centipawns)
            evals_cp = [move.get("score_cp", best_eval_cp - 300) for move in candidates] # Default to 3 pawn diff if missing

            # Compute softmax probabilities for each candidate move
            # Use score diff relative to best move, scaled by temperature T (in cp)
            # Ensure T_cp reflects typical centipawn differences (e.g., T_cp = 50)
            T_cp = 50 # Temperature in centipawns
            try:
                # Softmax calculation: exp(-(best_eval - eval) / T) / sum(...)
                # Use positive diff (best - current), lower diff = higher probability
                score_diffs = [(best_eval_cp - e) for e in evals_cp]
                # Prevent overflow with extremely large differences by capping or shifting
                max_diff = max(score_diffs) if score_diffs else 0
                exp_terms = [math.exp(-(diff - max_diff) / T_cp) for diff in score_diffs] # Shift by max_diff for stability
                softmax_denom = sum(exp_terms)

                if softmax_denom > 0:
                    probs = [term / softmax_denom for term in exp_terms]
                else: # Avoid division by zero if all exp terms are zero (huge differences)
                    probs = [1.0 / len(evals_cp)] * len(evals_cp) # Uniform probability
            except OverflowError:
                probs = [1.0 / len(evals_cp)] * len(evals_cp) # Uniform on overflow

            # Calculate entropy of the probability distribution
            entropy = -sum(p * math.log(p) if p > 0 else 0 for p in probs)

            # Normalize entropy by the maximum possible entropy (logarithm of the number of candidates)
            max_entropy = math.log(len(candidates)) if len(candidates) > 1 else 1.0 # Avoid log(1)=0
            norm_entropy = entropy / max_entropy if max_entropy > 0 else 0

            # Compute logistic scaling factor based on game dominance (using absolute centipawn eval)
            scaling_factor = 1 / (1 + math.exp(beta * (abs(best_eval_cp) - threshold)))

            # Adjust the normalized entropy with the scaling factor.
            adjusted_entropy = scaling_factor * norm_entropy
            move_entropies.append(adjusted_entropy)

        # Calculate decision difficulty based on entropy
        if move_entropies:
            # Use median instead of mean for robustness against outliers
            avg_entropy = np.median(move_entropies)
            # Scale entropy (0-1) to difficulty range (1-10)
            entropy_difficulty = 1.0 + (avg_entropy * 9.0)
        else:
            entropy_difficulty = 5.0  # Default if no entropy data

        # Calculate position difficulty based on narrow margins
        if position_difficulties:
            # Use median for robustness
            avg_position_difficulty = np.median(position_difficulties)
        else:
            avg_position_difficulty = 5.0  # Default if no position difficulty data

        # Combine entropy-based and position-based difficulty with best move bonus
        # Weighting can be adjusted (e.g., 60% entropy, 40% position narrowness)
        combined_difficulty = (entropy_difficulty * 0.6) + (avg_position_difficulty * 0.4) + best_move_bonus

        # Cap at maximum of 10 and minimum of 1
        return min(max(combined_difficulty, 1.0), 10.0)


    def _calculate_precision_bonus(self, player_evals):
        """
        Calculate a bonus to add to game difficulty based on high-precision play.
        High-quality play (fewer mistakes, more excellent moves) in a complex game
        should result in higher perceived difficulty. (Unchanged Logic)

        Args:
            player_evals: List of move evaluation dictionaries for a specific player.

        Returns:
            Precision bonus (0.0-3.0).
        """
        if not player_evals or len(player_evals) < 5: # Require minimum moves for meaningful bonus
            return 0.0

        total_moves = len(player_evals)

        # Calculate precision (average move quality - assuming 0-1 scale)
        move_qualities = [eval.get("move_quality", 0) for eval in player_evals]
        # Use median quality for robustness
        avg_quality = np.median(move_qualities) if move_qualities else 0
        precision = avg_quality # Precision is directly related to average quality

        # Count move classifications
        excellent_count = sum(1 for eval in player_evals if eval.get("classification") == "Excellent")
        # Consider 'Good' as positive contribution too
        good_count = sum(1 for eval in player_evals if eval.get("classification") == "Bon coup") # Or "Good"
        mistake_count = sum(1 for eval in player_evals if eval.get("classification") in ["Erreur", "Grosse erreur"]) # Or "Mistake", "Blunder"

        excellent_ratio = excellent_count / total_moves
        good_ratio = good_count / total_moves
        mistake_ratio = mistake_count / total_moves

        # --- Bonus Calculation ---
        # Base bonus from overall precision (median quality)
        precision_component = precision * 1.5 # Max 1.5 points from median quality

        # Bonus specifically for excellent moves
        excellent_component = excellent_ratio * 1.5 # Max 1.5 points from excellent ratio

        # Penalty for mistakes/blunders - should significantly reduce the bonus
        # Exponential penalty might be better: penalty = mistake_ratio^0.5 * MaxPenalty
        mistake_penalty = (mistake_ratio ** 0.7) * 3.0 # Stronger penalty for any mistakes, capped at 3

        # Consider game length slightly - longer high-precision games are harder
        # Normalize length up to ~50 moves (100 ply)
        length_factor = min(1.0, total_moves / 50.0)
        length_bonus = length_factor * 0.5 # Max 0.5 bonus for length

        # Combine components: Add positive contributions, subtract penalty
        total_bonus = precision_component + excellent_component + length_bonus - mistake_penalty

        # Ensure bonus is within bounds [0, 3.0]
        # The bonus ADDS to difficulty, max increase of 3 points.
        return min(max(total_bonus, 0.0), 3.0)


    def _calculate_tactical_nerf(self, player_evals, opponent_side=""):
        """
        Calculate a tactical complexity nerf factor based on the player's blunders,
        mitigating the nerf's impact for blunders occurring later in the game.
        Easy tactics offered by the player reduce the difficulty for the opponent.

        Args:
            player_evals: List of move evaluation dictionaries for the player being evaluated
                          (whose blunders potentially make the game easier for the opponent).
                          Each dict MUST contain a 'ply' key.
            opponent_side: Side of the opponent (whose difficulty score this nerf will affect).

        Returns:
            Nerf factor between 0.1 and 1.0 (1.0 = no nerf, 0.1 = maximum nerf) to be applied
            to the *opponent's* difficulty score.
        """
        if not player_evals:
            return 1.0  # No nerf if no moves evaluated for this player

        mitigated_nerf_factors = [] # Store potential nerf factors *after* mitigation

        for eval_data in player_evals:
            # --- GET PLY NUMBER ---
            ply = eval_data.get('ply')
            if ply is None:
                 # Skip if 'ply' is missing, as phase mitigation is not possible.
                 # Log a warning if this happens frequently during debugging.
                 # print(f"Warning: 'ply' missing in evaluation data for move {eval_data.get('move_notation', '?')}, skipping nerf calc.")
                 continue

            # We are interested in blunders by *this* player (represented by player_evals),
            # which means a negative score change *for them* (positive for the opponent).
            # Use score_change_cp for better granularity if available, else score_change (pawn units)
            score_change_cp = eval_data.get("score_change_cp")
            score_change_pawns = eval_data.get("score_change")

            # Determine the relevant score change (prefer centipawns if available)
            if score_change_cp is not None:
                # Blunder threshold in CP (e.g., -150 cp = -1.5 pawns)
                is_blunder = score_change_cp <= -150
                relevant_score_change_pawns = score_change_cp / 100.0 # Convert to pawns for comparison
            elif score_change_pawns is not None:
                # Blunder threshold in Pawns (e.g., -1.5)
                is_blunder = score_change_pawns <= -1.5
                relevant_score_change_pawns = score_change_pawns
            else:
                continue # Skip if no score change information available

            # Only proceed if it's actually a blunder/significant mistake for this player
            if not is_blunder:
                continue

            # --- Calculate Base Nerf Factor (before mitigation) ---
            base_nerf_factor = 1.0 # Start assuming no nerf applicable for this specific move

            # 1. Check for Massive Blunders (e.g., >= 3 pawns lost)
            if relevant_score_change_pawns <= -3.0:
                # Severity scales from 1.0 (at -3 pawns) up to 3.0 (at -9 pawns or more)
                blunder_severity = min(abs(relevant_score_change_pawns) / 3.0, 3.0)
                # Base nerf factor: 1.0 -> 0.1 (stronger nerf for bigger blunders)
                # Nerf = 1 - (severity * factor)
                # Example: severity=1 -> nerf=1-(1*0.3)=0.7; severity=3 -> nerf=1-(3*0.3)=0.1
                current_nerf = max(0.1, 1.0 - (blunder_severity * 0.3))
                base_nerf_factor = min(base_nerf_factor, current_nerf)

            # 2. Check Critical Positions where this player made a mistake < 0
            # Use is_critical flag if available, otherwise rely on score change threshold
            is_critical = eval_data.get("is_critical", False)
            if is_critical and relevant_score_change_pawns < 0: # Already checked <= -1.5 above, so < 0 is sufficient here
                tactical_depth = eval_data.get("tactical_depth", 0)

                if tactical_depth > 0: # Tactical sequence found
                    material_gain = self._estimate_material_gain(eval_data) # Estimate gain for opponent
                    # Nerf based on gain vs depth: higher gain / lower depth = stronger nerf
                    depth_factor = max(1, tactical_depth * tactical_depth) # Penalize shallow tactics more
                    scaling = 4.0 # Adjust sensitivity
                    raw_nerf_effect = material_gain / (depth_factor * scaling)
                    tactical_nerf = 1.0 - min(0.9, raw_nerf_effect) # Allow up to 90% reduction

                    # Apply extra penalty for obvious tactics (depth 1)
                    if tactical_depth == 1:
                        if material_gain >= 9.0: tactical_nerf = min(tactical_nerf, 0.2) # Queen blunder
                        elif material_gain >= 5.0: tactical_nerf = min(tactical_nerf, 0.3) # Rook blunder
                        elif material_gain >= 3.0: tactical_nerf = min(tactical_nerf, 0.4) # Minor piece blunder

                    base_nerf_factor = min(base_nerf_factor, tactical_nerf)

                # Also consider significant score drops in critical positions even if depth calculation failed
                # (Use the already calculated relevant_score_change_pawns)
                # Use a slightly different scaling for score-based nerf
                score_based_nerf = max(0.15, 1.0 - (abs(relevant_score_change_pawns) / 8.0)) # Capped nerf effect
                base_nerf_factor = min(base_nerf_factor, score_based_nerf)


            # --- APPLY PHASE-BASED MITIGATION ---
            # Only mitigate if a nerf was actually calculated for this move (factor < 1.0)
            if base_nerf_factor < 1.0:
                mitigation_level = 0.0 # Default: no mitigation (full nerf effect in early game)
                if ply > self.MID_GAME_END_PLY: # Late Game
                    mitigation_level = 0.6 # Reduce nerf effect by 60%
                elif ply > self.EARLY_GAME_END_PLY: # Mid Game
                    mitigation_level = 0.3 # Reduce nerf effect by 30%

                # The nerf_factor reduces difficulty (multiplies it).
                # Mitigation makes the nerf factor closer to 1.0 (less reduction).
                # Original reduction = 1.0 - base_nerf_factor
                # Mitigated reduction = original_reduction * (1.0 - mitigation_level)
                # Final factor = 1.0 - mitigated_reduction
                reduction = 1.0 - base_nerf_factor
                adjusted_reduction = reduction * (1.0 - mitigation_level)
                final_nerf_factor = 1.0 - adjusted_reduction

                # Ensure the final factor is still within [0.1, 1.0] bounds
                final_nerf_factor = max(base_nerf_factor, final_nerf_factor) # Cannot be weaker than base nerf if mitigation=0
                final_nerf_factor = min(1.0, final_nerf_factor) # Cannot exceed 1.0

                mitigated_nerf_factors.append(final_nerf_factor)
            # --- End Mitigation ---


        # If any blunders occurred and generated nerf factors, find the most significant one
        # (the lowest value after mitigation) as this represents the easiest opportunity given
        # to the opponent, considering *when* it happened.
        if mitigated_nerf_factors:
            # Return the minimum factor found across all blunders
            return min(mitigated_nerf_factors)
        else:
            # If no significant blunders met the criteria, return 1.0 (no nerf)
            return 1.0

    def _estimate_material_gain(self, position):
        """
        Estimate material gain potentially available to the opponent due to this position/blunder.
        Uses score change as primary indicator, supplemented by sequence analysis if available.
        (Logic Unchanged)

        Args:
            position: Move evaluation dictionary containing score change and optionally tactical sequence.

        Returns:
            Estimated material gain in pawn units.
        """
        # Use absolute score change (positive means gain for opponent)
        score_change_cp = position.get("score_change_cp")
        score_change_pawns = position.get("score_change")

        if score_change_cp is not None:
            relevant_score_change = abs(score_change_cp / 100.0)
        elif score_change_pawns is not None:
             relevant_score_change = abs(score_change_pawns)
        else:
            relevant_score_change = 0.0 # Default if no score change data

        # Quick estimation based on magnitude of score change
        if relevant_score_change >= 6.0: return 9.0  # Assume queen-level swing
        elif relevant_score_change >= 4.0: return 5.0 # Assume rook-level swing
        elif relevant_score_change >= 2.5: return 3.0 # Assume minor piece swing

        # Refine using tactical sequence if available
        tactical_sequence = position.get("tactical_sequence", [])
        estimated_gain = 0.0

        if tactical_sequence:
            capture_gain = 0.0
            for move in tactical_sequence:
                if move.get("is_capture", False):
                    # Crude estimate per capture in sequence
                    capture_gain += 1.5 # Slightly increased weight per capture

            # Check for checkmate at the end of the sequence
            mate_bonus = 0.0
            if "score" in tactical_sequence[-1]: # Check last move score
                final_score_str = str(tactical_sequence[-1]["score"]).lower()
                if 'mate' in final_score_str: # Check for mate indicator
                     # Check if mate is in opponent's favor (positive for mate score)
                     mate_score_val = 0
                     try:
                         # Extract number after 'mate '
                         mate_in_x = int(final_score_str.split()[-1])
                         # Positive mate score is bad for the player who blundered
                         if mate_in_x > 0: # Opponent delivers mate
                            mate_bonus = 15.0 # Very large effective gain for mate
                     except: pass # Ignore parsing errors

            # If captures were found, use that primarily, add mate bonus
            if capture_gain > 0:
                estimated_gain = capture_gain + mate_bonus
            # If no captures but mate, use mate bonus
            elif mate_bonus > 0:
                estimated_gain = mate_bonus
            # If sequence exists but no captures/mate, estimate from score diff within sequence
            elif len(tactical_sequence) > 0:
                try:
                    initial_score_cp = position.get("score_before_cp", position.get("score_cp", 0) - score_change_cp if score_change_cp is not None else 0)
                    final_score_cp = tactical_sequence[-1].get("score_cp", initial_score_cp)
                    if 'mate' in str(tactical_sequence[-1].get("score","")).lower():
                         final_score_cp = 1500 * np.sign(int(str(tactical_sequence[-1].get("score","")).split()[-1])) # Large value for mate
                    
                    sequence_score_diff = abs(final_score_cp - initial_score_cp) / 100.0 # In pawns
                    estimated_gain = min(sequence_score_diff * 1.5, 10.0) # Scaled, capped gain
                except:
                    estimated_gain = min(relevant_score_change * 2.0, 10.0) # Fallback to overall change

            # Use the maximum of score-based estimate and sequence-based estimate
            return max(estimated_gain, min(relevant_score_change * 2.5, 10.0))

        else:
            # If no sequence, rely solely on the overall score change
            return min(relevant_score_change * 2.5, 10.0) # More aggressive scaling if no sequence


# Helper function to integrate with an existing GameAnalyzer class (if used)
def add_difficulty_analysis_to_game_analyzer(game_analyzer):
    """
    Extends a GameAnalyzer instance (or similar) with game difficulty calculation.

    Assumes the GameAnalyzer has an `engine_manager` attribute and an `analyze_game`
    method that returns a dictionary structure including `["move_evaluations"]`.
    Crucially, it assumes `analyze_game` populates the 'ply' key for each move evaluation.

    Args:
        game_analyzer: An instance of the GameAnalyzer class to extend.

    Returns:
        The extended GameAnalyzer instance.
    """
    # Create difficulty calculator, potentially sharing the engine manager
    difficulty_calculator = GameDifficultyCalculator(game_analyzer.engine_manager)

    # Store the original analyze_game method
    original_analyze_game = game_analyzer.analyze_game

    # Create the new analyze_game method that wraps the original and adds difficulty
    def extended_analyze_game(*args, **kwargs):
        # Call the original analysis method
        results = original_analyze_game(*args, **kwargs)

        # Ensure that each move evaluation has a 'ply' key
        move_evaluations = results.get("move_evaluations", [])
        for i, eval_data in enumerate(move_evaluations):
            if 'ply' not in eval_data:
                # Calculate ply based on index and side
                # White moves have even indices (0, 2, 4...), Black moves have odd indices (1, 3, 5...)
                if eval_data.get("side") == "White":
                    move_number = eval_data.get("move_num", ((i // 2) + 1))
                    ply = (move_number - 1) * 2
                else:  # Black
                    move_number = eval_data.get("move_num", ((i // 2) + 1))
                    ply = (move_number - 1) * 2 + 1
                
                # Add ply to the evaluation data
                eval_data['ply'] = ply
                
                # Debug output to confirm ply calculation
                # print(f"Added ply {ply} to move {eval_data.get('move_text', i)}, side: {eval_data.get('side')}")

        # Calculate and add difficulty metrics
        if "move_evaluations" in results:
            try:
                difficulty_metrics = difficulty_calculator.calculate_game_difficulty(results)
                results["game_difficulty"] = difficulty_metrics
            except Exception as e:
                print(f"Error calculating game difficulty: {e}")
                results["game_difficulty"] = None # Indicate error
        else:
             results["game_difficulty"] = None # No move evals to calculate from

        return results

    # Replace the GameAnalyzer's method with the extended version
    game_analyzer.analyze_game = extended_analyze_game

    # Optionally, add the calculator instance to the analyzer for direct access
    game_analyzer.difficulty_calculator = difficulty_calculator

    print("GameAnalyzer instance extended with difficulty calculation.")
    return game_analyzer

# --- END OF FILE game_difficulty.py ---