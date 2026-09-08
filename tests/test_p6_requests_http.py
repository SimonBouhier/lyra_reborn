import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

import app.main as main
from app.journal import SQLiteJournalStore
from app.requests import RequestService
from app.session import SessionBook
from core.llm import EchoClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    store = SQLiteJournalStore(tmp_path / "journal.sqlite3")
    book = SessionBook(storage=store, llm_factory=lambda: (EchoClient(), "premières couches"))
    service = RequestService(book, store, voice_factory=lambda: (EchoClient(), "premières couches"))
    monkeypatch.setattr(main, "book", book)
    monkeypatch.setattr(main, "request_service", service)
    with TestClient(main.app) as client:
        yield client


def test_first_acceptance_can_be_recovered_by_client_id_and_display_is_durable(client):
    payload = {"demande": "envoi-client", "texte": "  Conserve ce texte  ", "voix": False}
    accepted = client.post("/api/demandes", json=payload)
    assert accepted.status_code == 200
    row = accepted.json()
    assert row["statut"] == "en_attente" and row["reponse"] is None
    assert row["texte"] == payload["texte"]
    recovered = client.get("/api/demandes/envoi-client")
    assert recovered.status_code == 200
    assert recovered.json()["session"] == row["session"]
    assert client.post("/api/demandes", json=payload).json() == row
    result = client.post("/api/demandes/envoi-client/executer").json()
    assert result["statut"] == "termine"
    assert result["reponse"]["reponse"].startswith("Tour pris.")
    journal = client.get(f'/api/session/{row["session"]}/journal').json()
    assert journal["demandes"][0]["reponse"] == result["reponse"]
    assert client.post("/api/demandes/envoi-client/executer").json() == result


def test_conflict_and_legacy_bypass_are_explicit(client):
    assert client.post("/api/demandes", json={"demande": "id", "texte": "Bonjour"}).status_code == 200
    assert client.post("/api/demandes", json={"demande": "id", "texte": "Autre"}).status_code == 409
    assert client.post("/api/parler", json={"texte": "Sans identité client"}).status_code == 410
    assert client.get("/api/demandes/inconnue").status_code == 404
    assert client.post("/api/demandes/id/relancer", json={}).status_code == 422


@pytest.mark.parametrize("payload", [
    {"texte": "Sans identité"},
    {"demande": "id", "texte": "Texte", "voix": "false"},
    {"demande": "id", "texte": "Texte", "system": "instruction cachée"},
    {"demande": "id/incorrect", "texte": "Texte"},
])
def test_invalid_intents_are_not_accepted(client, payload):
    assert client.post("/api/demandes", json=payload).status_code == 422
