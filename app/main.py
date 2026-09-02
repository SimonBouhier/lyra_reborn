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
from app.backend import make_llm
from app.session import SessionBook, format_path_reply

STATIC = Path(__file__).resolve().parent / "static"
HOSTS = (
    "http://127.0.0.1:8766",
    "http://localhost:8766",
)

def _llm_factory(*, live: bool = False):
    return make_llm(live=live)


book = SessionBook(llm_factory=_llm_factory)
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
    if body.session is not None:
        try:
            conv = book.require(body.session)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc

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

    if requested_backend is not None:
        client, label = requested_backend
        conv.use_backend(client, label)
    try:
        rec = conv.turn(body.texte)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Lyra n'a pas pu joindre le modèle. Réessaie dans un instant.",
        ) from exc
    if isinstance(conv.llm, EchoClient):
        texte_out = format_path_reply(rec)
    else:
        texte_out = (rec.output or "").strip()
        if not texte_out:
            raise HTTPException(status_code=502, detail="Le modèle n'a rien renvoyé.")
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
    return conv.snapshot()


@app.get("/")
def accueil():
    page = STATIC / "index.html"
    if not page.exists():
        raise HTTPException(status_code=500, detail="page absente")
    return FileResponse(page)


if STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
