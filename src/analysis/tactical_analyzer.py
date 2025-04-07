"""
Tactical analysis functionality for chess positions.
Handles identification and evaluation of tactical sequences.
"""

import chess
from src.utils import config

class TacticalAnalyzer:
    """Analyzes tactical sequences in chess positions."""
    
    def __init__(self, engine_manager):
        """
        Initialize the tactical analyzer.
        
        Args:
            engine_manager: An instance of EngineManager
        """
        self.engine_manager = engine_manager
        
    def calculate_tactical_depth_with_engine(self, board, pv, starting_score, engine_instance):
        """
        Calculate the depth of a tactical sequence in the principal variation using a specific engine instance.
        
        Args:
            board: The chess.Board representing the starting position
            pv: List of moves in the principal variation
            starting_score: The evaluation score at the starting position
            engine_instance: An instance of an engine to use for analysis
            
        Returns:
            Tuple of (tactical_depth, tactical_sequence)
            - tactical_depth: Number of plies (half-moves) in the tactical sequence
            - tactical_sequence: List of moves in the tactical sequence with annotations
        """
        if not pv:
            return 0, []
            
        tactical_depth = 0
        prev_score = starting_score
        tactical_sequence = []
        
        # Define material gain threshold
        material_gain_threshold = 1.5  # 1.5 pawns
        
        # Define a plateau tolerance (evaluation stabilizes)
        plateau_tolerance = 0.2
        
        # Maximum depth to search (limit to reasonable length)
        max_depth = min(10, len(pv))
        
        # Copy the board to not modify the original
        analysis_board = board.copy()
        
        for i, move in enumerate(pv[:max_depth]):
            if move not in analysis_board.legal_moves:
                break
                
            # Get move annotation
            try:
                move_san = analysis_board.san(move)
                is_capture = analysis_board.is_capture(move)
                gives_check = analysis_board.gives_check(move)
            except:
                move_san = move.uci()
                is_capture = False
                gives_check = False
                
            # Make the move
            analysis_board.push(move)
            
            # Analyze the new position with the provided engine instance
            try:
                info = engine_instance.analyze_position(
                    analysis_board,
                    depth=config.ENGINE_ANALYSIS["tactical_depth"] if hasattr(config.ENGINE_ANALYSIS, "tactical_depth") else 16,
                    multipv=1
                )
                
                current_score = info[0]["score"].white().score(
                    mate_score=config.ENGINE_ANALYSIS["mate_score"]
                ) / 100
            except Exception as e:
                print(f"Error analyzing position in tactical sequence: {e}")
                break
                
            # Store move data
            move_data = {
                "san": move_san,
                "score": current_score,
                "is_capture": is_capture,
                "gives_check": gives_check
            }
            tactical_sequence.append(move_data)
            
            # Check for stopping criteria
            
            # 1. Checkmate detected
            if info[0]["score"].is_mate():
                tactical_depth = i + 1
                break
                
            # 2. Material gain threshold reached
            score_change = abs(current_score - starting_score)
            if score_change >= material_gain_threshold:
                tactical_depth = i + 1
                break
                
            # 3. Position stabilizes (evaluation plateaus)
            score_diff = abs(current_score - prev_score)
            if i > 1 and score_diff < plateau_tolerance:
                tactical_depth = i + 1
                break
                
            # Update previous score
            prev_score = current_score
            
            # Increment tactical depth
            tactical_depth = i + 1
            
        return tactical_depth, tactical_sequence
        
    def calculate_tactical_depth(self, board, pv, starting_score):
        """
        Calculate the depth of a tactical sequence in the principal variation using the primary engine.
        
        Args:
            board: The chess.Board representing the starting position
            pv: List of moves in the principal variation
            starting_score: The evaluation score at the starting position
            
        Returns:
            Tuple of (tactical_depth, tactical_sequence)
            - tactical_depth: Number of plies (half-moves) in the tactical sequence
            - tactical_sequence: List of moves in the tactical sequence with annotations
        """
        # Use the primary engine by default
        return self.calculate_tactical_depth_with_engine(
            board, 
            pv, 
            starting_score, 
            self.engine_manager.primary_engine
        )