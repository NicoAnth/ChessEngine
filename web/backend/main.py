from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import logging
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# App and config
# Use absolute imports relative to this file's location to support execution from backend dir
try:
    from .config import PROJECT_ROOT
    from .managers.engine_manager import EngineManager
    from .routers import game, profiles, engine
except ImportError:
    # If run directly as script not module
    from config import PROJECT_ROOT
    from managers.engine_manager import EngineManager
    from routers import game, profiles, engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: pre-initialize the Stockfish engine.
    EngineManager.get_instance()
    yield
    # (no shutdown work required)


app = FastAPI(title="ChessEngine Web API", lifespan=lifespan)

# Configure CORS — origines explicites (surchargeables via CORS_ORIGINS, separees
# par des virgules). Le combo '*' + credentials est interdit par la spec CORS et
# inutile ici (l'API n'utilise pas de cookies) — cf S-04.
ALLOWED_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(game.router)
app.include_router(profiles.router)
app.include_router(engine.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "ChessEngine API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
