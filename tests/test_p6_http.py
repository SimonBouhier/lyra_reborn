"""P6 porte HTTP : assertions de contenu, pas juste 200 (plan §6 P6 DoD)."""
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app, book
from core.llm import EchoClient


@pytest.fixture
def client():
    book._sessions.clear()
    book._llm_factory = lambda: (EchoClient(), "premières couches")
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
    assert snap.json()["moteur"] == "premières couches"


def test_unknown_session_is_not_created_by_read_or_chat(client):
    before = len(book._sessions)

    read = client.get("/api/session/inconnue")
    chat = client.post(
        "/api/parler",
        json={"texte": "Bonjour", "session": "inconnue"},
    )

    assert read.status_code == 404
    assert chat.status_code == 404
    assert len(book._sessions) == before


def test_unknown_session_does_not_initialize_a_voice_backend(client, monkeypatch):
    calls = []

    def record_call(*, live=False):
        calls.append(live)
        return EchoClient(), "voix-test"

    monkeypatch.setattr(main_module, "make_llm", record_call)

    response = client.post(
        "/api/parler",
        json={"texte": "Bonjour", "session": "inconnue", "voix": True},
    )

    assert response.status_code == 404
    assert calls == []


def test_backend_label_is_isolated_per_session(client, monkeypatch):
    first = client.post("/api/parler", json={"texte": "Premier chemin"}).json()
    first_id = first["session"]

    monkeypatch.setattr(
        main_module,
        "make_llm",
        lambda *, live=False: (EchoClient(model="modele-test"), "modele-test"),
    )
    second = client.post(
        "/api/parler",
        json={"texte": "Seconde voix", "voix": True},
    ).json()

    resumed_first = client.post(
        "/api/parler",
        json={"texte": "Retour au premier", "session": first_id},
    ).json()

    assert second["moteur"] == "modele-test"
    assert resumed_first["moteur"] == "premières couches"
    assert client.get(f"/api/session/{first_id}").json()["moteur"] == "premières couches"
    assert client.get("/api/sante").json()["moteur"] == "configuration par session"


def test_failed_voice_request_does_not_create_an_empty_session(client, monkeypatch):
    def unavailable(*, live=False):
        raise RuntimeError("voix indisponible")

    monkeypatch.setattr(main_module, "make_llm", unavailable)
    before = len(book._sessions)

    response = client.post(
        "/api/parler",
        json={"texte": "Essaie une voix", "voix": True},
    )

    assert response.status_code == 503
    assert len(book._sessions) == before


def test_empty_chat_is_rejected(client):
    r = client.post("/api/parler", json={"texte": "x"})
    # pydantic min_length=1 accepts "x"; blank rejected by session
    r2 = client.post("/api/parler", json={"texte": "   "})
    assert r2.status_code in (400, 422)
