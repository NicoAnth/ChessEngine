from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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

@app.get("/api/health")
def health():
    return {"status": "ok", "message": "ChessEngine API is running"}


# ── Serve the built frontend (mono-process: one server for API + UI) ──
# Registered AFTER the routers so it never shadows /game, /profiles, /engine, /docs.
# A single catch-all serves real build files (assets, images) and otherwise falls
# back to index.html so the SPA can handle the route. No-op until the frontend is
# built (web/frontend/dist), so dev / CI without a build are unaffected.
_DIST = PROJECT_ROOT / "web" / "frontend" / "dist"
if _DIST.exists():
    _DIST_ROOT = str(_DIST.resolve())

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        candidate = (_DIST / full_path).resolve()
        if full_path and str(candidate).startswith(_DIST_ROOT) and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_DIST / "index.html")


if __name__ == "__main__":
    import uvicorn
    # Bind to localhost by default: the API is unauthenticated (single-user,
    # local use). Override HOST only if you knowingly expose it AND add auth.
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=8000)
