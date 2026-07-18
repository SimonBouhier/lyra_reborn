"""Similarité textuelle Jaro-Winkler — récolte EPP_Verdict (ADR-011-v2).

EPP utilise `rapidfuzz.distance.JaroWinkler` dans sa cascade de matching
(exact → JW > 0.9 → cosinus embedding). Implémentation stdlib ici (algorithme
standard, vérifiée sur les vecteurs de référence classiques) pour préserver la
pureté du noyau. Étage intermédiaire de la cascade du consensus : déterministe,
zéro appel modèle — attrape accents, coquilles et variantes proches que
`match_key` rate, avant de payer un embedding.
"""
from __future__ import annotations


def jaro(a: str, b: str) -> float:
    if a == b:
        return 1.0
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return 0.0
    window = max(la, lb) // 2 - 1
    if window < 0:
        window = 0
    match_a = [False] * la
    match_b = [False] * lb

    matches = 0
    for i in range(la):
        lo = max(0, i - window)
        hi = min(lb, i + window + 1)
        for j in range(lo, hi):
            if not match_b[j] and a[i] == b[j]:
                match_a[i] = True
                match_b[j] = True
                matches += 1
                break
    if matches == 0:
        return 0.0

    # transpositions : ordre des caractères appariés
    transpositions = 0
    k = 0
    for i in range(la):
        if match_a[i]:
            while not match_b[k]:
                k += 1
            if a[i] != b[k]:
                transpositions += 1
            k += 1
    transpositions //= 2

    m = float(matches)
    return (m / la + m / lb + (m - transpositions) / m) / 3.0


def jaro_winkler(a: str, b: str, prefix_scale: float = 0.1) -> float:
    """Jaro-Winkler : bonus de préfixe commun (jusqu'à 4 caractères)."""
    j = jaro(a, b)
    prefix = 0
    for ca, cb in zip(a[:4], b[:4]):
        if ca != cb:
            break
        prefix += 1
    return j + prefix * prefix_scale * (1.0 - j)
