"""
Engine manager for Stockfish integration.
Handles initializing, communicating with, and shutting down the chess engine.
"""

import chess
import chess.engine
import threading
from src.utils import config

class EngineManager:
    """Manages the integration with Stockfish chess engine."""
    
    def __init__(self, engine_path):
        """
        Initialize the chess engine connection.
        
        Args:
            engine_path: Path to the Stockfish executable
        """
        self.engine_path = engine_path
        self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
        self.engine_lock = threading.Lock()
    
    def analyze_position(self, board, depth=None, multipv=None):
        """
        Analyze the current board position.
        
        Args:
            board: A chess.Board instance
            depth: Analysis depth
            multipv: Number of principal variations to calculate
            
        Returns:
            Analysis information from the engine
        """
        if depth is None:
            depth = config.ENGINE_ANALYSIS["default_depth"]
        
        if multipv is None:
            multipv = config.ENGINE_ANALYSIS["multipv"]
        
        # Acquire lock to ensure thread safety when communicating with engine
        with self.engine_lock:
            info = self.engine.analyse(
                board, 
                chess.engine.Limit(depth=depth), 
                multipv=multipv
            )
        return info

    def get_best_move(self, board, depth=None):
        """
        Get the best move for the current position.
        
        Args:
            board: A chess.Board instance
            depth: Analysis depth
            
        Returns:
            The best move according to the engine
        """
        if depth is None:
            depth = config.ENGINE_ANALYSIS["default_depth"]
            
        with self.engine_lock:
            result = self.engine.play(
                board,
                chess.engine.Limit(depth=depth)
            )
        return result.move
    
    def format_score(self, score_obj):
        """
        Convert a score object to a human-readable string.
        
        Args:
            score_obj: A chess.engine.Score instance
            
        Returns:
            Formatted score string (e.g. "+1.2" or "-0.5")
        """
        # Convert to centipawns and divide by 100 for a decimal value
        score = score_obj.white().score(mate_score=config.ENGINE_ANALYSIS["mate_score"]) / 100
        
        # Format: always positive means white is winning, negative means black is winning
        return f"+{abs(score):.2f}" if score > 0 else f"-{abs(score):.2f}"
    
    def quit(self):
        """Properly shut down the engine."""
        try:
            # Acquérir le lock pour éviter les conflits avec les threads d'analyse
            with self.engine_lock:
                if self.engine:
                    self.engine.quit()
                    self.engine = None
        except Exception as e:
            print(f"Error shutting down engine: {e}")
            
    def __del__(self):
        """Ensure engine is properly shut down when object is deleted."""
        self.quit()