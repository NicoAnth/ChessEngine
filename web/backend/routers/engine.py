from fastapi import APIRouter
from ..schemas import EngineStatusResponse
from ..config import DEFAULT_ENGINE_PATH
from ..managers.engine_manager import EngineManager

router = APIRouter()

@router.get("/engine/status", response_model=EngineStatusResponse)
def engine_status():
    return {
        "available": EngineManager.is_available(),
        "engine_path": DEFAULT_ENGINE_PATH,
        "error": EngineManager.get_error(),
    }
