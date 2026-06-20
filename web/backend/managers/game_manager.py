import uuid
from typing import Dict, Optional, List, Any
from src.core.chess_game import ChessGame

class GameManager:
    def __init__(self):
        self.games: Dict[str, Dict[str, Any]] = {}

    def create_game(self) -> str:
        session_id = str(uuid.uuid4())
        self.games[session_id] = {
            "game": ChessGame(),
            "move_evaluations": [],
            "headers": {}
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.games.get(session_id)

    def get_game(self, session_id: str) -> Optional[ChessGame]:
        session = self.get_session(session_id)
        if not session:
            return None
        return session["game"]

    def get_move_evaluations(self, session_id: str) -> List[Dict[str, Any]]:
        session = self.get_session(session_id)
        if not session:
            return []
        return session["move_evaluations"]

    def append_move_evaluation(self, session_id: str, evaluation: Dict[str, Any]) -> None:
        session = self.get_session(session_id)
        if not session:
            return
        session["move_evaluations"].append(evaluation)

    def reset_move_evaluations(self, session_id: str) -> None:
        session = self.get_session(session_id)
        if not session:
            return
        session["move_evaluations"] = []

# Global instance
game_manager = GameManager()
