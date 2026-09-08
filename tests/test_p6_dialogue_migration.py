import hashlib
import pytest
from app.dialogue_store import DialogueStore
from app.journal import SQLiteJournalStore
from app.session import LyraConversation
from app.storage import SQLiteSessionStore, SessionStorageError
from core.llm import EchoClient
from scripts.migrate_p6_dialogue import migrate


@pytest.mark.parametrize('version', [1, 2])
def test_copy_preserves_legacy_state_and_original_file(tmp_path, version):
    source, destination = tmp_path / 'old.db', tmp_path / 'dialogue.db'
    old = (SQLiteSessionStore if version == 1 else SQLiteJournalStore)(source)
    conv = LyraConversation(llm=EchoClient(), backend_label='premières couches')
    conv.turn('Message original')
    old.save(conv.to_state())
    state = old.load(conv.id)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(SessionStorageError):
        DialogueStore(source).load(conv.id)
    report = migrate(source, destination)
    assert report['schema'] == 3 and report['profils_historiques_convertis'] == 0
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    assert DialogueStore(destination).load(conv.id) == state
    with pytest.raises(FileExistsError):
        migrate(source, destination)
