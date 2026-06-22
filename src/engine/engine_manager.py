"""
Engine manager for Stockfish integration.
Handles initializing, communicating with, and shutting down the chess engine.
Supports multiple engine instances for parallel analysis.
"""

import chess
import chess.engine
import contextlib
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

        # Set threads + transposition table size for Stockfish.
        options = {"Threads": threads}
        hash_mb = config.ENGINE_ANALYSIS.get("hash_mb")
        if hash_mb:
            options["Hash"] = hash_mb
        try:
            self.engine.configure(options)
            print(f"Engine configured with {threads} thread(s), Hash={hash_mb}MB")
        except Exception as e:
            print(f"Could not configure engine: {e}")

        self.lock = threading.Lock()
        self.in_use = False

    def analyze_position(self, board, depth=None, multipv=None):
        """Analyze the current board position.

        game=object() forces a fresh 'ucinewgame' before every search, which clears
        the transposition table. The depth-N result then depends ONLY on the position
        (not on what was analysed before), making the analysis deterministic and
        independent of order/instance — a prerequisite for the parallel engine pool.
        Without it, the warm TT makes the depth-16 eval drift (~0.02 pawn, cf bench).
        """
        with self.lock:
            info = self.engine.analyse(
                board,
                chess.engine.Limit(depth=depth),
                multipv=multipv,
                game=object(),
            )
        return info

    def get_best_move(self, board, depth=None):
        """Get the best move for the current position."""
        with self.lock:
            result = self.engine.play(
                board,
                chess.engine.Limit(depth=depth),
                game=object(),
            )
        return result.move

    def quit(self):
        """Terminate the Stockfish subprocess.

        Best-effort then forceful so shutdown never hangs: engine.quit() sends the
        UCI 'quit' and reaps the process; if that fails, engine.close() tears down
        the transport (kills the subprocess). The previous version called
        quit(timeout=...) — an unsupported kwarg — and fell through to a terminate()
        path whose attributes don't exist, leaving the subprocess (and its non-daemon
        I/O thread) alive and hanging interpreter shutdown.
        """
        eng = getattr(self, "engine", None)
        if eng is None:
            return
        self.engine = None
        try:
            eng.quit()
        except Exception:
            try:
                eng.close()
            except Exception:
                pass


class EngineManager:
    """Pool of Stockfish instances for concurrent analysis (one position per instance).

    Acquire/release are backed by a blocking queue.Queue: a worker that asks for an
    instance when none is free WAITS for one to be released instead of falling back
    to a shared engine. (The previous implementation returned a single 'primary'
    engine as a fallback, which silently serialised every excess worker on one UCI
    pipe and capped the speedup.) Each EngineInstance is therefore used by at most
    one thread at a time, so its stdin/stdout stream is never interleaved.

    Pair this with a ThreadPoolExecutor sized == pool size so no worker ever blocks.
    """

    def __init__(self, engine_path, size=None):
        self.engine_path = engine_path
        if size is None:
            size = config.ENGINE_ANALYSIS.get("pool_size", 4)
        self.size = max(1, int(size))

        print(f"Initializing engine pool: {self.size} instance(s)...")
        self._all = [EngineInstance(engine_path) for _ in range(self.size)]
        self._available = queue.Queue()
        for inst in self._all:
            self._available.put(inst)
        print(f"Engine pool ready: {self.size} instance(s)")

    def acquire(self, timeout=None):
        """Block until an engine instance is free, then reserve it."""
        return self._available.get(timeout=timeout)

    def release(self, inst):
        """Return an instance to the pool so another worker can use it."""
        self._available.put(inst)

    @contextlib.contextmanager
    def lease(self, timeout=None):
        """Context manager: acquire an instance and guarantee its release."""
        inst = self.acquire(timeout=timeout)
        try:
            yield inst
        finally:
            self.release(inst)

    def analyze_position(self, board, depth=None, multipv=None):
        """Analyze a position on any free instance (leased then returned)."""
        if depth is None:
            depth = config.ENGINE_ANALYSIS["default_depth"]
        if multipv is None:
            multipv = config.ENGINE_ANALYSIS["multipv"]
        with self.lease() as inst:
            return inst.analyze_position(board, depth, multipv)

    def get_best_move(self, board, depth=None):
        """Get the best move on any free instance (leased then returned)."""
        if depth is None:
            depth = config.ENGINE_ANALYSIS["default_depth"]
        with self.lease() as inst:
            return inst.get_best_move(board, depth)

    def format_score(self, score_obj):
        """Convert a score object to a human-readable string (e.g. '+1.20')."""
        score = score_obj.white().score(mate_score=config.ENGINE_ANALYSIS["mate_score"]) / 100
        return f"+{abs(score):.2f}" if score > 0 else f"-{abs(score):.2f}"

    def quit(self):
        """Safely shut down every engine process in the pool."""
        for inst in getattr(self, "_all", []):
            try:
                inst.quit()
            except Exception:
                pass
        self._all = []

    def __del__(self):
        """Ensure all engines are properly shut down when object is deleted."""
        self.quit()
