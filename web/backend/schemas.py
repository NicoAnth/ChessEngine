from pydantic import BaseModel
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
