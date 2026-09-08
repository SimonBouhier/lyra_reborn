"""P6 A01 : exclusion par session sur tout le cycle HTTP, sans modèle réel.

Les rendez-vous par Event rendent le chevauchement explicite, sans sommeil
arbitraire. Les seuls fichiers de données sont les SQLite de tmp_path.
"""
from concurrent.futures import ThreadPoolExecutor
import json
from threading import Event

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

import app.main as main_module
from app.session import SessionBook
from app.storage import SQLiteSessionStore, SessionStorageError


class ScriptedClient:
    model = "concurrence-factice"

    def generate(self, prompt, options, response_format=None):
        text = prompt.splitlines()[-1]
        if text == "B_FAIL":
            raise RuntimeError("échec factice de génération")
        return f"- REPONSE_{text}"


class Rendezvous:
    def __init__(self):
        self.entered = Event()
        self.release = Event()

    def pause(self):
        self.entered.set()
        if not self.release.wait(10):
            raise AssertionError("rendez-vous de test expiré")


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    store = SQLiteSessionStore(tmp_path / "sessions.sqlite3")
    book = SessionBook(
        llm_factory=lambda: (ScriptedClient(), ScriptedClient.model),
        backend_resolver=lambda label: (ScriptedClient(), label),
        storage=store,
    )
    monkeypatch.setattr(main_module, "book", book)
    with TestClient(main_module.app) as client:
        yield client, book, store


def post_in_other_thread(session, text):
    # Un client distinct par thread, comme deux onglets du navigateur.
    with TestClient(main_module.app) as client:
        return client.post("/api/parler", json={"session": session, "texte": text})


def outputs(state):
    return [entry["output"] for entry in state["cognitive_state"]["history"]]


def serialized_state(conv):
    # SQLite conserve du JSON : les tuples de l'écologie deviennent des listes.
    # Comparer tous les champs dans cette même représentation, sans les exclure.
    return json.loads(json.dumps(conv.to_state(), allow_nan=False))


@pytest.mark.parametrize("phase", ["restore", "snapshot", "generate", "save", "rollback"])
def test_failure_cannot_erase_an_accepted_turn_at_any_phase(runtime, monkeypatch, phase):
    client, book, store = runtime
    initial = client.post("/api/parler", json={"texte": "A_CONSERVER"})
    assert initial.status_code == 200
    assert initial.json()["reponse"] == "- REPONSE_A_CONSERVER"
    sid = initial.json()["session"]
    before = store.load(sid)
    rendezvous = Rendezvous()

    if phase == "restore":
        book._sessions.clear()
        resolve = book._backend_resolver

        def slow_restore(label):
            if not rendezvous.entered.is_set():
                rendezvous.pause()
            return resolve(label)

        monkeypatch.setattr(book, "_backend_resolver", slow_restore)
    elif phase == "snapshot":
        conv = book.require(sid)
        to_state = conv.to_state

        def slow_snapshot():
            if not rendezvous.entered.is_set():
                rendezvous.pause()
            return to_state()

        monkeypatch.setattr(conv, "to_state", slow_snapshot)
    elif phase == "generate":
        llm = book.require(sid).llm
        generate = llm.generate

        def slow_generate(prompt, options, response_format=None):
            if prompt.endswith("B_FAIL"):
                rendezvous.pause()
            return generate(prompt, options, response_format)

        monkeypatch.setattr(llm, "generate", slow_generate)
    elif phase == "save":
        save = store.save

        def failed_save(state):
            if state["id"] == sid:
                rendezvous.pause()
                raise SessionStorageError("échec factice de sauvegarde")
            save(state)

        monkeypatch.setattr(store, "save", failed_save)
    else:
        rollback = book.rollback

        def slow_rollback(session_id, previous_state):
            rendezvous.pause()
            rollback(session_id, previous_state)

        monkeypatch.setattr(book, "rollback", slow_rollback)

    # B échoue après avoir commencé ; C doit être refusé avant toute mutation.
    failed_text = "B_SAVE_FAIL" if phase == "save" else "B_FAIL"
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(post_in_other_thread, sid, failed_text)
        try:
            assert rendezvous.entered.wait(10), f"phase {phase} non atteinte"
            overlap = client.post(
                "/api/parler", json={"session": sid, "texte": "C_CHEVAUCHEMENT"}
            )
            assert overlap.status_code == 409
            assert "occupée" in overlap.json()["detail"]
            # Une lecture HTTP ne doit pas exposer l'état privé avant commit.
            assert client.get(f"/api/session/{sid}").status_code == 409
            # Le registre peut continuer à montrer le dernier état durable.
            rows = client.get("/api/sessions").json()["sessions"]
            assert next(row for row in rows if row["id"] == sid)["tours"] == 1
            # L'exclusion doit être locale à la conversation, pas au serveur.
            other = client.post("/api/parler", json={"texte": "AUTRE_CONVERSATION"})
            assert other.status_code == 200
            assert other.json()["session"] != sid
        finally:
            rendezvous.release.set()
        failed = future.result(timeout=10)

    assert failed.status_code == (503 if phase == "save" else 502)
    assert store.load(sid) == before
    assert serialized_state(book.require(sid)) == before
    if phase == "save":
        monkeypatch.setattr(store, "save", save)

    # Le rollback a remplacé l'objet : le prochain accès doit retrouver celui-ci.
    after = client.post("/api/parler", json={"session": sid, "texte": "D_SUIVANT"})
    assert after.status_code == 200
    durable = store.load(sid)
    assert durable["turns"] == 2
    assert outputs(durable) == ["- REPONSE_A_CONSERVER", "- REPONSE_D_SUIVANT"]
    restarted = SessionBook(
        storage=SQLiteSessionStore(store.path),
        backend_resolver=lambda label: (ScriptedClient(), label),
    )
    assert serialized_state(restarted.require(sid)) == durable


def test_success_remains_exclusive_until_persistence_finishes(runtime, monkeypatch):
    client, book, store = runtime
    initial = client.post("/api/parler", json={"texte": "INITIAL"})
    assert initial.status_code == 200
    sid = initial.json()["session"]
    rendezvous = Rendezvous()
    save = store.save

    def slow_save(state):
        if state["id"] == sid and state["turns"] == 2:
            rendezvous.pause()
        save(state)

    monkeypatch.setattr(store, "save", slow_save)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(post_in_other_thread, sid, "A_OK")
        try:
            assert rendezvous.entered.wait(10)
            rejected = client.post(
                "/api/parler", json={"session": sid, "texte": "B_REJETE"}
            )
            assert rejected.status_code == 409
            assert client.get(f"/api/session/{sid}").status_code == 409
        finally:
            rendezvous.release.set()
        accepted = future.result(timeout=10)
    assert accepted.status_code == 200
    assert accepted.json()["reponse"] == "- REPONSE_A_OK"
    assert client.get(f"/api/session/{sid}").json()["tours"] == 2
    following = client.post("/api/parler", json={"session": sid, "texte": "C_OK"})
    assert following.status_code == 200
    assert outputs(store.load(sid)) == [
        "- REPONSE_INITIAL", "- REPONSE_A_OK", "- REPONSE_C_OK"
    ]


def test_first_turn_is_protected_before_its_session_is_published(runtime, monkeypatch):
    client, book, store = runtime
    rendezvous = Rendezvous()
    save = store.save
    pending_id = []

    def slow_first_save(state):
        pending_id.append(state["id"])
        rendezvous.pause()
        save(state)

    monkeypatch.setattr(store, "save", slow_first_save)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(post_in_other_thread, None, "PREMIER")
        try:
            assert rendezvous.entered.wait(10)
            sid = pending_id[0]
            assert client.get(f"/api/session/{sid}").status_code == 409
            assert client.post(
                "/api/parler", json={"session": sid, "texte": "INTRUSION"}
            ).status_code == 409
            assert client.get("/api/sessions").json()["sessions"] == []
        finally:
            rendezvous.release.set()
        accepted = future.result(timeout=10)
    assert accepted.status_code == 200
    assert outputs(store.load(sid)) == ["- REPONSE_PREMIER"]


def test_failed_rollback_discards_mutated_object_before_later_restore(runtime, monkeypatch):
    client, book, store = runtime
    initial = client.post("/api/parler", json={"texte": "A_CONSERVER"})
    assert initial.status_code == 200
    sid = initial.json()["session"]
    before = store.load(sid)
    save = store.save
    resolve = book._backend_resolver

    def fail_save(state):
        raise SessionStorageError("sauvegarde indisponible")

    def fail_restore(label):
        raise RuntimeError("moteur indisponible pendant le rollback")

    monkeypatch.setattr(store, "save", fail_save)
    monkeypatch.setattr(book, "_backend_resolver", fail_restore)
    failed = client.post("/api/parler", json={"session": sid, "texte": "B_NON_DURABLE"})
    assert failed.status_code == 503
    assert "état précédent" in failed.json()["detail"]
    assert sid not in book._sessions
    assert store.load(sid) == before
    # L'accès est libéré mais la restauration reste indisponible, pas « occupée ».
    assert client.get(f"/api/session/{sid}").status_code == 503

    monkeypatch.setattr(store, "save", save)
    monkeypatch.setattr(book, "_backend_resolver", resolve)
    restored = client.get(f"/api/session/{sid}")
    assert restored.status_code == 200
    assert restored.json()["tours"] == 1
    following = client.post("/api/parler", json={"session": sid, "texte": "C_OK"})
    assert following.status_code == 200
    assert outputs(store.load(sid)) == ["- REPONSE_A_CONSERVER", "- REPONSE_C_OK"]
