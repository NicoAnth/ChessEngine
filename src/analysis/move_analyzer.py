"""
Move analysis functionality for chess games.
Handles individual move evaluation and assessment.
"""

import chess
from src.utils import config

class MoveAnalyzer:
    """Analyzes individual chess moves and provides detailed evaluations."""
    
    def __init__(self, engine_manager):
        """
        Initialize the move analyzer.
        
        Args:
            engine_manager: An instance of EngineManager
        """
        self.engine_manager = engine_manager
    
    def analyze_move(self, move_data, move_classifier):
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
            move_classifier: An instance of MoveClassifier for classifying moves
                
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
                    from src.analysis.tactical_analyzer import TacticalAnalyzer
                    tactical_analyzer = TacticalAnalyzer(self.engine_manager)
                    tactical_depth, tactical_sequence = tactical_analyzer.calculate_tactical_depth_with_engine(
                        prev_board.copy(), 
                        alt_info[0]["pv"], 
                        score_after,
                        engine_instance
                    )
            else:
                tactical_depth = 0
                tactical_sequence = []
            
            # Check if move is a sacrifice
            is_sacrifice = move_classifier.is_move_sacrifice(prev_board, move)
            
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
            
            # Calculate top moves evaluation drop if we have multiple alternatives
            top_moves_eval_drop = 0
            if len(alt_info) > 1:
                top_score = alt_info[0]["score"].white().score(mate_score=config.ENGINE_ANALYSIS["mate_score"]) / 100
                second_score = alt_info[1]["score"].white().score(mate_score=config.ENGINE_ANALYSIS["mate_score"]) / 100
                # Adjust for perspective
                if side == "Black":
                    top_score = -top_score
                    second_score = -second_score
                top_moves_eval_drop = abs(top_score - second_score)
            
            # Classify move and calculate move quality using Expected Points model
            classification, move_quality = move_classifier.classify_move(
                player_move_rank,
                score_diff_from_best,
                position_complexity,
                prev_score=prev_score,
                score_after=score_after,
                is_capture=is_capture,
                is_sacrifice=is_sacrifice,
                top_moves=top_moves,
                top_moves_eval_drop=top_moves_eval_drop,
                best_score=best_score
            )

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
                    "best_move": best_move_san,  # Keep SAN format for display
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