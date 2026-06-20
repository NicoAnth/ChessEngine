from fastapi import APIRouter, HTTPException
from typing import List, Dict

from ..schemas import (
    ProfileSummary, CreateProfileRequest, ProfileDetailsResponse,
    LinkChessComRequest, LinkLichessRequest, ExternalGame
)
from ..managers.profile_manager import profile_manager
from ..services.chesscom import ChessComService
from ..services.lichess import LichessService

router = APIRouter()

@router.get("/profiles", response_model=List[ProfileSummary])
def list_profiles():
    return profile_manager.list_profiles()

@router.post("/profiles", response_model=ProfileSummary)
def create_profile(request: CreateProfileRequest):
    try:
        return profile_manager.create_profile(request.username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/profiles/{username}")
def delete_profile(username: str):
    if profile_manager.delete_profile(username):
        return {"message": f"Profile '{username}' deleted"}
    raise HTTPException(status_code=404, detail="Profile not found")

@router.get("/profiles/{username}", response_model=ProfileDetailsResponse)
def get_profile(username: str):
    data = profile_manager.get_profile_with_stats(username)
    if not data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return data

@router.put("/profiles/{username}/link/chesscom", response_model=Dict[str, str])
def link_chesscom_profile(username: str, request: LinkChessComRequest):
    # Verify profile exists
    profile = profile_manager.get_profile_with_stats(username)
    if not profile:
        raise HTTPException(status_code=404, detail="Local profile not found")

    # Verify Chess.com user exists
    if not ChessComService.validate_user(request.chesscom_username):
        raise HTTPException(status_code=400, detail=f"Chess.com user '{request.chesscom_username}' not found")

    # Save link
    profile_manager.update_profile(username, {"chesscom_username": request.chesscom_username})
    return {"message": f"Successfully linked Chess.com user '{request.chesscom_username}'"}

@router.get("/profiles/{username}/chesscom/games", response_model=List[ExternalGame])
def get_chesscom_games(username: str, limit: int = 50):
    profile_data = profile_manager.get_profile_with_stats(username)
    if not profile_data:
        raise HTTPException(status_code=404, detail="Local profile not found")
        
    chesscom_user = profile_data["profile"].get("chesscom_username")
    if not chesscom_user:
        raise HTTPException(status_code=400, detail="Profile is not linked to Chess.com")

    games = ChessComService.get_recent_games(chesscom_user, limit=limit)
    return games

@router.put("/profiles/{username}/link/lichess", response_model=Dict[str, str])
def link_lichess_profile(username: str, request: LinkLichessRequest):
    # Verify profile exists
    profile = profile_manager.get_profile_with_stats(username)
    if not profile:
        raise HTTPException(status_code=404, detail="Local profile not found")

    # Verify Lichess user exists
    if not LichessService.validate_user(request.lichess_username):
        raise HTTPException(status_code=400, detail=f"Lichess user '{request.lichess_username}' not found")

    # Save link
    profile_manager.update_profile(username, {"lichess_username": request.lichess_username})
    return {"message": f"Successfully linked Lichess user '{request.lichess_username}'"}

@router.get("/profiles/{username}/lichess/games", response_model=List[ExternalGame])
def get_lichess_games(username: str, limit: int = 50):
    profile_data = profile_manager.get_profile_with_stats(username)
    if not profile_data:
        raise HTTPException(status_code=404, detail="Local profile not found")
        
    lichess_user = profile_data["profile"].get("lichess_username")
    if not lichess_user:
        raise HTTPException(status_code=400, detail="Profile is not linked to Lichess")

    games = LichessService.get_recent_games(lichess_user, limit=limit)
    return games
