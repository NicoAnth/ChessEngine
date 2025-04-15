"""
Game analysis functionality for chess games.
Integrates the separate components to provide complete game analysis.
"""

import chess
import concurrent.futures

from src.analysis.move_analyzer import MoveAnalyzer
from src.analysis.move_classifier import MoveClassifier
from src.analysis.tactical_analyzer import TacticalAnalyzer
from src.analysis.player_stats import PlayerStats
from src.utils import config

class GameAnalyzer:
    """Analyzes chess games and provides move evaluations and statistics."""
    
    def __init__(self, engine_manager):
        """
        Initialize the game analyzer.
        
        Args:
            engine_manager: An instance of EngineManager
        """
        self.engine_manager = engine_manager
        self.last_analysis_moves = []
        
        # Initialize component analyzers
        self.move_analyzer = MoveAnalyzer(engine_manager)
        self.move_classifier = MoveClassifier()
        self.tactical_analyzer = TacticalAnalyzer(engine_manager) 
        self.player_stats = PlayerStats()
        
    # Proxy methods to maintain backward compatibility with UI code
    def get_classification_color(self, classification):
        """Proxy to MoveClassifier.get_classification_color for backward compatibility."""
        return self.move_classifier.get_classification_color(classification)
        
    def get_score_color(self, score_change):
        """Proxy to MoveClassifier.get_score_color for backward compatibility."""
        return self.move_classifier.get_score_color(score_change)
    
    def score_to_win_probability(self, score):
        """Proxy to MoveClassifier.score_to_win_probability for backward compatibility."""
        return self.move_classifier.score_to_win_probability(score)
    
    def is_move_sacrifice(self, board, move):
        """Proxy to MoveClassifier.is_move_sacrifice for backward compatibility."""
        return self.move_classifier.is_move_sacrifice(board, move)
    
    def analyze_move(self, move_data):
        """
        Analyze a single move and return its evaluation.
        
        Args:
            move_data: Dictionary containing the move data needed for analysis
                
        Returns:
            Dictionary with detailed move evaluation and critical moment status
        """
        return self.move_analyzer.analyze_move(move_data, self.move_classifier)
            
    def analyze_game(self, moves, progress_callback=None, analysis_board=None):
        """
        Analyze a complete game from a list of moves using multithreading.
        
        Args:
            moves: List of chess.Move objects
            progress_callback: Optional callback function for progress updates
            analysis_board: Optional chess.Board to use for analysis. If None, a new board is created.
            
        Returns:
            Dictionary with analysis results:
            - move_evaluations: List of move evaluation dictionaries
            - white_stats: Statistics for white player
            - black_stats: Statistics for black player
            - critical_moments: List of critical position indices
        """
        # Keep track of moves for position recreation
        self.last_analysis_moves = moves.copy() if moves else []
        
        # Store position history for each move
        position_history = []
        analysis_board = chess.Board() if analysis_board is None else analysis_board.copy()
        position_history.append(analysis_board.fen())  # Initial position
        
        # Get start position evaluation
        try:
            start_info = self.engine_manager.analyze_position(
                analysis_board, 
                depth=config.ENGINE_ANALYSIS["detailed_depth"],
                multipv=1
            )
            start_score = start_info[0]["score"].white().score(
                mate_score=config.ENGINE_ANALYSIS["mate_score"]
            ) / 100
        except Exception as e:
            print(f"Error during initial position analysis: {e}")
            start_score = 0.0
        
        # Prepare data for parallel processing
        move_analysis_data = []
        
        # First pass - create position history and prepare data for analysis
        temp_board = analysis_board.copy()
        prev_score = start_score
        
        for i, move in enumerate(moves):
            # Determine side and move number
            side = "White" if i % 2 == 0 else "Black"
            move_num = (i // 2) + 1
            
            # Store previous board state
            prev_board = temp_board.copy()
            
            # Try to make the move on a temporary board
            try:
                if move in temp_board.legal_moves:
                    temp_board.push(move)
                    position_after = temp_board.copy()
                    
                    # Add to move analysis data
                    move_analysis_data.append({
                        "index": i,
                        "move": move,
                        "prev_board": prev_board,
                        "position_after": position_after,
                        "move_num": move_num,
                        "side": side,
                        "prev_score": prev_score
                    })
                    
                    # Add position to history
                    position_history.append(temp_board.fen())
                else:
                    print(f"Warning: Move {move.uci()} is not legal in current position")
                    # Create dummy data for illegal move
                    move_analysis_data.append({
                        "index": i,
                        "move": move,
                        "prev_board": prev_board,
                        "position_after": prev_board.copy(),  # Same as prev_board for illegal move
                        "move_num": move_num,
                        "side": side,
                        "prev_score": prev_score
                    })
            except Exception as e:
                print(f"Error setting up move {i} for analysis: {e}")
                # Create dummy data for error case
                move_analysis_data.append({
                    "index": i,
                    "move": move,
                    "prev_board": prev_board,
                    "position_after": prev_board.copy(),
                    "move_num": move_num,
                    "side": side,
                    "prev_score": prev_score
                })
        
        # Analysis results
        move_evaluations = [None] * len(moves)
        critical_moments = []
        
        # Use the number of threads from config
        num_threads = config.ENGINE_ANALYSIS.get("analysis_threads", 4)
        
        # Process moves in parallel
        completed = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Submit all move analysis tasks
            future_to_index = {
                executor.submit(self.analyze_move, data): i 
                for i, data in enumerate(move_analysis_data)
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_index):
                i = future_to_index[future]
                try:
                    result = future.result()
                    
                    # Update progress if callback provided
                    if progress_callback:
                        completed += 1
                        progress_callback(completed)
                    
                    # Store the evaluation at the correct index
                    move_evaluations[result["index"]] = result["evaluation"]
                    
                    # Update critical moments list
                    if result["is_critical"]:
                        critical_moments.append(result["index"])
                        
                    # Update prev_score for next move if it exists
                    if i < len(move_analysis_data) - 1:
                        move_analysis_data[i + 1]["prev_score"] = result["score_after"]
                        
                except Exception as e:
                    print(f"Error processing result for move {i}: {e}")
        
        # Ensure all results are in order
        for i, eval in enumerate(move_evaluations):
            if eval is None:
                # Fill in any missing evaluations with placeholder
                move_num = (i // 2) + 1
                side = "White" if i % 2 == 0 else "Black"
                move_evaluations[i] = {
                    "move_num": move_num,
                    "side": side,
                    "move_text": f"Move {i+1}",
                    "san": "?",
                    "score_before": 0.0,
                    "score_after": 0.0,
                    "score_change": 0.0,
                    "classification": "Erreur",
                    "move_quality": 0.3,
                    "best_move": None,
                    "best_score": None,
                    "player_move_rank": -1,
                    "position_complexity": 0,
                    "is_critical": False,
                    "is_capture": False,
                    "gives_check": False
                }
        
        # Calculate player statistics
        white_evals = [e for e in move_evaluations if e["side"] == "White"]
        black_evals = [e for e in move_evaluations if e["side"] == "Black"]
        
        white_stats = self.player_stats.calculate_player_stats(white_evals)
        black_stats = self.player_stats.calculate_player_stats(black_evals)
        
        # Calculate phase statistics for each player
        white_phase_stats = self.player_stats.calculate_phase_stats(white_evals)
        black_phase_stats = self.player_stats.calculate_phase_stats(black_evals)
        
        results = {
            "move_evaluations": move_evaluations,
            "white_stats": white_stats,
            "black_stats": black_stats,
            "white_phase_stats": white_phase_stats,
            "black_phase_stats": black_phase_stats,
            "critical_moments": critical_moments,
            "position_history": position_history
        }
        
        return results

    def analyze_position(self, board, depth=None):
        """
        Analyze the current position and return engine evaluation.
        
        Args:
            board: The chess.Board to analyze
            depth: Optional depth for analysis (uses detailed_depth from config if None)
            
        Returns:
            Evaluation score object
        """
        if depth is None:
            depth = config.ENGINE_ANALYSIS["detailed_depth"]
            
        try:
            info = self.engine_manager.analyze_position(board, depth=depth, multipv=3)
            if info and len(info) > 0:
                # Extraire la valeur de mate si présente pour corriger les problèmes de détection
                top_score = info[0]["score"]
                if hasattr(top_score, 'mate') and top_score.mate() is not None:
                    # Si un mate est présent, s'assurer qu'il est conservé dans l'objet score
                    mate_value = top_score.mate()
                    # Ajout d'une propriété spéciale pour s'assurer que l'information de mate est transmise
                    info[0]["is_mate"] = True
                    info[0]["mate_in"] = mate_value
                return info
            return None
        except Exception as e:
            print(f"Error analyzing position: {e}")
            return None
