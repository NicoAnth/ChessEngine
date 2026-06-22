"""In-memory store for batch-analysis jobs.

Each batch holds the per-game summaries; every game is also a normal session in the
game_manager (so the existing review UI can reopen any of them by session_id). Like
game sessions, batches live in RAM and are lost on restart — game summaries attached
to a profile (profile_manager) are the durable record.
"""
import uuid
from typing import Any, Dict, List, Optional


class BatchManager:
    def __init__(self) -> None:
        self.batches: Dict[str, Dict[str, Any]] = {}

    def create(self) -> str:
        batch_id = str(uuid.uuid4())
        self.batches[batch_id] = {"batch_id": batch_id, "status": "running", "games": []}
        return batch_id

    def add_game(self, batch_id: str, summary: Dict[str, Any]) -> None:
        batch = self.batches.get(batch_id)
        if batch is not None:
            batch["games"].append(summary)

    def finish(self, batch_id: str) -> None:
        batch = self.batches.get(batch_id)
        if batch is not None:
            batch["status"] = "done"

    def get(self, batch_id: str) -> Optional[Dict[str, Any]]:
        return self.batches.get(batch_id)


# Global instance
batch_manager = BatchManager()
