"""Mesures épistémiques SYNTHÉTIQUES (cohérence / fit / pression / tension).

⚠️ HONNÊTETÉ (charte §1 et §4) : ces fonctions sont des formules-jouets, PAS des
mesures d'une vraie génération. Elles proviennent de
session_2/lyra_framework_bundle/src/policies.py (lot 2), où elles servaient
d'« autopilote » : un système dynamique synthétique permettant de tester le
contrôleur P+I hors de toute génération LLM.

Rôle ici : uniquement l'AUTOPILOTE (démo + tests de la dynamique du contrôleur).
Dans la boucle réelle (core/loop.py), les signaux doivent provenir des vraies
métriques cheap (core/metrics/cheap.py) — le pont métriques→épistémique est un
chantier explicite (P2, voir BUILD_STATUS.md). Ne pas présenter ces sorties
comme des mesures réelles.
"""
from __future__ import annotations


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def measure_pressure(delta_r: float, tau_c: float) -> float:
    return _clip01(0.25 + 0.55 * delta_r + 0.30 * (tau_c - 0.22))


def measure_coherence(rho: float, delta_r: float, tau_c: float) -> float:
    b = 1.0 - abs(rho - 0.5) * 2.0
    c = max(0.0, 1.0 - abs(tau_c - 0.35) * 1.5)
    d = 1.0 - abs(delta_r - 0.6) * 1.2
    return _clip01(0.2 + 0.45 * b + 0.2 * c + 0.15 * d)


def measure_fit(coh: float, pressure: float) -> float:
    return _clip01(0.3 + 0.6 * coh - 0.05 * abs(pressure - 0.45))


def measure_tension(coh: float, fit: float, pressure: float) -> float:
    return _clip01(0.25 + 0.50 * pressure + 0.25 * (1.0 - 0.5 * (coh + fit)))
