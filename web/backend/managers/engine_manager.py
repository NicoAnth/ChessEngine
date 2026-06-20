from typing import Optional
from src.engine.engine_manager import EngineInstance
from ..config import DEFAULT_ENGINE_PATH

class EngineManager:
    _instance: Optional[EngineInstance] = None
    _error: Optional[str] = None

    @classmethod
    def get_instance(cls) -> Optional[EngineInstance]:
        if cls._instance is None:
            try:
                cls._instance = EngineInstance(DEFAULT_ENGINE_PATH)
                print(f"Stockfish engine initialized from {DEFAULT_ENGINE_PATH}")
            except Exception as e:
                print(f"Failed to initialize Stockfish: {e}")
                cls._instance = None
                cls._error = str(e)
        return cls._instance

    @classmethod
    def get_error(cls) -> Optional[str]:
        return cls._error

    @classmethod
    def is_available(cls) -> bool:
        return cls.get_instance() is not None
