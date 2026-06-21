"""Smoke tests de l'API FastAPI (sans dépendre de Stockfish)."""
from fastapi.testclient import TestClient

from web.backend.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_engine_status_shape():
    # Renvoie 200 que Stockfish soit présent ou non.
    r = client.get("/engine/status")
    assert r.status_code == 200
    body = r.json()
    assert "available" in body and isinstance(body["available"], bool)


def test_create_and_list_profile(tmp_path, monkeypatch):
    # Rediriger la persistance vers un dossier temporaire (pas de pollution).
    from web.backend.managers import profile_manager as pm
    monkeypatch.setattr(pm.profile_manager, "directory", tmp_path)

    r = client.post("/profiles", json={"username": "pytest_user"})
    assert r.status_code == 200
    assert r.json()["username"] == "pytest_user"

    r2 = client.get("/profiles")
    assert r2.status_code == 200
    assert any(p["username"] == "pytest_user" for p in r2.json())
