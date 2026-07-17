"""Garde-fous anti-oscillation : clamp + hystérésis + période réfractaire.

Porté de conscious/guards.py (lot 1). Combiné à l'EWMA de CognitiveState, c'est
le triple anti-oscillation (EWMA + zone morte + réfractaire) que l'audit a
désigné comme la meilleure brique réutilisable du canon.
"""
from __future__ import annotations
from typing import Dict

from core.knobs import clamp01
from core.state import CognitiveState
from core.config import SmoothingConfig


def clamp_and_hysteresis(state: CognitiveState, target: Dict[str, float],
                         smoothing: SmoothingConfig) -> Dict[str, float]:
    """Clamp [0,1] + zone morte : sous `hysteresis_eps`, on garde la valeur courante."""
    out: Dict[str, float] = {}
    for name in ("rho", "delta_r", "tau_c", "kappa"):
        cur = getattr(state.knobs, name)
        tar = clamp01(target[name])
        out[name] = cur if abs(tar - cur) < smoothing.hysteresis_eps else tar
    return out


def refractory_ok(state: CognitiveState, smoothing: SmoothingConfig) -> bool:
    """Vrai si la période réfractaire est écoulée (on peut re-moduler)."""
    return state.elapsed_since_update_ms() >= smoothing.refractory_ms
