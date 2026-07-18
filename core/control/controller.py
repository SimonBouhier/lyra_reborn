"""Contrôleur P+I à intégrateur fuyant — le régulateur de dynamique de Lyra.

Porté fidèlement de session_2/lyra_framework_bundle/src/run_loop3.py:controllers()
(lot 2), la version FONCTIONNELLE du contrôleur (l'audit a montré que ses 7 clés
de réglage sont réellement actives et que les consignes sont atteintes). Ré-
implémenté proprement avec une config typée au lieu d'un dict JSON.

Loi de commande :
  - TENSION -> τc     : proportionnel (P).
  - PRESSION -> δr     : P + intégrateur fuyant borné (I), avec purge asymétrique
    et anti-windup ; partage d'une part de l'intégrale vers τc quand δr sature
    sans que la pression baisse ; soft-cap sur δr.

⚠️ Ce contrôleur régule des signaux épistémiques (cohérence/fit/pression). Dans
l'autopilote (démo/tests) ils viennent de core/control/measures.py (synthétiques,
étiquetés). Dans la boucle réelle, ils devront venir des vraies métriques — pont
P2 (voir BUILD_STATUS.md). κ et ρ ne sont pas touchés par ce contrôleur.
"""
from __future__ import annotations
from dataclasses import dataclass

from core.knobs import Knobs
from core.control.measures import measure_tension


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


@dataclass
class ControlConfig:
    """Valeurs **calibrées empiriquement « B03 + P1P2 »** (baseline documentée dans
    `session_2/lyra_framework_bundle/README_ly_fr_bun.md`, alias le starter-kit de
    l'atelier — archivé ici : `docs/STARTER_KIT_ATELIER_B03_P1P2.md`). Elles
    remplacent les valeurs par défaut « au jugé » de la première version.

    ⚠️ **Échelle de τc** : dans le framework d'origine `tau_c ∈ [0.22, 1.60]` (une
    grandeur brute). Ici τc est un **bouton normalisé [0,1]** mappé vers la
    température ⇒ on garde `tau_c_hi = 1.0` (on ne copie PAS 1.60). En revanche
    setpoints, gains, zones mortes opèrent sur tension/pression ∈ [0,1] et sont
    transférables tels quels.
    """
    tau_c_lo: float = 0.22       # plancher (cf. critère §8 : τc_min ≥ 0.22)
    tau_c_hi: float = 1.0        # cap normalisé (framework : 1.60 → non transférable)
    tension_setpoint: float = 0.55
    pressure_setpoint: float = 0.45
    tension_band: float = 0.05
    pressure_band: float = 0.06
    kp_tension: float = 0.23
    kp_pressure: float = 0.07
    ki_pressure: float = 0.012
    pressure_i_leak: float = 0.03
    pressure_i_max: float = 0.12
    pressure_i_split_tau: float = 0.65     # part de l'intégrale réservée au partage vers τc
    pressure_tau_share_delta_r_gate: float = 0.82
    pressure_tau_share_gain: float = 0.12
    pressure_margin: float = 0.02
    delta_r_nudge_high: float = 0.025
    delta_r_floor: float = 0.28
    delta_r_soft_cap: float = 0.90


# Critères d'acceptation « on passe à la suite » (fenêtre 30 pas), issus du
# starter-kit B03+P1P2 (§8). Ce sont des cibles de CALIBRATION pour un run réel
# (métriques dérivées du graphe). L'autopilote synthétique (measures.py) ne vise
# qu'un sous-ensemble robuste — cf. tests/test_control_criteria.py.
ACCEPTANCE_CRITERIA = {
    "pressure_mean": (0.44, 0.46),
    "tension_mean": (0.54, 0.58),
    "tau_c_min": 0.22,       # ne pas coller au plancher
    "max_R2_streak": 10,     # strictement <
    "lambda_count_low": True,
}


class PIController:
    """Contrôleur avec état interne (l'intégrale de pression `pressure_i`)."""

    def __init__(self, cfg: ControlConfig | None = None):
        self.cfg = cfg or ControlConfig()
        self.pressure_i: float = 0.0

    def step(self, knobs: Knobs, coherence: float, fit: float, pressure: float) -> Knobs:
        """Un pas de régulation. Retourne des boutons mis à jour (δr, τc)."""
        c = self.cfg
        lo, hi = c.tau_c_lo, c.tau_c_hi
        rho, delta_r, tau_c, kappa = knobs.rho, knobs.delta_r, knobs.tau_c, knobs.kappa

        # clamp initial de τc
        tau_c = _clamp(tau_c, lo, hi)

        tens = measure_tension(coherence, fit, pressure)

        # TENSION -> τc (P)
        err_t = tens - c.tension_setpoint
        if abs(err_t) > c.tension_band:
            tau_c = _clamp(tau_c - c.kp_tension * err_t, lo, hi)

        # PRESSION -> δr & τc (P + I fuyant)
        err_p = c.pressure_setpoint - pressure
        if abs(err_p) > c.pressure_band:
            self.pressure_i = self.pressure_i + c.ki_pressure * err_p
        # fuite + bornage de l'intégrale
        self.pressure_i = max(-c.pressure_i_max,
                              min(c.pressure_i_max, self.pressure_i * (1.0 - c.pressure_i_leak)))

        split = c.pressure_i_split_tau
        delta_p = c.kp_pressure * err_p + (1.0 - split) * self.pressure_i
        delta_r = _clamp(delta_r + delta_p)

        # partage vers τc si δr saturé alors que la pression reste basse
        if pressure < c.pressure_setpoint - c.pressure_band and delta_r > c.pressure_tau_share_delta_r_gate:
            d_tau = max(0.0, split * self.pressure_i) + c.pressure_tau_share_gain * (c.pressure_setpoint - pressure)
            tau_c = min(hi, tau_c + d_tau)

        # purge asymétrique + anti-windup si pression trop haute
        if pressure > c.pressure_setpoint + c.pressure_margin:
            delta_r = max(c.delta_r_floor, delta_r - c.delta_r_nudge_high)
            if self.pressure_i > 0:
                self.pressure_i *= 0.5

        # soft-cap sur δr
        if delta_r > c.delta_r_soft_cap:
            delta_r = max(c.delta_r_soft_cap, delta_r - 0.02)

        # re-clamp τc
        tau_c = _clamp(tau_c, lo, hi)

        return Knobs(rho=rho, delta_r=delta_r, tau_c=tau_c, kappa=kappa)
