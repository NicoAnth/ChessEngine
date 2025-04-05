"""
Engine manager for Stockfish integration.
Handles initializing, communicating with, and shutting down the chess engine.
Supports multiple engine instances for parallel analysis.
"""

import chess
import chess.engine
import threading
import queue
from src.utils import config

class EngineInstance:
    """Represents a single Stockfish engine instance."""
    
    def __init__(self, engine_path, threads=None):
        """
        Initialize a single chess engine connection.
        
        Args:
            engine_path: Path to the Stockfish executable
            threads: Number of threads for this engine instance to use internally
        """
        self.engine_path = engine_path
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        
        # Configure engine settings
        if threads is None:
            threads = config.ENGINE_ANALYSIS.get("engine_threads_per_instance", 1)
        
        # Set threads for Stockfish's internal parallelism
        try:
            self.engine.configure({"Threads": threads})
            print(f"Engine configured with {threads} internal threads")
        except Exception as e:
            print(f"Could not configure engine threads: {e}")
            
        self.lock = threading.Lock()
        self.in_use = False
    
    def analyze_position(self, board, depth=None, multipv=None):
        """Analyze the current board position."""
        with self.lock:
            info = self.engine.analyse(
                board, 
                chess.engine.Limit(depth=depth), 
                multipv=multipv
            )
        return info
    
    def get_best_move(self, board, depth=None):
        """Get the best move for the current position."""
        with self.lock:
            result = self.engine.play(
                board,
                chess.engine.Limit(depth=depth)
            )
        return result.move
    
    def quit(self):
        """Safely shut down the engine process."""
        if not hasattr(self, 'engine') or self.engine is None:
            return
            
        try:
            # Check if the engine is still running before trying to quit
            if hasattr(self.engine, 'ping') and self.engine.protocol.returncode is None:
                # First try a clean shutdown
                try:
                    self.engine.quit(timeout=0.5)
                except Exception as e:
                    print(f"Clean engine shutdown failed, forcing termination: {e}")
                    
            # Force termination if engine is still running
            if hasattr(self.engine, 'protocol') and hasattr(self.engine.protocol, 'process'):
                if self.engine.protocol.process and self.engine.protocol.returncode is None:
                    try:
                        self.engine.protocol.process.terminate()
                        # Allow a brief moment for process to terminate
                        import time
                        time.sleep(0.1)
                    except Exception:
                        pass  # Already terminated
                        
            self.engine = None
        except Exception as e:
            print(f"Error during engine shutdown: {e}")
            self.engine = None  # Ensure engine reference is cleared even on error

class EngineManager:
    """Manages multiple Stockfish engine instances for parallel analysis."""
    
    def __init__(self, engine_path):
        """
        Initialize the engine manager with multiple engine instances.
        
        Args:
            engine_path: Path to the Stockfish executable
        """
        self.engine_path = engine_path
        self.engine_pool = []
        self.engine_pool_lock = threading.Lock()
        
        # Create a pool of engine instances
        num_engines = config.ENGINE_ANALYSIS.get("analysis_threads", max(1, min(4, (threading.active_count() + 1) // 2)))
        print(f"Initializing {num_engines} Stockfish engine instances...")
        
        for _ in range(num_engines):
            self.engine_pool.append(EngineInstance(engine_path))
        
        # Keep one engine instance for "regular" usage outside of game analysis
        self.primary_engine = EngineInstance(engine_path)
        
        print(f"Engine pool initialized with {len(self.engine_pool)} engines")
    
    def get_engine_instance(self):
        """
        Get an available engine instance from the pool.
        
        Returns:
            An EngineInstance object
        """
        with self.engine_pool_lock:
            # Find an available engine
            for engine in self.engine_pool:
                if not engine.in_use:
                    engine.in_use = True
                    return engine
                    
            # If no engine is available, use the primary engine as fallback
            return self.primary_engine
    
    def release_engine_instance(self, engine_instance):
        """
        Release an engine instance back to the pool.
        
        Args:
            engine_instance: The EngineInstance to release
        """
        with self.engine_pool_lock:
            if engine_instance in self.engine_pool:
                engine_instance.in_use = False
    
    def analyze_position(self, board, depth=None, multipv=None):
        """
        Analyze the current board position using the primary engine.
        
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
        
        # Use the primary engine for regular analysis
        return self.primary_engine.analyze_position(board, depth, multipv)

    def get_best_move(self, board, depth=None):
        """
        Get the best move for the current position using the primary engine.
        
        Args:
            board: A chess.Board instance
            depth: Analysis depth
            
        Returns:
            The best move according to the engine
        """
        if depth is None:
            depth = config.ENGINE_ANALYSIS["default_depth"]
            
        return self.primary_engine.get_best_move(board, depth)
    
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
        """Safely shut down all engine processes."""
        # Shut down all engine instances in the pool
        with self.engine_pool_lock:
            for engine in self.engine_pool:
                engine.quit()
            self.engine_pool = []
            
        # Shut down the primary engine
        if hasattr(self, 'primary_engine'):
            self.primary_engine.quit()
            self.primary_engine = None
    
    def __del__(self):
        """Ensure all engines are properly shut down when object is deleted."""
        self.quit()
