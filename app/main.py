"""Porte P6 : journal et dialogue de référence, archives de contrôle préservées.

À lancer sur l'interface locale ; CORS limité aux origines du lanceur.
"""
from __future__ import annotations
import os
from pathlib import Path
import uuid

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict, StrictBool

from core.llm import EchoClient
from app.backend import make_llm, restore_llm
from app.session import SessionBook, SessionBusyError, SessionStateError, format_path_reply
from app.storage import SessionStorageError
from app.journal import SQLiteJournalStore, RequestConflict
from app.requests import RequestService
from app.dialogue import DialogueConversation
from app.dialogue_store import DialogueStore

STATIC = Path(__file__).resolve().parent / "static"
DEFAULT_DATABASE = Path(__file__).resolve().parents[1] / "data" / "lyra_sessions.sqlite3"
DATABASE = Path(os.getenv("LYRA_DB_PATH", str(DEFAULT_DATABASE)))
HOSTS = (
    "http://127.0.0.1:8766",
    "http://localhost:8766",
)
SESSION_BUSY_DETAIL = (
    "Cette conversation est occupée. "
    "Réessaie après la fin de l'opération en cours."
)

def _llm_factory(*, live: bool = False):
    return make_llm(live=live)


def _backend_resolver(label: str):
    return restore_llm(label)


book = SessionBook(
    llm_factory=lambda: (EchoClient(), "conversation sans modèle"),
    backend_resolver=_backend_resolver,
    storage=DialogueStore(DATABASE),
    conversation_factory=DialogueConversation,
)
request_service = RequestService(book, book._storage, voice_factory=lambda: make_llm(live=True))
app = FastAPI(title="Lyra", version="0.1.0.dev0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(HOSTS),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ChatIn(BaseModel):
    texte: str = Field(..., min_length=1)
    session: str | None = None
    voix: bool = False


@app.get("/api/sante")
def sante():
    return {"ok": True, "moteur": "configuration par session"}


@app.post("/api/parler")
def parler(body: ChatIn):
    if isinstance(book._storage, SQLiteJournalStore):
        raise HTTPException(status_code=410, detail="Recharge la page pour utiliser les demandes enregistrées.")
    # L'identité précède la publication du nouvel objet dans le registre.
    sid = body.session if body.session is not None else uuid.uuid4().hex[:12]
    try:
        with book.exclusive(sid):
            return _parler_exclusif(body, sid)
    except SessionBusyError as exc:
        raise HTTPException(status_code=409, detail=SESSION_BUSY_DETAIL) from exc


class DemandeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    demande: str = Field(..., pattern=r"^[A-Za-z0-9_-]{1,128}$")
    texte: str = Field(..., min_length=1, max_length=100_000)
    session: str | None = Field(None, pattern=r"^[A-Za-z0-9_-]{1,128}$")
    voix: StrictBool = False


class RelanceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    relance: str = Field(..., pattern=r"^[A-Za-z0-9_-]{1,128}$")


class ConversationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conversation: str = Field(..., pattern=r"^[A-Za-z0-9_-]{1,128}$")


class CorrectionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    correction: str = Field(..., pattern=r"^[A-Za-z0-9_-]{1,128}$")
    texte: str = Field(..., min_length=1, max_length=100000)
    precedente: str | None = None


class RappelIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rappel: str = Field(..., pattern=r"^[A-Za-z0-9_-]{1,128}$")
    source: str = Field(..., pattern=r"^[A-Za-z0-9_-]{1,128}$")
    role: str = Field(..., pattern=r"^(user|assistant)$")


def _journal_call(operation):
    try:
        return operation()
    except SessionBusyError as exc:
        raise HTTPException(status_code=409, detail=SESSION_BUSY_DETAIL) from exc
    except RequestConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Demande ou conversation inconnue.") from exc
    except (SessionStorageError, SessionStateError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=(
            "Le journal ne peut pas être utilisé. Conserve l'identifiant de la demande. "
            "Une ancienne base nécessite la migration sur copie décrite dans le guide P6."
        )) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/demandes")
def accepter_demande(body: DemandeIn):
    return _journal_call(lambda: request_service.accept(
        body.demande, {"texte": body.texte, "session": body.session, "voix": body.voix},
    ))


@app.get("/api/demandes/{rid}")
def lire_demande(rid: str):
    return _journal_call(lambda: request_service.get(rid))


@app.post("/api/demandes/{rid}/executer")
def executer_demande(rid: str):
    return _journal_call(lambda: request_service.run(rid))


@app.post("/api/demandes/{rid}/relancer")
def relancer_demande(rid: str, body: RelanceIn):
    return _journal_call(lambda: request_service.run(rid, retry_id=body.relance))


@app.get("/api/session/{sid}/journal")
def journal_session(sid: str, apres: int = Query(0, ge=0), limite: int = Query(50, ge=1, le=100)):
    def read():
        request_service.start()
        rows = request_service.store.history(sid, apres, limite)
        return {"session": sid, "demandes": rows,
                "curseur": rows[-1]["position"] if rows else apres}
    return _journal_call(read)


@app.post("/api/conversations")
def creer_conversation(body: ConversationIn):
    def create():
        request_service.start()
        with book.exclusive(body.conversation):
            try:
                return book.require(body.conversation).snapshot()
            except KeyError:
                conv = book.create(session_id=body.conversation)
                try:
                    book.persist(conv)
                except Exception:
                    book.rollback(conv.id, None)
                    raise
                return conv.snapshot()
    return _journal_call(create)


@app.get("/api/passages/{rid}/{role}")
def lire_passage(rid: str, role: str):
    return _journal_call(lambda: request_service.store.passage(rid, role))


@app.post("/api/passages/{rid}/{role}/corrections")
def corriger_passage(rid: str, role: str, body: CorrectionIn):
    return _journal_call(lambda: request_service.store.correct(body.correction, rid, role, body.texte, body.precedente))


@app.get("/api/session/{sid}/rappels")
def lire_rappels(sid: str):
    return _journal_call(lambda: {"rappels": request_service.store.recalls(sid)})


@app.post("/api/session/{sid}/rappels")
def ajouter_rappel(sid: str, body: RappelIn):
    return _journal_call(lambda: request_service.store.add_recall(body.rappel, sid, body.source, body.role))


@app.post("/api/session/{sid}/rappels/{rid}/retirer")
def retirer_rappel(sid: str, rid: str):
    return _journal_call(lambda: request_service.store.remove_recall(rid, sid))


def _rollback_or_unavailable(sid, previous_state):
    try:
        book.rollback(sid, previous_state)
    except (SessionStateError, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Le retour à l'état précédent a échoué. "
                "La session doit être restaurée depuis le stockage durable."
            ),
        ) from exc


def _parler_exclusif(body: ChatIn, sid: str):
    """Cycle complet sous réservation, y compris restauration et rollback."""
    conv = None
    previous_state = None
    if body.session is not None:
        try:
            conv = book.require(body.session)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc
        except (SessionStateError, SessionStorageError, RuntimeError) as exc:
            raise HTTPException(
                status_code=503,
                detail="La session durable ne peut pas être restaurée.",
            ) from exc
        try:
            previous_state = conv.to_state()
        except SessionStateError as exc:
            raise HTTPException(
                status_code=503,
                detail="La session active ne peut pas être préparée pour une sauvegarde.",
            ) from exc

    requested_backend = None
    if body.voix:
        try:
            requested_backend = make_llm(live=True)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    if conv is None:
        try:
            conv = book.create(session_id=sid, backend=requested_backend)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        if requested_backend is not None:
            client, label = requested_backend
            conv.use_backend(client, label)
        rec = conv.turn(body.texte)
        if isinstance(conv.llm, EchoClient):
            texte_out = format_path_reply(rec)
        else:
            texte_out = (rec.output or "").strip()
            if not texte_out:
                raise RuntimeError("le modèle n'a rien renvoyé")
        book.persist(conv)
    except (SessionStateError, SessionStorageError) as exc:
        _rollback_or_unavailable(conv.id, previous_state)
        raise HTTPException(
            status_code=503,
            detail="Lyra n'a pas pu enregistrer la session.",
        ) from exc
    except ValueError as exc:
        _rollback_or_unavailable(conv.id, previous_state)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        _rollback_or_unavailable(conv.id, previous_state)
        raise HTTPException(
            status_code=502,
            detail="Lyra n'a pas pu joindre le modèle. Réessaie dans un instant.",
        ) from exc
    return {
        "session": conv.id,
        "reponse": texte_out,
        "boutons": rec.knobs_used,
        "boutons_suivants": rec.knobs_next,
        "options": rec.options,
        "module": rec.modulated,
        "graphe": rec.graph,
        "memoire": rec.ecology,
        "concepts": rec.concepts,
        "nemeton": rec.nemeton,
        "moteur": conv.backend_label,
    }


@app.get("/api/session/{sid}")
def session_etat(sid: str):
    try:
        with book.exclusive(sid):
            conv = book.require(sid)
            return conv.snapshot()
    except SessionBusyError as exc:
        raise HTTPException(status_code=409, detail=SESSION_BUSY_DETAIL) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc
    except (SessionStateError, SessionStorageError, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="La session durable ne peut pas être restaurée.",
        ) from exc


@app.get("/api/sessions")
def sessions():
    try:
        return {"sessions": book.list_sessions()}
    except SessionStorageError as exc:
        raise HTTPException(
            status_code=503,
            detail="Le registre durable des sessions est indisponible.",
        ) from exc


@app.get("/")
def accueil():
    page = STATIC / "index.html"
    if not page.exists():
        raise HTTPException(status_code=500, detail="page absente")
    return FileResponse(page)


if STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
