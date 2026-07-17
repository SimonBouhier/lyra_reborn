"""Politique de modulation RÉACTIVE : métriques cheap -> ajustement des boutons.

Porté de conscious/policies/modulator.py (lot 1). C'est la politique qui pilote
la boucle réelle (core/loop.py) à partir des vraies métriques d'une génération.
À distinguer du contrôleur P+I (core/control/controller.py) qui régule, lui, une
dynamique épistémique — voir la note d'architecture dans BUILD_STATUS.md.
"""
from __future__ import annotations
from typing import Dict

from core.knobs import Knobs, clamp01


TASK_OVERRIDES: Dict[str, Dict[str, float]] = {
    "creative": {"tau_c": 0.95, "rho": 0.85, "kappa": 0.35, "delta_r": 0.75},
    "focused":  {"tau_c": 0.60, "rho": 0.55, "kappa": 0.70, "delta_r": 0.45},
    "strict":   {"tau_c": 0.35, "rho": 0.50, "kappa": 0.85, "delta_r": 0.35},
}


def apply_task_overrides(knobs: Knobs, task_type: str) -> Knobs:
    ov = TASK_OVERRIDES.get(task_type or "", {})
    d = knobs.as_dict()
    for k, v in ov.items():
        d[k] = clamp01(v)
    return Knobs.from_dict(d)


def decide_next_knobs(cur: Knobs, cheap: Dict[str, float]) -> Knobs:
    """Règles simples et lisibles :
      - répétitions        -> ↑κ (repeat_penalty), ↓τc (température)
      - structure faible   -> ↑ρ (cohésion), ↑δr (longueur)
      - pertinence faible  -> ↑ρ, ↑τc (légère) pour explorer
    """
    rho, dr, tau, kap = cur.rho, cur.delta_r, cur.tau_c, cur.kappa
    rep = cheap.get("repeat4", 0.0)
    ko = cheap.get("kw_overlap", 0.0)
    ss = cheap.get("struct", 0.0)

    if rep > 0.01:
        kap = min(1.0, kap + 0.10)
        tau = max(0.0, tau - 0.05)
    if ss < 0.45:
        rho = min(1.0, rho + 0.08)
        dr = min(1.0, dr + 0.08)
    if ko < 0.12:
        rho = min(1.0, rho + 0.10)
        tau = min(1.0, tau + 0.05)

    return Knobs(rho=rho, delta_r=dr, tau_c=tau, kappa=kap)
