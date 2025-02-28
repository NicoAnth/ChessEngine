"""
Game analysis functionality for chess games.
Handles move evaluation, classification, and statistics with simplified scoring.
"""

import chess
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
        
    def analyze_game(self, moves, progress_callback=None):
        """
        Analyze a complete game from a list of moves.
        
        Args:
            moves: List of chess.Move objects
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary with analysis results:
            - move_evaluations: List of move evaluation dictionaries
            - white_stats: Statistics for white player
            - black_stats: Statistics for black player
            - critical_moments: List of critical position indices
        """
        # Clone board state to analyze from the beginning
        analysis_board = chess.Board()
        total_moves = len(moves)
        
        # Analysis results
        move_evaluations = []
        critical_moments = []
        
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
        
        prev_score = start_score
        position_complexity = 0  # Track position complexity
        
        # Analyze each move
        for i, move in enumerate(moves):
            try:
                # Update progress if callback provided
                if progress_callback:
                    progress_callback(i + 1)
                
                # Store previous board state for SAN notation
                prev_board_fen = analysis_board.fen()
                prev_board = chess.Board(prev_board_fen)
                move_san = prev_board.san(move)
                
                # Check if move is a capture or check
                is_capture = prev_board.is_capture(move)
                gives_check = prev_board.gives_check(move)
                
                # Play the move
                analysis_board.push(move)
                
                # Determine side and move text
                side = "White" if i % 2 == 0 else "Black"
                move_num = (i // 2) + 1
                move_full_text = f"{move_num}. {move_san}" if side == "White" else f"{move_num}... {move_san}"
                
                # Analyze the position after the move
                info = self.engine_manager.analyze_position(
                    analysis_board, 
                    depth=config.ENGINE_ANALYSIS["detailed_depth"],
                    multipv=1
                )
                
                # Get evaluation after move
                score_after = info[0]["score"].white().score(
                    mate_score=config.ENGINE_ANALYSIS["mate_score"]
                ) / 100
                
                # Analyze alternative moves
                try:
                    alt_info = self.engine_manager.analyze_position(
                        prev_board,
                        depth=config.ENGINE_ANALYSIS["detailed_depth"],
                        multipv=3  # Top 3 moves for comparison
                    )
                    
                    best_move = None
                    best_score = None
                    best_move_san = None
                    
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
                    if alt_info:
                        top_move = alt_info[0]["pv"][0]
                        top_score = alt_info[0]["score"].white().score(
                            mate_score=config.ENGINE_ANALYSIS["mate_score"]
                        ) / 100
                        
                        # Find player's move in alternatives
                        player_move_rank = -1
                        player_move_score = None
                        
                        for idx, analysis in enumerate(alt_info):
                            if analysis["pv"][0] == move:
                                player_move_rank = idx
                                player_move_score = analysis["score"].white().score(
                                    mate_score=config.ENGINE_ANALYSIS["mate_score"]
                                ) / 100
                                break
                        
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
                    critical_moments.append(i)
                
                # Classify move and calculate move quality
                classification, move_quality = self.classify_move(
                    player_move_rank,
                    score_diff_from_best,
                    position_complexity
                )
                
                # Store evaluation data
                move_evaluations.append({
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
                    "gives_check": gives_check
                })
                
                # Update previous score for next move
                prev_score = score_after
                
            except Exception as move_error:
                print(f"Error analyzing move {i}: {move_error}")
                # Add empty evaluation to keep the sequence
                move_evaluations.append({
                    "move_num": (i // 2) + 1,
                    "side": "White" if i % 2 == 0 else "Black",
                    "move_text": f"Move {i+1}",
                    "san": "?",
                    "score_before": 0,
                    "score_after": 0,
                    "score_change": 0,
                    "classification": "Bon coup",
                    "move_quality": 0.7,  # Default quality
                    "best_move": None,
                    "best_score": None,
                    "player_move_rank": -1,
                    "position_complexity": 0,
                    "is_critical": False,
                    "is_capture": False,
                    "gives_check": False
                })
        
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
        
        return {
            "move_evaluations": move_evaluations,
            "white_stats": white_stats,
            "black_stats": black_stats,
            "white_phase_stats": white_phase_stats,
            "black_phase_stats": black_phase_stats,
            "critical_moments": critical_moments
        }
        
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