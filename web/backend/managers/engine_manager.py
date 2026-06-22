import logging
from typing import Optional
from src.engine.engine_manager import EngineInstance, EngineManager as EnginePool
from ..config import DEFAULT_ENGINE_PATH

logger = logging.getLogger(__name__)


class EngineManager:
    """Web access point to Stockfish.

    - get_instance(): a single shared EngineInstance for live, one-position-at-a-time
      endpoints (move / bestmove / analyze). Serial use, no contention.
    - get_pool(): a pool of N instances (config pool_size) for analysing many
      independent positions concurrently — used by the (parallel) PGN import.
    """

    _instance: Optional[EngineInstance] = None
    _pool: Optional[EnginePool] = None
    _error: Optional[str] = None

    @classmethod
    def get_instance(cls) -> Optional[EngineInstance]:
        if cls._instance is None:
            try:
                cls._instance = EngineInstance(DEFAULT_ENGINE_PATH)
                logger.info("Stockfish engine initialized from %s", DEFAULT_ENGINE_PATH)
            except Exception as e:
                logger.warning("Failed to initialize Stockfish: %s", e)
                cls._instance = None
                cls._error = str(e)
        return cls._instance

    @classmethod
    def get_pool(cls) -> Optional[EnginePool]:
        """Lazily build (once) the concurrent engine pool for batch/parallel analysis."""
        if cls._pool is None:
            try:
                cls._pool = EnginePool(DEFAULT_ENGINE_PATH)
                logger.info("Stockfish engine pool initialized (%d instances)", cls._pool.size)
            except Exception as e:
                logger.warning("Failed to initialize Stockfish pool: %s", e)
                cls._pool = None
                cls._error = str(e)
        return cls._pool

    @classmethod
    def get_error(cls) -> Optional[str]:
        return cls._error

    @classmethod
    def is_available(cls) -> bool:
        return cls.get_instance() is not None

    @classmethod
    def shutdown(cls) -> None:
        """Quit every engine process (single instance + pool). Called at app shutdown."""
        if cls._instance is not None:
            try:
                cls._instance.quit()
            except Exception:
                pass
            cls._instance = None
        if cls._pool is not None:
            try:
                cls._pool.quit()
            except Exception:
                pass
            cls._pool = None
