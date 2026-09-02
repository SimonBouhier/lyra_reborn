"""Porte d'entrée P6 — premières couches.

Un serveur local qui expose le noyau (contrôle + mémoire) derrière une page.
CORS fermé sur localhost. Pas d'étoile. Rien n'est exposé sur le réseau.
"""
from __future__ import annotations
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core.llm import EchoClient
from app.backend import make_llm, restore_llm
from app.session import SessionBook, SessionStateError, format_path_reply
from app.storage import SQLiteSessionStore, SessionStorageError

STATIC = Path(__file__).resolve().parent / "static"
DEFAULT_DATABASE = Path(__file__).resolve().parents[1] / "data" / "lyra_sessions.sqlite3"
DATABASE = Path(os.getenv("LYRA_DB_PATH", str(DEFAULT_DATABASE)))
HOSTS = (
    "http://127.0.0.1:8766",
    "http://localhost:8766",
)

def _llm_factory(*, live: bool = False):
    return make_llm(live=live)


def _backend_resolver(label: str):
    return restore_llm(label)


book = SessionBook(
    llm_factory=_llm_factory,
    backend_resolver=_backend_resolver,
    storage=SQLiteSessionStore(DATABASE),
)
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
            conv = book.create(backend=requested_backend)
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
        book.rollback(conv.id, previous_state)
        raise HTTPException(
            status_code=503,
            detail="Lyra n'a pas pu enregistrer la session.",
        ) from exc
    except ValueError as exc:
        book.rollback(conv.id, previous_state)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        book.rollback(conv.id, previous_state)
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
        conv = book.require(sid)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc
    except (SessionStateError, SessionStorageError, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="La session durable ne peut pas être restaurée.",
        ) from exc
    return conv.snapshot()


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
