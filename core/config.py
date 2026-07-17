"""Config de base du noyau Lyra (seuils de garde + lissage).

Porté fidèlement depuis le canon `conscious/config.py` (lot 1), qui est la
formulation la plus propre de ces réglages. Voir manifeste/VOCABULAIRE.md.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class HeuristicThresholds:
    """Seuils de garde : emballement / troncature / carry-over inter-prompts."""
    max_repeat4: float = 0.02
    min_keyword_overlap: float = 0.02
    max_intrusion_prev_prompt: float = 0.35
    trunc_margin: float = 0.95  # sortie > 95 % du budget de tokens ⇒ troncature suspecte


@dataclass
class SmoothingConfig:
    """Anti-oscillation : lissage EWMA + zone morte (hystérésis) + période réfractaire."""
    ewma_alpha: float = 0.35       # lissage de l'état
    hysteresis_eps: float = 0.05   # zone morte : en-deçà, on ne bouge pas le bouton
    refractory_ms: int = 1200      # délai minimal entre deux re-modulations
