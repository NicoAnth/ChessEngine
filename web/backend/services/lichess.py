import logging
import requests
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class LichessService:
    BASE_URL = "https://lichess.org/api"
    # Lichess requires a descriptive User-Agent
    HEADERS = {
        "User-Agent": "ChessEngine-App/1.0 (local development)"
    }

    @classmethod
    def validate_user(cls, username: str) -> bool:
        """
        Check if a user exists on Lichess
        """
        try:
            url = f"{cls.BASE_URL}/user/{username}"
            response = requests.get(url, headers=cls.HEADERS, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning("Error checking Lichess user: %s", e)
            return False

    @classmethod
    def get_recent_games(cls, username: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch recent games for a Lichess user.
        Excludes ongoing games.
        """
        try:
            url = f"{cls.BASE_URL}/games/user/{username}"
            request_headers = {
                **cls.HEADERS,
                "Accept": "application/x-ndjson",
            }
            params = {
                "max": limit,
                "moves": "true",
                "tags": "true",
                "opening": "true",
                "clocks": "true",
                "evals": "false"
            }
            # Lichess returns NDJSON (newline-delimited JSON)
            # We read full text to let requests handle decompression reliably.
            response = requests.get(url, headers=request_headers, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.warning("Lichess API error: %s", response.status_code)
                return []

            games = []
            # Parse NDJSON line by line
            for line_str in response.text.splitlines():
                if not line_str.strip():
                    continue
                try:
                    game_data = json.loads(line_str)
                    formatted_game = cls._format_game(username, game_data)
                    if formatted_game:
                        games.append(formatted_game)
                except Exception as parse_err:
                    logger.warning("Error parsing game line: %s", parse_err)
                    continue
                        
            return games
        except Exception as e:
            logger.warning("Error fetching Lichess games: %s", e)
            return []

    @classmethod
    def _format_game(cls, username: str, game: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Map Lichess raw data to our frontend simplified model
        """
        try:
            # Check user/players existence
            players = game.get("players", {})
            white = players.get("white", {})
            black = players.get("black", {})
            
            white_user = white.get("user", {}) if white.get("user") else {}
            black_user = black.get("user", {}) if black.get("user") else {}

            white_user_id = white_user.get("id", "").lower()
            black_user_id = black_user.get("id", "").lower()
            white_user_name = white_user.get("name", "").lower()
            black_user_name = black_user.get("name", "").lower()
            
            target_user = username.lower()
            
            user_color = "unknown"
            opponent_info = {}

            if white_user_id == target_user or white_user_name == target_user:
                user_color = "white"
                opponent_info = black
            elif black_user_id == target_user or black_user_name == target_user:
                user_color = "black"
                opponent_info = white
            else:
                white_id_from_game = game.get("players", {}).get("white", {}).get("userId", "").lower()
                black_id_from_game = game.get("players", {}).get("black", {}).get("userId", "").lower()
                if white_id_from_game == target_user:
                    user_color = "white"
                    opponent_info = black
                elif black_id_from_game == target_user:
                    user_color = "black"
                    opponent_info = white
                else:
                    return None

            opponent_user = opponent_info.get("user", {})
            opponent_username = opponent_user.get("name", "Anonymous")
            opponent_rating = opponent_info.get("rating", 0)

            # Result
            winner = game.get("winner") # 'white' or 'black'
            status = game.get("status") # 'mate', 'resign', 'draw', etc.
            
            if status == "draw" or status == "stalemate":
                user_result = "draw"
            elif winner == user_color:
                user_result = "win"
            elif winner:
                user_result = "loss"
            else:
                user_result = "aborted"

            # Time control
            clock = game.get("clock", {})
            initial = int(clock.get("initial", 0) or 0)
            increment = int(clock.get("increment", 0) or 0)
            if initial > 0 or increment > 0:
                time_control = f"{initial}+{increment}"
            else:
                time_control = game.get("speed", "unknown")

            # Check if fen is available, otherwise empty
            fen = game.get("fen", "")

            pgn = game.get("pgn") or cls._build_pgn(game)

            return {
                "uuid": game.get("id", ""),
                "source": "lichess",
                "url": f"https://lichess.org/{game.get('id', '')}",
                "pgn": pgn,
                "time_control": time_control,
                "end_time": (game.get("lastMoveAt", 0) // 1000), 
                "rated": game.get("rated", False),
                "fen": fen,
                "user_color": user_color,
                "user_result": user_result,
                "opponent_username": opponent_username,
                "opponent_rating": opponent_rating
            }
        except Exception as e:
            logger.warning("Format error: %s", e)
            return None

    @classmethod
    def _build_pgn(cls, game: Dict[str, Any]) -> str:
        game_id = game.get("id", "")
        site = f"https://lichess.org/{game_id}" if game_id else "https://lichess.org"

        players = game.get("players", {})
        white_user = players.get("white", {}).get("user", {})
        black_user = players.get("black", {}).get("user", {})

        white_name = white_user.get("name", "White")
        black_name = black_user.get("name", "Black")

        winner = game.get("winner")
        status = game.get("status")
        if winner == "white":
            result = "1-0"
        elif winner == "black":
            result = "0-1"
        elif status in ("draw", "stalemate"):
            result = "1/2-1/2"
        else:
            result = "*"

        last_move_at = int(game.get("lastMoveAt", 0) or 0)
        if last_move_at > 0:
            date_value = datetime.utcfromtimestamp(last_move_at / 1000).strftime("%Y.%m.%d")
        else:
            date_value = "????.??.??"

        clock = game.get("clock", {})
        initial = int(clock.get("initial", 0) or 0)
        increment = int(clock.get("increment", 0) or 0)
        time_control = f"{initial}+{increment}" if (initial > 0 or increment > 0) else "-"

        headers = [
            f"[Event \"Lichess Game\"]",
            f"[Site \"{site}\"]",
            f"[Date \"{date_value}\"]",
            f"[Round \"-\"]",
            f"[White \"{white_name}\"]",
            f"[Black \"{black_name}\"]",
            f"[Result \"{result}\"]",
            f"[TimeControl \"{time_control}\"]",
        ]

        opening = game.get("opening", {})
        eco = opening.get("eco")
        opening_name = opening.get("name")
        if eco:
            headers.append(f"[ECO \"{eco}\"]")
        if opening_name:
            headers.append(f"[Opening \"{opening_name}\"]")

        moves = (game.get("moves") or "").strip()
        if moves:
            return "\n".join(headers) + f"\n\n{moves} {result}\n"
        return "\n".join(headers) + f"\n\n{result}\n"
