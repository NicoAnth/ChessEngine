import logging
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ChessComService:
    BASE_URL = "https://api.chess.com/pub"
    # Chess.com requires a descriptive User-Agent
    HEADERS = {
        "User-Agent": "ChessEngine-App/1.0 (local development; contact: admin@localhost)"
    }

    @staticmethod
    def _map_result(result: str) -> str:
        """
        Map Chess.com result codes to our simplified status: 'win', 'loss', 'draw'.
        Codes: win, checkmated, agreed, repetition, timeout, resigned, stalemate, lose, insufficient, 50move, abandoned, timevsinsufficient
        """
        if not result:
            return "draw"
        
        result = result.lower()
        if result == "win":
            return "win"
        # Everything else is a loss or draw depending on context, BUT the result here is from the perspective of the player.
        # So "checkmated", "resigned", "timeout", "lose", "abandoned" -> loss
        # "agreed", "repetition", "stalemate", "insufficient", "50move", "timevsinsufficient" -> draw
        
        if result in ["checkmated", "timeout", "resigned", "lose", "abandoned"]:
            return "loss"
        
        return "draw"

    @classmethod
    def validate_user(cls, username: str) -> bool:
        """
        Check if a user exists on Chess.com
        """
        try:
            url = f"{cls.BASE_URL}/player/{username}"
            response = requests.get(url, headers=cls.HEADERS, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning("Chess.com validation error: %s", e)
            return False

    @classmethod
    def get_recent_games(cls, username: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch recent games from the user's archives.
        We'll look at the most recent monthly archive first.
        """
        try:
            # 1. Get list of available archives
            archives_url = f"{cls.BASE_URL}/player/{username}/games/archives"
            resp = requests.get(archives_url, headers=cls.HEADERS, timeout=5)
            if resp.status_code != 200:
                return []
            
            data = resp.json()
            archives = data.get("archives", [])
            
            if not archives:
                return []

            # 2. Fetch games from the last archive (most recent month)
            # If not enough games, we could go back, but for simplicity let's stick to the latest month first
            # The archives list is usually chronological.
            latest_archive_url = archives[-1]
            
            games_resp = requests.get(latest_archive_url, headers=cls.HEADERS, timeout=10)
            if games_resp.status_code != 200:
                return []
                
            games_data = games_resp.json()
            games = games_data.get("games", [])
            
            # Sort by end_time descending
            games.sort(key=lambda x: x.get("end_time", 0), reverse=True)
            
            # 3. Process and simplify
            processed_games = []
            for g in games[:limit]:
                white = g.get("white", {})
                black = g.get("black", {})
                
                # Determine user color and opponent
                if white.get("username", "").lower() == username.lower():
                    user_color = "white"
                    opponent = black
                    user_result = cls._map_result(white.get("result"))
                else:
                    user_color = "black"
                    opponent = white
                    user_result = cls._map_result(black.get("result"))
                    
                processed_games.append({
                    "uuid": g.get("uuid", str(g.get("end_time"))), # Fallback ID
                    "source": "chesscom",
                    "url": g.get("url"),
                    "pgn": g.get("pgn"),
                    "time_control": g.get("time_control"),
                    "end_time": g.get("end_time"), # Unix timestamp
                    "rated": g.get("rated", False),
                    "fen": g.get("fen"),
                    "user_color": user_color,
                    "user_result": user_result,
                    "opponent_username": opponent.get("username"),
                    "opponent_rating": opponent.get("rating"),
                })
                
            return processed_games

        except Exception as e:
            logger.warning("Error fetching Chess.com games: %s", e)
            return []
