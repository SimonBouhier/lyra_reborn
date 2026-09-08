import hashlib
import json

import pytest

from app.journal import SQLiteJournalStore
from app.session import LyraConversation
from app.storage import SQLiteSessionStore, SessionStorageError
from core.llm import EchoClient
from scripts.migrate_p6_journal import migrate


def test_v1_is_refused_without_an_explicit_copy_migration(tmp_path):
    path = tmp_path / "old.sqlite3"
    store = SQLiteSessionStore(path)
    conv = LyraConversation(llm=EchoClient(), backend_label="premières couches")
    store.save(conv.to_state())
    before = path.read_bytes()
    with pytest.raises(SessionStorageError, match="version"):
        SQLiteJournalStore(path).get("id")
    assert path.read_bytes() == before


def test_copy_preserves_state_and_reports_lost_legacy_responses(tmp_path):
    source, destination = tmp_path / "old.sqlite3", tmp_path / "new.sqlite3"
    conv = LyraConversation(llm=EchoClient(), backend_label="premières couches", refractory_ms=0)
    for i in range(52):
        conv.turn(f"Mémoire ancienne {i}")
    old = SQLiteSessionStore(source)
    old.save(conv.to_state())
    expected = old.load(conv.id)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    report = migrate(source, destination)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    new = SQLiteJournalStore(destination)
    assert new.load(conv.id) == expected
    rows = new.history(conv.id, 0, 100)
    assert len(rows) == 52
    assert all(row["statut"] == "importe" and row["reponse"] is None for row in rows)
    assert rows[0]["texte"] == "Mémoire ancienne 0"
    assert rows[0]["historique_importe"]["sortie_moteur"] is None
    assert rows[-1]["historique_importe"]["sortie_moteur"] is not None
    assert report["sorties_moteur_absentes"] == 2
    assert report["reponses_affichees_non_reconstructibles"] == 52
    assert json.loads(destination.with_suffix(".migration.json").read_text(encoding="utf-8")) == report
    with pytest.raises(FileExistsError):
        migrate(source, destination)


def test_migration_keeps_v1_validation_strict(tmp_path):
    source, destination = tmp_path / "bad.sqlite3", tmp_path / "copy.sqlite3"
    old = SQLiteSessionStore(source)
    conv = LyraConversation(llm=EchoClient(), backend_label="premières couches")
    state = conv.to_state()
    state["turns"] = 2
    old.save(state)
    before = source.read_bytes()
    with pytest.raises(ValueError, match="historique incomplet"):
        migrate(source, destination)
    assert source.read_bytes() == before
    assert not destination.with_suffix(".migration.json").exists()
