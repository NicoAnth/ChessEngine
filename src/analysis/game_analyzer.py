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
from src.analysis.opening_detector import OpeningDetector
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
        self.opening_detector = OpeningDetector()  # Initialize opening detector
        
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
        # Vérifions explicitement si le coup fait partie d'une ouverture avant d'analyser
        is_opening_move = False
        if "opening" in move_data and move_data["opening"] is not None:
            # Vérification supplémentaire pour s'assurer que l'information d'ouverture est complète
            if "eco" in move_data["opening"] and "name" in move_data["opening"]:
                is_opening_move = True
        
        move_data["is_opening_move"] = is_opening_move
        return self.move_analyzer.analyze_move(move_data, self.move_classifier)
            
    def analyze_game(self, moves, progress_callback=None, analysis_board=None):
        """Analyse complète d'une partie avec détection améliorée de l'ouverture finale."""
        self.last_analysis_moves = moves.copy() if moves else []
        self.opening_detector.reset()

        position_history = []
        analysis_board = chess.Board() if analysis_board is None else analysis_board.copy()
        position_history.append(analysis_board.fen())

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

        print("[OPENING] Début détection améliorée")
        opening_info_by_move = [None] * (len(moves) + 1)
        temp_board_for_openings = analysis_board.copy()
        last_exact_position = 0

        for i, move in enumerate(moves):
            try:
                if move not in temp_board_for_openings.legal_moves:
                    print(f"[OPENING] Coup illégal index {i}")
                    break
                temp_board_for_openings.push(move)
                opening_info = self.opening_detector.detect_opening(temp_board_for_openings, force_exact_match=True)
                if opening_info is not None:
                    opening_info_by_move[i + 1] = opening_info
                    last_exact_position = i + 1
                    print(f"[OPENING] Exact {i+1}: {opening_info.get('name')}")
                else:
                    if len(temp_board_for_openings.move_stack) <= 30:
                        opening_info = self.opening_detector.detect_opening(temp_board_for_openings, force_exact_match=False)
                        if opening_info is not None:
                            opening_info_by_move[i + 1] = opening_info
                            last_exact_position = i + 1
                            print(f"[OPENING] Approx {i+1}: {opening_info.get('name')}")
                if opening_info_by_move[i + 1] is None and i > 0 and opening_info_by_move[i] is not None and (i + 1) <= last_exact_position + 8:
                    opening_info_by_move[i + 1] = opening_info_by_move[i]
            except Exception as e:
                print(f"[OPENING] Erreur coup {i+1}: {e}")

        print(f"[OPENING] Fin détection {sum(1 for info in opening_info_by_move if info)} coups taggés")

        move_analysis_data = []
        temp_board = analysis_board.copy()
        prev_score = start_score
        for i, move in enumerate(moves):
            side = "White" if i % 2 == 0 else "Black"
            move_num = (i // 2) + 1
            prev_board = temp_board.copy()
            try:
                if move in temp_board.legal_moves:
                    temp_board.push(move)
                    position_after = temp_board.copy()
                    opening_info = opening_info_by_move[i + 1]
                    move_data = {
                        "index": i,
                        "move": move,
                        "prev_board": prev_board,
                        "position_after": position_after,
                        "move_num": move_num,
                        "side": side,
                        "prev_score": prev_score,
                        "is_opening_move": opening_info is not None
                    }
                    if opening_info is not None:
                        move_data["opening"] = opening_info
                    move_analysis_data.append(move_data)
                    position_history.append(temp_board.fen())
                else:
                    print(f"Warning: illegal move {move.uci()}")
                    move_analysis_data.append({
                        "index": i,
                        "move": move,
                        "prev_board": prev_board,
                        "position_after": prev_board.copy(),
                        "move_num": move_num,
                        "side": side,
                        "prev_score": prev_score,
                        "is_opening_move": False
                    })
                    position_history.append(prev_board.fen())
            except Exception as e:
                print(f"Error setting up move {i}: {e}")
                move_analysis_data.append({
                    "index": i,
                    "move": move,
                    "prev_board": prev_board,
                    "position_after": prev_board.copy(),
                    "move_num": move_num,
                    "side": side,
                    "prev_score": prev_score,
                    "is_opening_move": False
                })
                position_history.append(prev_board.fen())

        move_evaluations = [None] * len(moves)
        critical_moments = []
        num_threads = config.ENGINE_ANALYSIS.get("analysis_threads", 4)
        completed = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            future_to_index = {executor.submit(self.analyze_move, data): i for i, data in enumerate(move_analysis_data)}
            for future in concurrent.futures.as_completed(future_to_index):
                i = future_to_index[future]
                try:
                    result = future.result()
                    if progress_callback:
                        completed += 1
                        progress_callback(completed)
                    move_evaluations[result["index"]] = result["evaluation"]
                    move_idx = result["index"]
                    if move_idx < len(move_analysis_data) and "opening" in move_analysis_data[move_idx]:
                        move_evaluations[move_idx]["opening"] = move_analysis_data[move_idx]["opening"]
                    if result["is_critical"]:
                        critical_moments.append(result["index"])
                    if i < len(move_analysis_data) - 1:
                        move_analysis_data[i + 1]["prev_score"] = result["score_after"]
                except Exception as e:
                    print(f"Error processing result for move {i}: {e}")

        for i, eval in enumerate(move_evaluations):
            if eval is None:
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
            if i < len(move_analysis_data) and "opening" in move_analysis_data[i]:
                move_evaluations[i]["opening"] = move_analysis_data[i]["opening"]

        white_evals = [e for e in move_evaluations if e["side"] == "White"]
        black_evals = [e for e in move_evaluations if e["side"] == "Black"]
        white_stats = self.player_stats.calculate_player_stats(white_evals)
        black_stats = self.player_stats.calculate_player_stats(black_evals)
        white_phase_stats = self.player_stats.calculate_phase_stats(white_evals)
        black_phase_stats = self.player_stats.calculate_phase_stats(black_evals)
        opening_count = sum(1 for eval in move_evaluations if "opening" in eval and eval["opening"] is not None)
        print(f"[OPENING] {opening_count}/{len(move_evaluations)} coups taggés")

        final_opening = None
        for info in reversed(opening_info_by_move):
            if info:
                final_opening = info
                break

        # Fallback par séquence de coups pour obtenir une ouverture plus spécifique
        GENERIC_NAMES = {"King's Pawn Game", "Queen's Pawn Game"}
        try:
            if (final_opening is None) or (final_opening.get("name") in GENERIC_NAMES):
                temp_board_seq = chess.Board()
                san_list = []
                for mv in moves:
                    try:
                        san_list.append(temp_board_seq.san(mv))
                        temp_board_seq.push(mv)
                    except Exception:
                        break
                # Recherche du préfixe le plus long correspondant
                for k in range(len(san_list), 1, -1):
                    candidate_moves = ' '.join(san_list[:k])
                    normalized = self.opening_detector._normalize_moves(candidate_moves)
                    if normalized in self.opening_detector.openings_by_moves:
                        cand = self.opening_detector.openings_by_moves[normalized]
                        if cand.get("name") not in GENERIC_NAMES:
                            final_opening = cand
                            print(f"[OPENING] Fallback séquence -> {cand.get('name')} (k={k})")
                            break
                        # Accepte tout si pas déjà de final_opening
                        if final_opening is None:
                            final_opening = cand
                            break
        except Exception as e:
            print(f"[OPENING] Fallback séquence erreur: {e}")

        results = {
            "move_evaluations": move_evaluations,
            "white_stats": white_stats,
            "black_stats": black_stats,
            "white_phase_stats": white_phase_stats,
            "black_phase_stats": black_phase_stats,
            "critical_moments": critical_moments,
            "position_history": position_history
        }
        if final_opening:
            results["final_opening"] = final_opening
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
