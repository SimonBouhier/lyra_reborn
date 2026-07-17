"""Politique de phase λ (SEUIL) + garde à hystérésis.

Porté de session_2/lyra_framework_bundle/src/policies.py:PolicySEUIL (lot 2).
La spec complète de la phase λ vit dans session_2/Archi (phase_lambda.md + SEUIL)
— acompte sur la couche P2. Quand la cohérence dépasse un seuil, on entre en
phase λ (léger boost de τc) ; en sortie, une période de cooldown évite le
papillotement.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class LambdaConfig:
    threshold: float = 0.90
    tau_gain: float = 1.04
    tau_bias: float = 0.015
    cooldown: int = 5


class PolicyLambda:
    """Détecteur de phase λ avec cooldown (anti-papillotement)."""

    def __init__(self, cfg: LambdaConfig | None = None):
        self.cfg = cfg or LambdaConfig()
        self._cool = 0
        self.active = False

    def step(self, coherence: float, tau_c: float) -> tuple[bool, float]:
        """Retourne (phase_λ_active, τc éventuellement boosté)."""
        c = self.cfg
        if self._cool > 0:
            self._cool -= 1
            self.active = False
            return False, tau_c

        if coherence >= c.threshold:
            self.active = True
            tau_c = tau_c * c.tau_gain + c.tau_bias
            return True, tau_c

        if self.active:
            self._cool = c.cooldown
        self.active = False
        return False, tau_c
