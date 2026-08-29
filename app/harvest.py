"""Récolte bornée de concepts pour un tour de chat (première couche P6).

Pas un nœud par mot (leçon Uni : 1,18 M d'arêtes). Le prompt de l'humain
fournit au plus MAX_CONCEPTS tokens assez longs, hors mots-outils.
"""
from __future__ import annotations
from typing import List

from core.metrics.cheap import tokens

MAX_CONCEPTS = 5
MIN_LEN = 5

# Mots-outils fréquents — volontairement court. Ce n'est pas un parseur linguistique.
STOP = {
    "alors", "avec", "cette", "comme", "dans", "dont", "elle", "elles", "entre",
    "est", "les", "leur", "leurs", "mais", "même", "nous", "pour", "plus",
    "que", "qui", "sans", "sont", "sous", "sur", "une", "vous", "the", "and",
    "for", "that", "this", "with", "from", "have", "not", "are", "was", "were",
    "peut", "être", "fait", "faire", "tout", "tous", "bien", "aussi", "très",
    "comment", "pourquoi", "quand", "quel", "quelle", "quels", "quelles",
    "explique", "expliquer", "relie", "maintenant", "langage", "simple",
}


def harvest_concepts(text: str, limit: int = MAX_CONCEPTS) -> List[str]:
    """Retourne 0 à `limit` concepts, dans l'ordre d'apparition, sans doublon."""
    seen = set()
    out: List[str] = []
    for tok in tokens(text or ""):
        if len(tok) < MIN_LEN or tok in STOP:
            continue
        if tok in seen:
            continue
        seen.add(tok)
        out.append(tok)
        if len(out) >= limit:
            break
    return out
