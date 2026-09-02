import json

import pytest

from app.session import LyraConversation, SessionBook, SessionStateError
from app.storage import SQLiteSessionStore, SessionStorageError
from core.llm import EchoClient


def _backend(label: str):
    model = "echo" if label == "premières couches" else label
    return EchoClient(model=model), label


def test_conversation_state_round_trip_preserves_the_live_control_path():
    conv = LyraConversation(
        llm=EchoClient(),
        refractory_ms=0,
        backend_label="premières couches",
    )
    conv.turn("Explique la récursivité et les fractales")
    conv.loop.controller.pressure_i = 0.073
    conv.turn("Relie maintenant récursivité et mémoire")

    state = conv.to_state()
    restored = LyraConversation.from_state(state, backend=_backend(state["backend_label"]))

    assert restored.to_state() == state
    assert restored.navigator.graph is restored.graph
    assert restored.navigator.memento is restored.memento

    restored.turn("Ajoute une troisième idée au graphe")
    assert restored.turns == 3
    assert len(restored.memento) == 3


def test_sqlite_store_survives_a_new_session_book(tmp_path):
    store = SQLiteSessionStore(tmp_path / "sessions.sqlite3")
    first = SessionBook(
        llm_factory=lambda: _backend("premières couches"),
        backend_resolver=_backend,
        storage=store,
    )
    conv = first.create(refractory_ms=0)
    conv.turn("Explique la mémoire persistante")
    first.persist(conv)

    second = SessionBook(
        llm_factory=lambda: _backend("premières couches"),
        backend_resolver=_backend,
        storage=SQLiteSessionStore(tmp_path / "sessions.sqlite3"),
    )
    restored = second.require(conv.id)

    assert restored.id == conv.id
    assert restored.to_state() == conv.to_state()
    assert second.list_sessions()[0]["id"] == conv.id
    assert second.list_sessions()[0]["tours"] == 1


def test_unknown_session_lookup_does_not_mutate_sqlite(tmp_path):
    store = SQLiteSessionStore(tmp_path / "sessions.sqlite3")
    book = SessionBook(storage=store, backend_resolver=_backend)

    with pytest.raises(KeyError, match="inconnue"):
        book.require("inconnue")

    assert store.list_summaries() == []
    assert book._sessions == {}


def test_unsupported_session_schema_fails_loudly():
    conv = LyraConversation(llm=EchoClient(), backend_label="premières couches")
    state = conv.to_state()
    state["schema_version"] = 999

    with pytest.raises(SessionStateError, match="version"):
        LyraConversation.from_state(state, backend=_backend("premières couches"))


def test_corrupt_sqlite_payload_fails_loudly(tmp_path):
    store = SQLiteSessionStore(tmp_path / "sessions.sqlite3")
    store._initialize()
    with store._connect() as connection:
        connection.execute(
            """
            INSERT INTO sessions
                (session_id, schema_version, backend_label, turns,
                 created_at, updated_at, state_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("broken", 1, "premières couches", 0, 1.0, 1.0, "{not-json"),
        )

    with pytest.raises(SessionStorageError, match="illisible"):
        store.load("broken")


def test_sqlite_metadata_mismatch_fails_loudly(tmp_path):
    store = SQLiteSessionStore(tmp_path / "sessions.sqlite3")
    conv = LyraConversation(llm=EchoClient(), backend_label="premières couches")
    conv.turn("Une session cohérente")
    store.save(conv.to_state())

    with store._connect() as connection:
        connection.execute(
            "UPDATE sessions SET turns = 99 WHERE session_id = ?",
            (conv.id,),
        )

    with pytest.raises(SessionStorageError, match="incohérentes"):
        store.load(conv.id)


def test_non_finite_json_number_fails_loudly(tmp_path):
    store = SQLiteSessionStore(tmp_path / "sessions.sqlite3")
    conv = LyraConversation(llm=EchoClient(), backend_label="premières couches")
    state = conv.to_state()
    state["controller"]["pressure_i"] = 1e999

    with pytest.raises(SessionStorageError, match="invalide"):
        store.save(state)


def test_overflowing_json_exponent_fails_loudly_on_load(tmp_path):
    store = SQLiteSessionStore(tmp_path / "sessions.sqlite3")
    conv = LyraConversation(llm=EchoClient(), backend_label="premières couches")
    state = conv.to_state()
    payload = json.dumps(state, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace('"pressure_i":0.0', '"pressure_i":1e999')
    assert '"pressure_i":1e999' in payload
    store._initialize()
    with store._connect() as connection:
        connection.execute(
            """
            INSERT INTO sessions
                (session_id, schema_version, backend_label, turns,
                 created_at, updated_at, state_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conv.id,
                1,
                conv.backend_label,
                conv.turns,
                conv.created,
                conv.created,
                payload,
            ),
        )

    with pytest.raises(SessionStorageError, match="illisible"):
        store.load(conv.id)


def test_default_backend_resolver_never_substitutes_an_unknown_model(tmp_path):
    store = SQLiteSessionStore(tmp_path / "sessions.sqlite3")
    conv = LyraConversation(llm=EchoClient(model="other"), backend_label="other")
    store.save(conv.to_state())

    with pytest.raises(RuntimeError, match="aucun résolveur"):
        SessionBook(storage=store).require(conv.id)


def test_sqlite_connection_is_released_after_each_operation(tmp_path):
    database = tmp_path / "sessions.sqlite3"
    moved = tmp_path / "sessions.moved.sqlite3"
    store = SQLiteSessionStore(database)
    conv = LyraConversation(llm=EchoClient(), backend_label="premières couches")
    conv.turn("Ferme proprement la base")

    store.save(conv.to_state())
    assert store.load(conv.id)["turns"] == 1
    assert store.list_summaries()[0]["id"] == conv.id

    database.replace(moved)
    moved.replace(database)
