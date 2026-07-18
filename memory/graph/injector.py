"""Injecteur nemeton : résumé BORNÉ de l'état du graphe pour le prompt système.

Design de `Lyra_Uni_0_2/nemeton_prompt_injector.py` (audité : câblé et honnête),
ré-implémenté borné. Posture inchangée : le modèle UTILISE Lyra, il n'EST PAS
Lyra — l'injection est un contexte, pas une identité.
"""
from __future__ import annotations
from typing import List

from memory.graph.store import GraphStore


def inject(store: GraphStore, max_chars: int = 1200, top: int = 8) -> str:
    """Bloc d'injection déterministe et borné (≤ max_chars, garanti).

    Contenu : volumétrie + concepts les plus connectés (degré) + entrées
    récentes. Tronque proprement si nécessaire — jamais de graphe entier
    sérialisé dans un prompt (leçon de l'audit : 1,18 M d'arêtes injectées).
    """
    c = store.counts()
    if c["nodes"] == 0:
        return "[NEMETON] graphe vide."

    nodes = store.list_nodes(limit=10_000)
    by_degree = sorted(nodes, key=lambda n: (store.degree(n.id), n.ts), reverse=True)
    hubs: List[str] = [f"{n.id}({store.degree(n.id)})" for n in by_degree[:top]]
    recent: List[str] = [n.id for n in nodes[:top]]

    txt = (
        f"[NEMETON] {c['nodes']} concepts, {c['edges']} liens. "
        f"Plus connectés : {', '.join(hubs)}. "
        f"Récents : {', '.join(recent)}."
    )
    if len(txt) > max_chars:
        txt = txt[: max_chars - 1] + "…"
    return txt
