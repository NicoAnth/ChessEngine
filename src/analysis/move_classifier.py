"""
Chess move classification functionality.
Handles evaluation and categorization of chess moves based on various criteria.
"""

import chess
import math
from src.utils import config

class MoveClassifier:
    """Classifies chess moves based on quality, complexity, and expected points model."""
    
    def __init__(self):
        """Initialize the move classifier."""
        pass
        
    def score_to_win_probability(self, score):
        """
        Convert an engine score (in pawns) to a win probability (0.0 to 1.0).
        
        Args:
            score: Score value in pawns (positive for white, negative for black)
            
        Returns:
            Win probability as a float between 0.0 and 1.0
        """
        # Standard logistic function: P(win) = 1 / (1 + 10^(-eval/4))
        # This models chess statistics where:
        # - A score of 0.0 (equal position) = 50% win probability
        # - A score of +1.0 pawns (small advantage) ≈ 76% win probability
        # - A score of +2.0 pawns (clear advantage) ≈ 90% win probability
        # - A score of +5.0 pawns (winning advantage) ≈ 99% win probability
        return 1 / (1 + math.pow(10, -score/4))
    
    def is_move_sacrifice(self, board, move):
        """
        Determine if a move is a material sacrifice.
        
        Args:
            board: The board position before the move
            move: The chess.Move to check
            
        Returns:
            Boolean indicating if the move is a sacrifice
        """
        # More accurate piece values (including positional factors)
        piece_values = {
            chess.PAWN: 1.0,
            chess.KNIGHT: 3.0,
            chess.BISHOP: 3.25,  # Slightly higher than knight in most positions
            chess.ROOK: 5.0, 
            chess.QUEEN: 9.0,
            chess.KING: 0.0      # Not relevant for sacrifice calculations
        }
        
        # Determine the moving piece type
        piece_moved = board.piece_at(move.from_square)
        if not piece_moved or piece_moved.piece_type == chess.KING:
            return False  # Kings can't be sacrificed
            
        piece_value = piece_values.get(piece_moved.piece_type, 0)
        
        # --- Direct capture sacrifice check ---
        if board.is_capture(move):
            captured_square = move.to_square
            if board.is_en_passant(move):
                # Special case for en passant captures
                captured_square = chess.square(chess.square_file(move.to_square), 
                                              chess.square_rank(move.from_square))
                
            captured_piece = board.piece_at(captured_square)
            if captured_piece:
                captured_value = piece_values.get(captured_piece.piece_type, 0)
                
                # Simple sacrifice: giving up a higher value piece for a lower value one
                if piece_value - captured_value >= config.MOVE_CLASSIFICATION["sacrifice_threshold"]:
                    return True
        
        # --- Make the move on a temporary board to analyze the resulting position ---
        temp_board = board.copy()
        temp_board.push(move)
        
        # --- Check if the piece can be captured after the move ---
        attackers = temp_board.attackers(not piece_moved.color, move.to_square)
        if attackers:
            # Calculate total value of attackers and defenders
            defenders = temp_board.attackers(piece_moved.color, move.to_square)
            
            # Get the smallest attacker (usually the one that would capture)
            smallest_attacker_value = float('inf')
            for attacker in attackers:
                attacker_piece = temp_board.piece_at(attacker)
                if attacker_piece:
                    attacker_value = piece_values.get(attacker_piece.piece_type, 0)
                    smallest_attacker_value = min(smallest_attacker_value, attacker_value)
            
            # If there are no defenders or the piece is of higher value than the smallest attacker
            if not defenders or piece_value > smallest_attacker_value:
                # This is a sacrifice - the piece is offered without adequate defense
                return True
                
            # Even with defenders, if piece value is substantially higher than the smallest attacker
            # and there are more attackers than defenders, it's likely a sacrifice
            if piece_value - smallest_attacker_value >= config.MOVE_CLASSIFICATION["sacrifice_threshold"] and len(attackers) > len(defenders):
                return True
        
        # --- Check for delayed/positional sacrifices ---
        
        # Pawns moving to 7th/2nd rank with enemy piece nearby might be sacrificing for promotion
        if piece_moved.piece_type == chess.PAWN:
            rank = chess.square_rank(move.to_square)
            if (piece_moved.color == chess.WHITE and rank == 6) or (piece_moved.color == chess.BLACK and rank == 1):
                # Check if pawn is likely to be captured before promotion
                if attackers:
                    return True
        
        # Knight outpost sacrifice (knight moves to advanced position where it might be captured)
        if piece_moved.piece_type == chess.KNIGHT:
            # For white knights, an outpost is typically on ranks 5-7
            # For black knights, an outpost is typically on ranks 2-4
            rank = chess.square_rank(move.to_square)
            in_outpost_position = (piece_moved.color == chess.WHITE and rank >= 4) or \
                                (piece_moved.color == chess.BLACK and rank <= 3)
                                
            # Knight on an advanced rank with attackers is likely a sacrifice
            if in_outpost_position and attackers:
                return True
        
        # Exchange sacrifice (trading a better piece for a worse one, but not directly)
        # Look for pieces that might be attacking the same square after our move
        for square in chess.SQUARES:
            target_piece = temp_board.piece_at(square)
            if (target_piece and target_piece.color != piece_moved.color and 
                temp_board.is_attacked_by(piece_moved.color, square)):
                
                # The moving piece enables an attack on this target
                if not board.is_attacked_by(piece_moved.color, square):
                    target_value = piece_values.get(target_piece.piece_type, 0)
                    # If we're enabling the capture of a piece worth less than what we moved
                    # it might be a sacrifice
                    if piece_value - target_value >= config.MOVE_CLASSIFICATION["sacrifice_threshold"]:
                        return True
        
        return False
        
    def is_only_good_move(self, player_move_rank, top_moves_eval_drop):
        """
        Determine if a move was the only good option in the position.
        
        Args:
            player_move_rank: The rank of the player's move (0 = best move)
            top_moves_eval_drop: The evaluation drop between top moves
            
        Returns:
            Boolean indicating if this was the only good move
        """
        # If it's not the top move, it can't be the only good move
        if player_move_rank != 0:
            return False
            
        # Check if alternative moves show a significant drop in evaluation
        if top_moves_eval_drop >= config.MOVE_CLASSIFICATION["only_move_eval_drop"]:
            return True
            
        return False
            
    def classify_move(self, player_move_rank, score_diff_from_best, position_complexity,
                     prev_score=None, score_after=None, is_capture=False, is_sacrifice=False,
                     top_moves=None, top_moves_eval_drop=None, best_score=None):
        """
        Classify move based on the Expected Points model and special cases.

        Args:
            player_move_rank: The rank of the player's move in engine's evaluation (0 = best move)
            score_diff_from_best: Difference between player's move score and best move score
            position_complexity: Complexity factor of the position (0-1)
            prev_score: The evaluation before the move (optional)
            score_after: The evaluation after the move (optional)
            is_capture: Whether the move is a capture (optional)
            is_sacrifice: Whether the move is a material sacrifice (optional)
            top_moves: List of top moves and their scores (optional)
            top_moves_eval_drop: The evaluation drop between top moves (optional)
            best_score: The evaluation score after the engine's best move (optional)

        Returns:
            Tuple of (classification string, numerical quality score [0-1])
        """
        # Initialize variables
        expected_points_loss = 0.0
        position_improved = False
        winning_threshold = config.MOVE_CLASSIFICATION["winning_position_threshold"]
        win_prob_before = 0.5 # Default if prev_score is None
        win_prob_after = 0.5 # Default if score_after is None

        # Calculate expected points loss by comparing win probability AFTER player's move vs AFTER best move
        if player_move_rank > 0 and best_score is not None and score_after is not None:
            # Convert evaluation scores (always from White's perspective) to win probabilities
            best_move_win_prob = self.score_to_win_probability(best_score)
            player_move_win_prob = self.score_to_win_probability(score_after)
            expected_points_loss = abs(best_move_win_prob - player_move_win_prob)
        elif player_move_rank == 0: # If it's the best move, loss is 0
             expected_points_loss = 0.0
        # else: Keep expected_points_loss = 0.0 if scores are missing, avoid penalizing analysis errors

        # Calculate if position improved and get win probabilities
        position_improvement = 0
        if prev_score is not None and score_after is not None:
            win_prob_before = self.score_to_win_probability(prev_score)
            win_prob_after = self.score_to_win_probability(score_after)
            position_improvement = win_prob_after - win_prob_before
            improvement_threshold = config.MOVE_CLASSIFICATION["position_improvement_threshold"]
            if position_improvement >= improvement_threshold:
                position_improved = True

        # --- Special Case Classification Logic ---

        # Best move (Rank 0 in engine analysis)
        if player_move_rank == 0:
            if position_complexity > 0.7 or (top_moves_eval_drop is not None and top_moves_eval_drop >= 0.8):
                # No quality calculation needed here, classification is enough
                pass # Fall through to general classification
            else:
                 # No quality calculation needed here, classification is enough
                pass # Fall through to general classification

        # Super coup
        # Ensure win_prob_before/after were calculated
        if prev_score is not None and score_after is not None and player_move_rank <= 1:
             # Check conditions using win_prob_before and win_prob_after
             is_super_coup = (
                 #(win_prob_before < 0.35 and win_prob_after >= 0.45) or
                 #(win_prob_before >= 0.45 and win_prob_before < 0.6 and win_prob_after >= 0.8) or
                 (self.is_only_good_move(player_move_rank, top_moves_eval_drop) and position_complexity > 0.7)
             )
             if is_super_coup:
                 # Quality is based on expected points loss, classification is special
                 quality = max(0.0, min(1.0, 1.0 - expected_points_loss))
                 return "Super coup", quality # Return quality along with special classification

        # Coup brillant - DÉSACTIVÉ
        # La section suivante est commentée pour désactiver temporairement la classification "Coup brillant"
        """
        if is_sacrifice and player_move_rank <= 1 and score_after is not None:
            if self.score_to_win_probability(score_after) >= 0.5:
                 # Quality is based on expected points loss, classification is special
                quality = max(0.0, min(1.0, 1.0 - expected_points_loss))
                return "Coup brillant", quality # Return quality along with special classification
        """

        # --- General Classification Logic ---

        # Apply complexity bonus *before* final quality calculation
        if position_complexity > 0.5:
            complexity_factor = position_complexity * 0.4
            adjusted_loss = expected_points_loss * (1.0 - complexity_factor)
        else:
            adjusted_loss = expected_points_loss

        # Calculate quality score (inverse of adjusted loss)
        quality = max(0.0, min(1.0, 1.0 - adjusted_loss))

        # Classify based on UNADJUSTED expected points loss thresholds for consistency
        # The quality score reflects complexity, but classification reflects raw error magnitude
        loss_thresholds = config.MOVE_CLASSIFICATION
        if player_move_rank == 0: # Already handled best/excellent distinction earlier implicitly
             classification = "Excellent" # Default best move classification if not 'Meilleur coup'
             if position_complexity > 0.7 or (top_moves_eval_drop is not None and top_moves_eval_drop >= 0.8):
                 classification = "Meilleur coup"
        elif expected_points_loss <= loss_thresholds["excellent_threshold"]:
            classification = "Excellent"
        elif expected_points_loss <= loss_thresholds["bon_coup_threshold"]:
            classification = "Bon coup"
        elif expected_points_loss <= loss_thresholds["imprecision_threshold"]:
            classification = "Imprécision"
        elif expected_points_loss <= loss_thresholds["erreur_threshold"]:
            classification = "Erreur"
        else:
            classification = "Grosse erreur"

        return classification, quality
    
    def get_classification_color(self, classification):
        """
        Get the color for a move classification.
        
        Args:
            classification: The move classification string
            
        Returns:
            Color hex code
        """
        # Standard classifications
        classification_colors = {
            "Meilleur coup": "#1E88E5",   # Blue
            "Excellent": "#1976D2",       # Dark Blue
            "Bon coup": "#4CAF50",        # Green
            "Imprécision": "#FFC107",     # Amber
            "Erreur": "#FF9800",          # Orange
            "Grosse erreur": "#F44336",   # Red
            
            # Special classifications
            "Super coup": "#8E24AA",      # Purple
            "Coup brillant": "#D81B60"    # Pink
        }
        
        # Try to get from standard classifications, fallback to special ones if defined
        return classification_colors.get(classification, "#000000")

    def get_score_color(self, score_change):
        """
        Get the color for a score change.
        
        Args:
            score_change: The change in score
            
        Returns:
            Color hex code
        """
        if score_change > 0.05:
            return "#4CAF50"  # Green for positive score changes
        elif score_change < -0.05:
            return "#F44336"  # Red for negative score changes
        else:
            return "#757575"  # Gray for neutral score changes