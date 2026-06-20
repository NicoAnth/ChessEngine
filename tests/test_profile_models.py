"""M-07 — schéma de profil persisté modélisé en Pydantic (validation à l'écriture)."""
import json

from web.backend.schemas import GameRecord, StoredProfile
from web.backend.managers.profile_manager import ProfileManager


def test_game_record_defaults_and_validation():
    r = GameRecord(id="abc", moves=12, user_side="White")
    d = r.model_dump(mode="json")
    assert d["id"] == "abc"
    assert d["moves"] == 12
    assert d["user_accuracy"] is None
    assert d["difficulty"] is None


def test_stored_profile_preserves_unknown_keys():
    # Files written by older code may carry extra keys — they must survive a round-trip.
    p = StoredProfile.model_validate({"username": "bob", "legacy_blob": {"x": 1}})
    assert p.username == "bob"
    assert p.model_dump()["legacy_blob"] == {"x": 1}


def test_add_imported_game_persists_a_valid_record(tmp_path):
    pm = ProfileManager(directory=tmp_path)
    pm.create_profile("bob")
    headers = {"White": "bob", "Black": "alice", "Result": "1-0",
               "ECO": "C60", "TimeControl": "600"}
    move_evals = [{"side": "White"}, {"side": "Black"}, {"side": "White"}]
    white_stats = {"accuracy": 95.0, "precision": 90.0,
                   "best_move_percentage": 50.0, "total_moves": 2}
    pm.add_imported_game("bob", headers, move_evals, white_stats, {},
                         {"overall": 5.0, "white": 6.0, "black": 4.0})

    raw = json.loads((tmp_path / "bob.json").read_text(encoding="utf-8"))
    assert len(raw["games"]) == 1
    g = raw["games"][0]
    GameRecord.model_validate(g)  # the persisted record conforms to the model
    assert g["white"] == "bob"
    assert g["user_side"] == "White"
    assert g["user_accuracy"] == 95.0
    assert g["eco"] == "C60"
    assert g["moves"] == 3
