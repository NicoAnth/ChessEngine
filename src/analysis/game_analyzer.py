"""
Game analysis functionality for chess games.
Handles move evaluation, classification, and statistics with simplified scoring.
"""

import chess
import concurrent.futures
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
        
    def analyze_move(self, move_data):
        """
        Analyze a single move and return its evaluation.
        
        Args:
            move_data: Dictionary containing the move data needed for analysis:
                - index: The index of the move in the game
                - move: The chess.Move object
                - prev_board: The board state before the move
                - position_after: The board state after the move
                - move_num: The move number
                - side: "White" or "Black"
                - prev_score: The score before the move
                
        Returns:
            Dictionary with detailed move evaluation and critical moment status
        """
        i = move_data["index"]
        move = move_data["move"]
        prev_board = move_data["prev_board"]
        analysis_board = move_data["position_after"]
        prev_score = move_data["prev_score"]
        move_num = move_data["move_num"]
        side = move_data["side"]
        
        # Get an engine instance from the pool
        engine_instance = self.engine_manager.get_engine_instance()
        
        try:
            # Safely generate SAN notation and check move properties
            try:
                # Verify the move is legal in this position
                if move in prev_board.legal_moves:
                    move_san = prev_board.san(move)
                    is_capture = prev_board.is_capture(move)
                    gives_check = prev_board.gives_check(move)
                else:
                    # Handle illegal moves gracefully
                    move_san = move.uci()
                    is_capture = False
                    gives_check = False
            except Exception as e:
                print(f"Error generating SAN for move: {e}")
                move_san = move.uci()  # Fallback to UCI notation
                is_capture = False
                gives_check = False
            
            # Construct full move text
            move_full_text = f"{move_num}. {move_san}" if side == "White" else f"{move_num}... {move_san}"
            
            # Skip illegal moves
            if move not in prev_board.legal_moves:
                print(f"Warning: Move {move.uci()} is not legal in current position, skipping")
                self.engine_manager.release_engine_instance(engine_instance)  # Release the engine
                return {
                    "index": i,
                    "evaluation": {
                        "move_num": move_num,
                        "side": side,
                        "move_text": move_full_text,
                        "san": move_san,
                        "score_before": prev_score,
                        "score_after": prev_score,  # Keep previous score
                        "score_change": 0,
                        "classification": "Erreur",
                        "move_quality": 0.3,  # Default poor quality for illegal moves
                        "best_move": None,
                        "best_score": None,
                        "player_move_rank": -1,
                        "position_complexity": 0,
                        "is_critical": False,
                        "is_capture": is_capture,
                        "gives_check": gives_check
                    },
                    "is_critical": False
                }
            
            # Analyze the position after the move
            try:
                info = engine_instance.analyze_position(
                    analysis_board, 
                    depth=config.ENGINE_ANALYSIS["detailed_depth"],
                    multipv=1
                )
                
                # Validate that we have valid analysis info
                if not info or len(info) == 0:
                    print(f"Warning: Empty engine analysis for move {move_san}")
                    score_after = prev_score  # Use previous score as fallback
                else:
                    # Get evaluation after move
                    score_after = info[0]["score"].white().score(
                        mate_score=config.ENGINE_ANALYSIS["mate_score"]
                    ) / 100
            except Exception as e:
                print(f"Error analyzing position after move {move_san}: {e}")
                score_after = prev_score  # Use previous score as fallback
            
            # Analyze alternative moves
            try:
                alt_info = engine_instance.analyze_position(
                    prev_board,
                    depth=config.ENGINE_ANALYSIS["detailed_depth"],
                    multipv=config.ENGINE_ANALYSIS["multipv"]  # Top 3 moves for comparison
                )
                
                best_move = None
                best_score = None
                best_move_san = None
                position_complexity = 0
                
                # Calculate position complexity based on eval differences
                if len(alt_info) > 1:
                    # Calculate difference between top moves
                    top_score = alt_info[0]["score"].white().score(
                        mate_score=config.ENGINE_ANALYSIS["mate_score"]
                    ) / 100
                    second_score = alt_info[1]["score"].white().score(
                        mate_score=config.ENGINE_ANALYSIS["mate_score"]
                    ) / 100
                    top_move_diff = abs(top_score - second_score)
                    
                    # Lower diff means more complex position
                    position_complexity = max(0, min(1.0, 1.0 - (top_move_diff / 2)))
                
                # If there's at least one alternative
                if alt_info and len(alt_info) > 0:
                    # Make sure the PV contains valid moves
                    try:
                        if "pv" in alt_info[0] and len(alt_info[0]["pv"]) > 0:
                            top_move = alt_info[0]["pv"][0]
                            top_score = alt_info[0]["score"].white().score(
                                mate_score=config.ENGINE_ANALYSIS["mate_score"]
                            ) / 100
                        else:
                            print(f"Warning: Invalid PV in engine analysis for move {move_san}")
                            top_move = None
                            top_score = None
                    except Exception as e:
                        print(f"Error parsing principal variation: {e}")
                        top_move = None
                        top_score = None

                    # Find player's move in alternatives
                    player_move_rank = -1
                    player_move_score = None
                    
                    for idx, analysis in enumerate(alt_info):
                        try:
                            if "pv" in analysis and len(analysis["pv"]) > 0 and analysis["pv"][0] == move:
                                player_move_rank = idx
                                player_move_score = analysis["score"].white().score(
                                    mate_score=config.ENGINE_ANALYSIS["mate_score"]
                                ) / 100
                                break
                        except Exception as e:
                            print(f"Error comparing player move with engine move: {e}")
                            continue
                    
                    # If player's move is top move
                    if player_move_rank == 0:
                        best_move = None
                        best_score = None
                    else:
                        best_move = top_move
                        best_move_san = prev_board.san(best_move)
                        best_score = top_score
                        
                        # If player's move wasn't found in alternatives
                        if player_move_rank == -1:
                            player_move_rank = len(alt_info)
                            # Estimate player's move score from position evaluation
                            player_move_score = score_after if side == "White" else -score_after
            except Exception as e:
                print(f"Error finding alternative move: {e}")
                best_move = None
                best_move_san = None
                best_score = None
                player_move_rank = -1
                player_move_score = None
                position_complexity = 0
            
            # Adjust scores for perspective
            view_score = score_after if side == "White" else -score_after
            view_prev_score = prev_score if side == "White" else -prev_score
            
            # Calculate score change (positive is good, negative is bad)
            score_change = view_score - view_prev_score
            
            # Get the difference between player's move and best move
            score_diff_from_best = 0
            if best_score is not None and player_move_score is not None:
                if side == "White":
                    score_diff_from_best = player_move_score - best_score
                else:
                    score_diff_from_best = best_score - player_move_score
            
            # Check if this is a critical position
            is_critical = False
            if abs(score_change) >= 0.5 or position_complexity > 0.7:
                is_critical = True
                
                # Calculate tactical depth for critical positions
                tactical_depth = 0
                tactical_sequence = []
                if is_critical and "pv" in alt_info[0]:
                    tactical_depth, tactical_sequence = self.calculate_tactical_depth_with_engine(
                        prev_board.copy(), 
                        alt_info[0]["pv"], 
                        score_after,
                        engine_instance
                    )
            else:
                tactical_depth = 0
                tactical_sequence = []
            
            # Classify move and calculate move quality
            classification, move_quality = self.classify_move(
                player_move_rank,
                score_diff_from_best,
                position_complexity
            )

            # Format top moves info for difficulty calculation
            top_moves = []
            for analysis in alt_info:
                try:
                    if "pv" in analysis and len(analysis["pv"]) > 0 and "score" in analysis:
                        move_obj = analysis["pv"][0]
                        move_san_text = prev_board.san(move_obj)
                        score = analysis["score"].white().score(mate_score=config.ENGINE_ANALYSIS["mate_score"]) / 100
                        # Adjust score for Black's perspective
                        if side == "Black":
                            score = -score
                        top_moves.append({"move": move_san_text, "score": score})
                except Exception as e:
                    print(f"Error formatting top move info: {e}")
                    continue
            
            # Release the engine instance back to the pool
            self.engine_manager.release_engine_instance(engine_instance)

            # Return evaluation data
            return {
                "index": i,
                "evaluation": {
                    "move_num": move_num,
                    "side": side,
                    "move_text": move_full_text,
                    "san": move_san,
                    "score_before": prev_score,
                    "score_after": score_after,
                    "score_change": score_change,
                    "classification": classification,
                    "move_quality": move_quality,
                    "best_move": best_move_san,
                    "best_score": best_score,
                    "player_move_rank": player_move_rank,
                    "position_complexity": position_complexity,
                    "is_critical": is_critical,
                    "is_capture": is_capture,
                    "gives_check": gives_check,
                    "top_moves": top_moves,
                    # Add tactical depth information for critical positions
                    "tactical_depth": tactical_depth if is_critical else 0,
                    "tactical_sequence": tactical_sequence if is_critical else []
                },
                "is_critical": is_critical,
                "score_after": score_after  # Include score_after for next move
            }
            
        except Exception as move_error:
            print(f"Error analyzing move {i}: {move_error}")
            
            # Make sure to release the engine
            self.engine_manager.release_engine_instance(engine_instance)
            
            # Return empty evaluation as fallback
            return {
                "index": i,
                "evaluation": {
                    "move_num": move_num,
                    "side": side,
                    "move_text": f"Move {i+1}",
                    "san": "?",
                    "score_before": prev_score,
                    "score_after": prev_score,
                    "score_change": 0,
                    "classification": "Erreur",
                    "move_quality": 0.3,
                    "best_move": None,
                    "best_score": None,
                    "player_move_rank": -1,
                    "position_complexity": 0,
                    "is_critical": False,
                    "is_capture": False,
                    "gives_check": False
                },
                "is_critical": False,
                "score_after": prev_score  # Include score_after for next move
            }
            
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
        
        # Calculate player statistics based on move quality
        white_stats = self.calculate_player_stats([e for e in move_evaluations if e["side"] == "White"])
        black_stats = self.calculate_player_stats([e for e in move_evaluations if e["side"] == "Black"])
        
        # Calculate phase statistics
        opening_evals = move_evaluations[:min(10, len(move_evaluations))]
        middlegame_evals = move_evaluations[min(10, len(move_evaluations)):max(20, len(move_evaluations)-10)]
        endgame_evals = move_evaluations[max(20, len(move_evaluations)-10):]
        
        white_phase_stats = {
            "opening": self.calculate_player_stats([e for e in opening_evals if e["side"] == "White"]),
            "middlegame": self.calculate_player_stats([e for e in middlegame_evals if e["side"] == "White"]),
            "endgame": self.calculate_player_stats([e for e in endgame_evals if e["side"] == "White"])
        }
        
        black_phase_stats = {
            "opening": self.calculate_player_stats([e for e in opening_evals if e["side"] == "Black"]),
            "middlegame": self.calculate_player_stats([e for e in middlegame_evals if e["side"] == "Black"]),
            "endgame": self.calculate_player_stats([e for e in endgame_evals if e["side"] == "Black"])
        }
        
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
        
    def classify_move(self, player_move_rank, score_diff_from_best, position_complexity):
        """
        Simplified move classification based on engine rank and score difference.
        
        Args:
            player_move_rank: The rank of the player's move in engine's evaluation (0 = best move)
            score_diff_from_best: Difference between player's move score and best move score
            position_complexity: Complexity factor of the position (0-1)
            
        Returns:
            Tuple of (classification string, numerical quality score)
        """
        # Simplify classification to 5 categories:
        # Excellent, Bon coup, Imprécision, Erreur, Grosse erreur
        
        # Start with a perfect quality score
        quality = 1.0
        
        # By default, best engine move is excellent
        if player_move_rank == 0:
            return "Excellent", 1.0
        
        # For non-best moves, use score difference and complexity
        abs_diff = abs(score_diff_from_best)
        
        # Apply complexity bonus (more complex positions get more leniency)
        complexity_bonus = position_complexity * 0.2
        
        # Adjust quality score based on difference from best move
        if abs_diff > 1.5:
            quality = 0.1  # Grosse erreur
        elif abs_diff > 0.8:
            quality = 0.3  # Erreur
        elif abs_diff > 0.3:
            quality = 0.6  # Imprécision
        else:
            quality = 0.85  # Bon coup
        
        # Apply complexity bonus
        quality = min(1.0, quality + complexity_bonus)
        
        # Classify based on final quality score
        if quality >= 0.95:
            return "Excellent", quality
        elif quality >= 0.75:
            return "Bon coup", quality
        elif quality >= 0.5:
            return "Imprécision", quality
        elif quality >= 0.25:
            return "Erreur", quality
        else:
            return "Grosse erreur", quality
    
    def calculate_player_stats(self, evaluations):
        """
        Calculate player statistics focusing on move quality.
        
        Args:
            evaluations: List of move evaluation dictionaries
            
        Returns:
            Dictionary with player statistics
        """
        if not evaluations:
            return {"precision": 0, "counts": {}}
        
        # Count move classifications
        counts = {
            "Excellent": 0,
            "Bon coup": 0,
            "Imprécision": 0,
            "Erreur": 0,
            "Grosse erreur": 0
        }
        
        for eval in evaluations:
            counts[eval["classification"]] += 1
        
        # Calculate precision (average move quality)
        move_qualities = [eval.get("move_quality", 0) for eval in evaluations]
        avg_quality = sum(move_qualities) / len(move_qualities) if move_qualities else 0
        precision = avg_quality * 100
        
        # Count best moves (rank 0)
        best_moves = sum(1 for eval in evaluations if eval.get("player_move_rank", -1) == 0)
        total_moves = len(evaluations)
        best_move_percentage = best_moves / total_moves * 100 if total_moves > 0 else 0
        
        # Calculate critical accuracy
        critical_evals = [eval for eval in evaluations if eval.get("is_critical", False)]
        critical_qualities = [eval.get("move_quality", 0) for eval in critical_evals]
        critical_accuracy = sum(critical_qualities) / len(critical_qualities) * 100 if critical_qualities else 0
        
        return {
            "precision": round(precision, 1),
            "accuracy": round(precision, 1),  # Add accuracy key with same value as precision
            "best_move_percentage": round(best_move_percentage, 1),
            "critical_accuracy": round(critical_accuracy, 1),
            "counts": counts,
            "total_moves": total_moves
        }
    
    def get_classification_color(self, classification):
        """
        Get the color for a move classification.
        
        Args:
            classification: The move classification string
            
        Returns:
            Color hex code
        """
        classification_colors = {
            "Excellent": "#1976D2",   # Blue
            "Bon coup": "#4CAF50",    # Green
            "Imprécision": "#FFC107", # Amber
            "Erreur": "#FF9800",      # Orange
            "Grosse erreur": "#F44336" # Red
        }
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
        # Use the primary engine by default for backward compatibility
        return self.calculate_tactical_depth_with_engine(
            board, 
            pv, 
            starting_score, 
            self.engine_manager.primary_engine
        )
