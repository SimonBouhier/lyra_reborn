"""Contrat conversationnel : isolation, corrections et versions de tentative."""
import json
from threading import Event
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.dialogue import DialogueConversation, default_profile
from app.dialogue_store import DialogueStore
from app.context import assemble_context, ContextLimitError
from app.journal import RequestConflict
from app.requests import RequestService
from app.session import SessionBook, SessionStateError
from app.storage import SessionStorageError


class ScriptedChat:
    def __init__(self):
        self.calls = []

    def freeze(self, client=None):
        return {"adapter": "scripted-v1", "model": "factice", "digest": "fixture", "runtime": "fixture"}

    def chat(self, engine, messages, profile):
        self.calls.append(json.loads(json.dumps(messages)))
        return {"text": "Réponse factice " + str(len(self.calls)), "usage": {"prompt_tokens": 12, "output_tokens": 4}, "finish_reason": "stop"}


def runtime(path, chat=None):
    store = DialogueStore(path)
    book = SessionBook(storage=store, conversation_factory=DialogueConversation)
    chat = chat or ScriptedChat()
    service = RequestService(book, store, voice_factory=lambda: (None, "factice"), chat_adapter=chat)
    return service, chat


def ask(service, rid, text, sid=None):
    row = service.accept(rid, {"texte": text, "session": sid, "voix": True})
    return service.run(row["demande"])


def context(service, rid):
    return service.get(rid)["tentatives"][-1]["execution"]["context"]


def test_recent_messages_have_roles_and_do_not_require_derived_memory(tmp_path):
    service, chat = runtime(tmp_path / "dialogue.db")
    first = ask(service, "a1", "Deux options : cuivre ou verre.")
    sid = first["session"]
    second = ask(service, "a2", "Développe la deuxième.", sid)
    assert second["statut"] == "termine"
    assert chat.calls[-1][1:] == [
        {"role": "user", "content": "Deux options : cuivre ou verre."},
        {"role": "assistant", "content": "Réponse factice 1"},
        {"role": "user", "content": "Développe la deuxième."},
    ]
    state = service.store.load(sid)
    assert state["schema_version"] == 2 and state["turns"] == 2
    assert not {"graph", "controller", "memento", "ecology"}.intersection(state)
    resumed, _ = runtime(service.store.path, chat)
    assert resumed.book.require(sid).to_state() == state


def test_recall_only_imports_selected_message_and_follows_its_correction(tmp_path):
    service, chat = runtime(tmp_path / "dialogue.db")
    a = ask(service, "a1", "Le rendez-vous est mardi.")
    ask(service, "a2", "SECRET_EXCLU", a["session"])
    b = ask(service, "b1", "Conversation indépendante.")
    assert "mardi" not in json.dumps(chat.calls[-1])
    service.store.add_recall("lien1", b["session"], "a1", "user")
    service.store.correct("cor1", "a1", "user", "Le rendez-vous est jeudi.", None)
    ask(service, "b2", "Quel jour ?", b["session"])
    sent = json.dumps(chat.calls[-1], ensure_ascii=False)
    assert "jeudi" in sent and "mardi" in sent and "SECRET_EXCLU" not in sent
    assert "Réponse factice 1" not in sent  # seule la parole utilisateur rappelée
    assert context(service, "b2")["recalls"][0]["correction"]["id"] == "cor1"
    assert service.get("a1")["texte"] == "Le rendez-vous est mardi."
    service.store.remove_recall("lien1", b["session"])
    ask(service, "b3", "La suite", b["session"])
    assert context(service, "b3")["recalls"] == []


def test_corrections_are_idempotent_and_concurrent_revisions_conflict(tmp_path):
    service, _ = runtime(tmp_path / "dialogue.db")
    ask(service, "a1", "Version originale")
    first = service.store.correct("c1", "a1", "user", "Version corrigée", None)
    assert service.store.correct("c1", "a1", "user", "Version corrigée", None) == first
    with pytest.raises(RequestConflict):
        service.store.correct("c2", "a1", "user", "Correction périmée", None)
    with pytest.raises(RequestConflict):
        service.store.correct("c1", "a1", "user", "Identité détournée", None)
    latest = service.store.correct("c2", "a1", "user", "Nouvelle correction", "c1")
    assert latest["previous"] == "c1"


def test_context_is_frozen_for_a_running_attempt_but_new_attempt_sees_correction(tmp_path):
    service, chat = runtime(tmp_path / "dialogue.db")
    a = ask(service, "a1", "Ancienne information")
    entered, release = Event(), Event()
    original = chat.chat

    def paused(*args):
        entered.set()
        assert release.wait(10)
        raise RuntimeError("calcul interrompu facticement")

    chat.chat = paused
    service.accept("a2", {"texte": "Poursuis", "session": a["session"], "voix": True})
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(service.run, "a2")
        try:
            assert entered.wait(10)
            before = context(service, "a2")
            service.store.correct("c1", "a1", "user", "Nouvelle information", None)
        finally:
            release.set()
        assert pending.result()["statut"] == "echoue"
    chat.chat = original
    result = service.run("a2", retry_id="reprise")
    assert result["statut"] == "termine"
    assert result["tentatives"][0]["execution"]["context"] == before
    assert "Nouvelle information" in json.dumps(chat.calls[-1], ensure_ascii=False)


def test_budget_reports_omissions_and_refuses_required_content_without_calling_model(tmp_path):
    service, chat = runtime(tmp_path / "dialogue.db")
    a = ask(service, "a1", "a" * 700)
    sid = a["session"]
    service.accept("a2", {"texte": "Courant", "session": sid, "voix": True})
    snapshot = service.store.context_source("a2")
    profile = default_profile()
    profile["max_input_characters"] = 700
    result = assemble_context(snapshot, profile)
    assert result["omissions"] and result["messages"][-1]["content"] == "Courant"
    snapshot["request"]["texte"] = "x" * 1000
    with pytest.raises(ContextLimitError):
        assemble_context(snapshot, profile)
    assert len(chat.calls) == 1


def test_strict_reference_state_rejects_missing_profile(tmp_path):
    service, _ = runtime(tmp_path / "dialogue.db")
    a = ask(service, "a1", "Bonjour")
    state = service.store.load(a["session"])
    del state["profile"]
    with pytest.raises((SessionStateError, ValueError)):
        DialogueConversation.from_state(state)


def test_recalls_do_not_follow_other_recalls_transitively(tmp_path):
    service, chat = runtime(tmp_path / "dialogue.db")
    ask(service, "source", "CONTENU_NON_SELECTIONNE")
    middle = ask(service, "milieu", "Message à rappeler")
    service.store.add_recall("vers-milieu", middle["session"], "source", "user")
    destination = ask(service, "destination", "Autre conversation")
    service.store.add_recall("vers-destination", destination["session"], "milieu", "user")
    ask(service, "suite", "Poursuis", destination["session"])
    sent = json.dumps(chat.calls[-1], ensure_ascii=False)
    assert "Message à rappeler" in sent and "CONTENU_NON_SELECTIONNE" not in sent


@pytest.mark.parametrize("after_commit", [False, True])
def test_dialogue_publication_failure_respects_the_durable_decision(tmp_path, monkeypatch, after_commit):
    service, chat = runtime(tmp_path / "dialogue.db")
    accepted = service.accept("a1", {"texte": "Bonjour", "session": None, "voix": True})
    complete = service.store.complete

    def broken(*args):
        if after_commit:
            complete(*args)
        raise SessionStorageError("publication facticement interrompue")

    monkeypatch.setattr(service.store, "complete", broken)
    result = service.run("a1")
    assert result["statut"] == ("termine" if after_commit else "echoue")
    assert service.store.load(accepted["session"])["turns"] == int(after_commit)
    resumed, _ = runtime(service.store.path, chat)
    assert resumed.run("a1")["statut"] == result["statut"]
    assert len(chat.calls) == 1  # relire n'appelle pas le modèle


def test_failed_first_attempt_keeps_its_engine_on_explicit_retry(tmp_path):
    service, chat = runtime(tmp_path / "dialogue.db")
    freezes, engines = [], []
    original = chat.chat

    def freeze(_):
        freezes.append(1)
        return {"adapter": "scripted-v1", "model": "initial", "digest": "initial", "runtime": "fixture"}

    def fail(engine, *args):
        engines.append(engine)
        raise RuntimeError("première tentative échouée")

    chat.freeze, chat.chat = freeze, fail
    assert ask(service, "a1", "Bonjour")["statut"] == "echoue"
    def resume(engine, *args):
        engines.append(engine)
        return original(engine, *args)
    chat.chat = resume
    assert service.run("a1", retry_id="reprise")["statut"] == "termine"
    assert len(freezes) == 1 and engines[0] == engines[1]
