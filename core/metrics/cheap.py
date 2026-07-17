"""Métriques « bon marché », sans modèle, calculées sur le texte.

Porté fidèlement de conscious/metrics/cheap.py (lot 1). Servent à la politique
de modulation réactive (core/control/reactive.py) : détecter répétitions,
structure faible, faible pertinence, troncature, carry-over inter-prompts.
"""
from __future__ import annotations
from typing import List, Dict
from collections import Counter
import re

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+")


def tokens(text: str) -> List[str]:
    return [t.lower() for t in WORD_RE.findall(text or "")]


def keyword_overlap(prompt: str, output: str) -> float:
    """Jaccard entre les mots-clés fréquents du prompt et les mots de la sortie."""
    p = tokens(prompt)
    o = tokens(output)
    if not p or not o:
        return 0.0
    top_p = set(k for k, _ in Counter(p).most_common(min(15, len(p))))
    o_set = set(o)
    union = len(top_p | o_set)
    return len(top_p & o_set) / union if union else 0.0


def repeat4_rate(output: str) -> float:
    """Taux de 4-grammes répétés (emballement)."""
    toks = tokens(output)
    if len(toks) < 8:
        return 0.0
    grams = [" ".join(toks[i:i + 4]) for i in range(len(toks) - 3)]
    c = Counter(grams)
    total = max(1, len(grams))
    return sum(v for v in c.values() if v > 1) / total


def structure_score(output: str) -> float:
    """Score de structure ∈ [0,1] : titres/listes/sections, pénalise les murs de texte."""
    if not output:
        return 0.0
    lines = [l.strip() for l in output.splitlines() if l.strip()]
    if not lines:
        return 0.0
    n = len(lines)
    heads = sum(1 for l in lines if l.startswith(("#", "##", "###")) or re.match(r"^\*\*.+\*\*$", l))
    bullets = sum(1 for l in lines if l.startswith(("-", "*", "•", "1.", "2.", "3.")))
    codef = sum(1 for l in lines if l.startswith("```"))
    sections = sum(1 for l in lines if re.search(r"^(?:##|—|-{3,}|_{3,})", l))
    density = min(1.0, (heads * 1.2 + bullets * 0.8 + sections * 0.6 + codef * 1.0) / max(4.0, n / 10))
    avg_len = sum(len(l) for l in lines) / n
    wall_penalty = 1.0 if avg_len < 220 else max(0.35, 1.5 - avg_len / 220.0)
    return max(0.0, min(1.0, density * wall_penalty))


def truncation_suspect(output: str, num_predict: int, trunc_margin: float) -> bool:
    return len(tokens(output)) >= int(trunc_margin * max(1, num_predict))


def carryover_intrusion(prev_prompt: str, cur_prompt: str) -> float:
    """Jaccard entre l'ancien et le nouveau prompt (reprise de sujet)."""
    prev = set(tokens(prev_prompt))
    cur = set(tokens(cur_prompt))
    union = len(prev | cur)
    return len(prev & cur) / union if union else 0.0


def hedge_score(prompt: str, output: str) -> Dict[str, float]:
    """Évaluation rapide de la sortie (0-1, ↑ meilleur) + métriques composantes."""
    ko = keyword_overlap(prompt, output)
    r4 = repeat4_rate(output)
    ss = structure_score(output)
    quick = max(0.0, min(1.0, ko * ss * (1.0 - min(1.0, r4 * 5))))
    return {"kw_overlap": ko, "repeat4": r4, "struct": ss, "hedge": quick}
