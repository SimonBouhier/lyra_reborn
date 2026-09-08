"""Journal P6 : demandes durables, répétitions et tentatives distinctes."""
from concurrent.futures import ThreadPoolExecutor
import json
from threading import Event

import pytest

from app.journal import SQLiteJournalStore, RequestConflict
from app.requests import RequestService
from app.session import SessionBook, SessionBusyError
from app.storage import SessionStorageError
from core.llm import EchoClient, OllamaClient


class Voice:
    model = "factice"

    def __init__(self):
        self.calls = []
        self.fail = False

    def generate(self, prompt, options, response_format=None):
        self.calls.append(prompt)
        if self.fail:
            raise RuntimeError("panne factice")
        return "- Réponse enregistrée : " + prompt.splitlines()[-1]


def runtime(path, voice=None):
    voice = voice or Voice()
    store = SQLiteJournalStore(path)
    book = SessionBook(storage=store,
                       llm_factory=lambda: (voice, voice.model),
                       backend_resolver=lambda label: (voice, label))
    return RequestService(book, store, voice_factory=lambda: (voice, voice.model)), voice


def accept(service, request_id="r-1", text="Bonjour", session=None, voice=False):
    return service.accept(request_id, {"texte": text, "session": session, "voix": voice})


def test_acceptance_is_durable_before_generation_and_replay_finds_first_session(tmp_path):
    service, voice = runtime(tmp_path / "journal.sqlite3")
    accepted = accept(service, text="  Texte exact\nà conserver  ")
    assert accepted["statut"] == "en_attente"
    assert voice.calls == []
    assert accepted["texte"] == "  Texte exact\nà conserver  "
    resumed, _ = runtime(service.store.path, voice)
    assert accept(resumed, text=accepted["texte"])["session"] == accepted["session"]
    assert resumed.get("r-1")["tentatives"] == []


@pytest.mark.parametrize("change", [{"texte": "Autre"}, {"voix": True}, {"session": "autre"}])
def test_identity_cannot_be_reused_for_a_different_intent(tmp_path, change):
    service, _ = runtime(tmp_path / "journal.sqlite3")
    accept(service)
    payload = {"texte": "Bonjour", "session": None, "voix": False, **change}
    with pytest.raises(RequestConflict):
        service.accept("r-1", payload)


def test_success_replay_returns_exact_display_response_without_generation(tmp_path):
    service, voice = runtime(tmp_path / "journal.sqlite3")
    accepted = accept(service)
    result = service.run("r-1")
    assert result["statut"] == "termine"
    assert result["reponse"]["reponse"] == "- Réponse enregistrée : Bonjour"
    resumed, _ = runtime(service.store.path, voice)
    assert resumed.run("r-1")["reponse"] == result["reponse"]
    assert len(voice.calls) == 1
    assert resumed.store.load(accepted["session"])["turns"] == 1
    assert result["tentatives"][0]["execution"]["prompt"] == "Bonjour"


def test_explicit_retry_is_itself_idempotent_after_a_lost_response(tmp_path):
    service, voice = runtime(tmp_path / "journal.sqlite3")
    accept(service)
    voice.fail = True
    assert service.run("r-1")["statut"] == "echoue"
    assert service.run("r-1")["statut"] == "echoue"
    assert len(voice.calls) == 1
    assert service.run("r-1", retry_id="retry-1")["statut"] == "echoue"
    assert service.run("r-1", retry_id="retry-1")["statut"] == "echoue"
    assert len(voice.calls) == 2
    voice.fail = False
    result = service.run("r-1", retry_id="retry-2")
    assert result["statut"] == "termine"
    assert [a["statut"] for a in result["tentatives"]] == ["echoue", "echoue", "termine"]
    assert len(voice.calls) == 3


def test_restart_marks_unfinished_attempt_interrupted_without_reexecuting(tmp_path):
    service, voice = runtime(tmp_path / "journal.sqlite3")
    accept(service)
    service.store.begin("r-1", None)
    resumed, _ = runtime(service.store.path, voice)
    interrupted = resumed.get("r-1")
    assert interrupted["statut"] == "interrompu"
    assert resumed.run("r-1")["statut"] == "interrompu"
    assert voice.calls == []
    assert resumed.run("r-1", retry_id="reprise-1")["statut"] == "termine"


def test_complete_is_atomic_with_session_and_result(tmp_path, monkeypatch):
    service, voice = runtime(tmp_path / "journal.sqlite3")
    row = accept(service)
    before = service.store.load(row["session"])
    write = service.store._write_state

    def fail_after_write(connection, state):
        write(connection, state)
        raise SessionStorageError("échec avant validation du résultat")

    monkeypatch.setattr(service.store, "_write_state", fail_after_write)
    failed = service.run("r-1")
    assert failed["statut"] == "echoue"
    assert failed["reponse"] is None
    assert service.store.load(row["session"]) == before
    assert json.loads(json.dumps(service.book.require(row["session"]).to_state())) == before
    monkeypatch.setattr(service.store, "_write_state", write)
    assert service.run("r-1", retry_id="reprise")["statut"] == "termine"


def test_running_request_is_readable_but_cannot_execute_twice(tmp_path):
    service, voice = runtime(tmp_path / "journal.sqlite3")
    row = accept(service)
    entered, release = Event(), Event()
    generate = voice.generate

    def slow(prompt, options, response_format=None):
        entered.set()
        assert release.wait(10)
        return generate(prompt, options, response_format)

    voice.generate = slow
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(service.run, "r-1")
        try:
            assert entered.wait(10)
            assert service.get("r-1")["statut"] == "en_cours"
            assert service.run("r-1")["statut"] == "en_cours"
            assert accept(service)["statut"] == "en_cours"
            with pytest.raises((SessionBusyError, RequestConflict)):
                accept(service, "r-2", session=row["session"])
            assert accept(service, "autre")["session"] != row["session"]
        finally:
            release.set()
        assert future.result(timeout=10)["statut"] == "termine"
    assert len(voice.calls) == 1


def test_exception_after_commit_does_not_undo_the_durable_result(tmp_path, monkeypatch):
    service, voice = runtime(tmp_path / "journal.sqlite3")
    row = accept(service)
    complete = service.store.complete

    def commit_then_raise(*args):
        complete(*args)
        raise SessionStorageError("accusé de publication perdu après commit")

    monkeypatch.setattr(service.store, "complete", commit_then_raise)
    result = service.run("r-1")
    assert result["statut"] == "termine"
    assert service.store.load(row["session"])["turns"] == 1
    resumed, _ = runtime(service.store.path, voice)
    assert resumed.run("r-1")["reponse"] == result["reponse"]
    assert len(voice.calls) == 1


def test_failed_error_write_is_recovered_without_rerunning_the_model(tmp_path, monkeypatch):
    service, voice = runtime(tmp_path / "journal.sqlite3")
    row = accept(service)
    voice.fail = True
    fail = service.store.fail

    def disk_unavailable(*args, **kwargs):
        raise SessionStorageError("disque facticement indisponible")

    monkeypatch.setattr(service.store, "fail", disk_unavailable)
    with pytest.raises(SessionStorageError):
        service.run("r-1")
    assert service.store.load(row["session"])["turns"] == 0
    monkeypatch.setattr(service.store, "fail", fail)
    # Même processus : l'identité n'est plus réservée, donc l'ancienne
    # tentative peut être déclarée interrompue sans recréer le serveur.
    assert service.get("r-1")["statut"] == "interrompu"
    assert service.run("r-1")["statut"] == "interrompu"
    assert len(voice.calls) == 1


def test_journal_exceeds_control_history_and_stays_scoped(tmp_path):
    service, _ = runtime(tmp_path / "journal.sqlite3", EchoClient())
    sid = None
    for i in range(52):
        row = accept(service, f"r-{i}", f"Texte {i}", sid)
        sid = row["session"]
        assert service.run(f"r-{i}")["statut"] == "termine"
    other = accept(service, "autre", "Autre conversation")
    rows = service.store.history(sid, 0, 100)
    assert len(rows) == 52
    assert rows[0]["texte"] == "Texte 0"
    assert rows[0]["reponse"]["reponse"].startswith("Tour pris.")
    assert len(service.store.load(sid)["cognitive_state"]["history"]) == 50
    assert len(service.store.history(other["session"], 0, 100)) == 1


def test_retry_after_another_turn_is_refused_until_branching_is_defined(tmp_path):
    service, voice = runtime(tmp_path / "journal.sqlite3")
    row = accept(service)
    voice.fail = True
    assert service.run("r-1")["statut"] == "echoue"
    voice.fail = False
    accept(service, "r-2", "La suite", row["session"])
    assert service.run("r-2")["statut"] == "termine"
    with pytest.raises(RequestConflict):
        service.run("r-1", retry_id="tardive")


def test_completed_client_configuration_survives_a_new_runtime(tmp_path, monkeypatch):
    seen = []

    def scripted_generate(self, prompt, options=None, response_format=None):
        seen.append((self.model, self.base_url, self.timeout, self.think))
        return "- Sortie factice ; aucun réseau"

    monkeypatch.setattr(OllamaClient, "generate", scripted_generate)
    first = OllamaClient(model="modele-factice", base_url="http://127.0.0.1:9991", timeout=37, think=True)
    service, _ = runtime(tmp_path / "journal.sqlite3", first)
    row = accept(service)
    assert service.run("r-1")["statut"] == "termine"
    changed = OllamaClient(model="autre", base_url="http://127.0.0.1:9992", timeout=99, think=False)
    resumed, _ = runtime(service.store.path, changed)
    accept(resumed, "r-2", "Suite", row["session"])
    assert resumed.run("r-2")["statut"] == "termine"
    assert seen == [("modele-factice", "http://127.0.0.1:9991", 37, True)] * 2
