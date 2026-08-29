"""P6 porte HTTP : assertions de contenu, pas juste 200 (plan §6 P6 DoD)."""
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from app.main import app, book
from core.llm import EchoClient


@pytest.fixture
def client():
    book._sessions.clear()
    book._llm_factory = EchoClient
    return TestClient(app)


def test_health_and_page(client):
    h = client.get("/api/sante")
    assert h.status_code == 200
    assert h.json()["ok"] is True
    page = client.get("/")
    assert page.status_code == 200
    assert "Parler à Lyra" in page.text
    assert "chemin" in page.text.lower() or "Demander une voix" in page.text


def test_chat_returns_knobs_and_nonempty_graph(client):
    r = client.post("/api/parler", json={"texte": "Explique la récursivité et les fractales"})
    assert r.status_code == 200
    body = r.json()
    assert body["reponse"]
    assert "chemin" in body["reponse"].lower()
    assert "rho" in body["boutons"]
    assert body["graphe"]["nodes"] >= 1
    assert body["concepts"]
    sid = body["session"]
    snap = client.get(f"/api/session/{sid}")
    assert snap.status_code == 200
    assert snap.json()["tours"] == 1


def test_empty_chat_is_rejected(client):
    r = client.post("/api/parler", json={"texte": "x"})
    # pydantic min_length=1 accepts "x"; blank rejected by session
    r2 = client.post("/api/parler", json={"texte": "   "})
    assert r2.status_code in (400, 422)
