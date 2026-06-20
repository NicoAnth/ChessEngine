import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid

from ..config import PROFILE_DIR
from ..schemas import GameRecord, StoredProfile

class ProfileManager:
    def __init__(self, directory: Path = PROFILE_DIR):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def _slugify(self, username: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", username.strip().lower())
        slug = re.sub(r"_+", "_", slug).strip("_")
        return slug or "user"

    def _path_for(self, username: str) -> Path:
        return self.directory / f"{self._slugify(username)}.json"

    def _load_raw(self, username: str) -> Optional[Dict[str, Any]]:
        path = self._path_for(username)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _save_raw(self, username: str, data: Dict[str, Any]) -> None:
        path = self._path_for(username)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def delete_profile(self, username: str) -> bool:
        path = self._path_for(username)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_profiles(self) -> List[Dict[str, Any]]:
        profiles: List[Dict[str, Any]] = []
        for file in sorted(self.directory.glob("*.json")):
            try:
                with file.open("r", encoding="utf-8") as f:
                    raw = json.load(f)
                profiles.append({
                    "username": raw.get("username", file.stem),
                    "chesscom_username": raw.get("chesscom_username"),
                    "lichess_username": raw.get("lichess_username"),
                    "created_at": raw.get("created_at"),
                    "updated_at": raw.get("updated_at"),
                    "total_games": len(raw.get("games", [])),
                })
            except Exception:
                continue
        return profiles

    def create_profile(self, username: str) -> Dict[str, Any]:
        username = (username or "").strip()
        if not username:
            raise ValueError("Username is required")

        existing = self._load_raw(username)
        if existing:
            return {
                "username": existing.get("username", username),
                "created_at": existing.get("created_at"),
                "updated_at": existing.get("updated_at"),
                "total_games": len(existing.get("games", [])),
            }

        now = datetime.utcnow().isoformat()
        raw = StoredProfile(
            username=username, created_at=now, updated_at=now
        ).model_dump(mode="json")
        self._save_raw(username, raw)
        return {
            "username": username,
            "created_at": now,
            "updated_at": now,
            "total_games": 0,
        }

    def update_profile(self, username: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        profile = self._load_raw(username)
        if not profile:
            return None
        
        # Apply updates
        for k, v in updates.items():
            if k not in ["games", "username", "created_at"]: # Protect core fields
                profile[k] = v
        
        profile["updated_at"] = datetime.utcnow().isoformat()
        self._save_raw(username, profile)
        return profile

    def add_imported_game(
        self,
        username: str,
        headers: Dict[str, str],
        move_evaluations: List[Dict[str, Any]],
        white_stats: Dict[str, Any],
        black_stats: Dict[str, Any],
        difficulty: Dict[str, Any],
    ) -> None:
        profile = self._load_raw(username)
        if not profile:
            profile = {
                "username": username,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "games": [],
            }

        white_name = (headers.get("White") or "").strip()
        black_name = (headers.get("Black") or "").strip()
        uname = username.strip().lower()

        if white_name.lower() == uname:
            user_side = "White"
            user_stats = white_stats
        elif black_name.lower() == uname:
            user_side = "Black"
            user_stats = black_stats
        else:
            user_side = "Unknown"
            user_stats = {}

        final_opening = None
        for ev in move_evaluations:
            op = ev.get("opening")
            if op:
                final_opening = op

        game_record = GameRecord(
            id=str(uuid.uuid4()),
            imported_at=datetime.utcnow().isoformat(),
            event=headers.get("Event"),
            site=headers.get("Site"),
            date=headers.get("Date") or headers.get("UTCDate"),
            round=headers.get("Round"),
            result=headers.get("Result"),
            time_control=headers.get("TimeControl"),
            eco=headers.get("ECO") or (final_opening or {}).get("eco"),
            opening_name=(final_opening or {}).get("name"),
            white=headers.get("White"),
            black=headers.get("Black"),
            white_elo=headers.get("WhiteElo"),
            black_elo=headers.get("BlackElo"),
            moves=len(move_evaluations),
            user_side=user_side,
            user_accuracy=user_stats.get("accuracy"),
            user_precision=user_stats.get("precision"),
            user_best_move_percentage=user_stats.get("best_move_percentage"),
            user_total_moves=user_stats.get("total_moves"),
            difficulty=difficulty,
        ).model_dump(mode="json")

        profile.setdefault("games", []).append(game_record)
        profile["updated_at"] = datetime.utcnow().isoformat()
        self._save_raw(username, profile)

    def format_time_control(self, tc_raw: Optional[str]) -> str:
        if not tc_raw or tc_raw == "?" or tc_raw == "Unknown":
            return "Inconnu"
        
        try:
            parts = tc_raw.split("+")
            seconds = int(parts[0])
            increment = 0
            if len(parts) > 1:
                increment = int(parts[1])
            
            minutes = seconds // 60
            
            # Format Bullet/Blitz standard
            if increment > 0:
                return f"{minutes}+{increment}"
            
            if minutes == 0:
                return f"{seconds}s"
                
            return f"{minutes} min"

        except ValueError:
            return tc_raw

    def get_profile_with_stats(self, username: str) -> Optional[Dict[str, Any]]:
        profile = self._load_raw(username)
        if not profile:
            return None

        games = profile.get("games", [])

        def _avg(values: List[float]) -> float:
            return round(sum(values) / len(values), 1) if values else 0.0

        known_games = [g for g in games if g.get("user_side") in ("White", "Black")]
        white_games = [g for g in known_games if g.get("user_side") == "White"]
        black_games = [g for g in known_games if g.get("user_side") == "Black"]

        all_acc = [float(g["user_accuracy"]) for g in known_games if g.get("user_accuracy") is not None]
        white_acc = [float(g["user_accuracy"]) for g in white_games if g.get("user_accuracy") is not None]
        black_acc = [float(g["user_accuracy"]) for g in black_games if g.get("user_accuracy") is not None]

        by_time: Dict[str, Dict[str, Any]] = {}
        for g in known_games:
            tc_raw = g.get("time_control")
            tc_display = self.format_time_control(tc_raw)
            
            row = by_time.setdefault(tc_display, {"time_control": tc_display, "games": 0, "accuracy_values": []})
            row["games"] += 1
            if g.get("user_accuracy") is not None:
                row["accuracy_values"].append(float(g["user_accuracy"]))

        by_time_control = []

        for row in by_time.values():
            by_time_control.append({
                "time_control": row["time_control"],
                "games": row["games"],
                "accuracy": _avg(row["accuracy_values"]),
            })
        by_time_control.sort(key=lambda x: x["games"], reverse=True)

        opening_counts: Dict[str, Dict[str, Any]] = {}
        for g in games:
            eco = g.get("eco") or "Unknown"
            opening_name = g.get("opening_name") or "Unknown opening"
            key = f"{eco}|{opening_name}"
            row = opening_counts.setdefault(key, {"eco": eco, "name": opening_name, "games": 0})
            row["games"] += 1

        top_openings = sorted(opening_counts.values(), key=lambda x: x["games"], reverse=True)[:5]
        
        # Prepare history with formatted time controls
        history = []
        for g in sorted(games, key=lambda x: x.get("imported_at", ""), reverse=True):
            g_copy = g.copy()
            g_copy["time_control"] = self.format_time_control(g.get("time_control"))
            history.append(g_copy)

        return {
            "profile": {
                "username": profile.get("username"),
                "chesscom_username": profile.get("chesscom_username"),
                "lichess_username": profile.get("lichess_username"),
                "created_at": profile.get("created_at"),
                "updated_at": profile.get("updated_at"),
                "total_games": len(games),
            },
            "stats": {
                "overall_accuracy": _avg(all_acc),
                "accuracy_white": _avg(white_acc),
                "accuracy_black": _avg(black_acc),
                "games_as_white": len(white_games),
                "games_as_black": len(black_games),
                "by_time_control": by_time_control,
                "top_openings": top_openings,
            },
            "history": history,
        }

profile_manager = ProfileManager()
