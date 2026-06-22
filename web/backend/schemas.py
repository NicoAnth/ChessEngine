from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional, List, Any

class GameResponse(BaseModel):
    session_id: str
    fen: str
    turn: str
    is_game_over: bool


class MoveRequest(BaseModel):
    session_id: str
    uci: str


class MoveResponse(BaseModel):
    success: bool
    fen: str
    is_check: bool
    is_checkmate: bool
    message: Optional[str] = None
    played_uci: Optional[str] = None


class ImportPgnRequest(BaseModel):
    session_id: str
    pgn: str
    profile_username: Optional[str] = None


class ImportPgnResponse(BaseModel):
    success: bool
    fen: str
    turn: str
    is_game_over: bool
    imported_moves: int
    headers: Dict[str, str] = {}
    message: Optional[str] = None


class BatchImportRequest(BaseModel):
    """Analyse many games at once. `pgn` is a (possibly multi-game) PGN blob and/or
    `pgns` a list of PGN strings (e.g. one per game from a Chess.com/Lichess fetch).
    Both are flattened into a single list of games."""
    pgn: Optional[str] = None
    pgns: Optional[List[str]] = None
    profile_username: Optional[str] = None


class AnalysisResponse(BaseModel):
    score: str
    best_move: str
    depth: int


class EngineStatusResponse(BaseModel):
    available: bool
    engine_path: str
    error: Optional[str] = None


class CreateProfileRequest(BaseModel):
    username: str


class ProfileSummary(BaseModel):
    username: str
    chesscom_username: Optional[str] = None
    lichess_username: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    total_games: int


class ProfileDetailsResponse(BaseModel):
    profile: Dict[str, Any]
    stats: Dict[str, Any]
    history: List[Dict[str, Any]]


class LinkChessComRequest(BaseModel):
    chesscom_username: str


class LinkLichessRequest(BaseModel):
    lichess_username: str


class ExternalGame(BaseModel):
    uuid: str
    source: str  # 'chesscom' | 'lichess'
    url: Optional[str] = None
    pgn: Optional[str] = None
    time_control: Optional[str] = None
    end_time: int
    rated: bool
    fen: Optional[str] = None
    user_color: str
    user_result: str
    opponent_username: str
    opponent_rating: Optional[int] = None

# Deprecated alias for backward compatibility if frontend uses it (though we should update frontend too)
ChessComGame = ExternalGame


# ── Persisted profile schema — source of truth for user_profiles/web/<slug>.json ──

class GameRecord(BaseModel):
    """One imported, analyzed game stored inside a profile."""
    model_config = ConfigDict(extra="allow")  # keep any unknown keys on round-trip

    id: str
    imported_at: Optional[str] = None
    event: Optional[str] = None
    site: Optional[str] = None
    date: Optional[str] = None
    round: Optional[str] = None
    result: Optional[str] = None
    time_control: Optional[str] = None
    eco: Optional[str] = None
    opening_name: Optional[str] = None
    white: Optional[str] = None
    black: Optional[str] = None
    white_elo: Optional[str] = None
    black_elo: Optional[str] = None
    moves: int = 0
    user_side: str = "Unknown"
    user_accuracy: Optional[float] = None
    user_precision: Optional[float] = None
    user_best_move_percentage: Optional[float] = None
    user_total_moves: Optional[int] = None
    difficulty: Optional[Dict[str, Any]] = None


class StoredProfile(BaseModel):
    """A user profile as persisted to disk (web side)."""
    model_config = ConfigDict(extra="allow")  # preserve any extra keys already on disk

    username: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    chesscom_username: Optional[str] = None
    lichess_username: Optional[str] = None
    games: List[GameRecord] = Field(default_factory=list)
