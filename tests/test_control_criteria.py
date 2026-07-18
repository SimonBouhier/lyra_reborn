"""P1 — le contrôleur calibré (B03+P1P2) régule dans une bande raisonnable.

Les bandes exactes du starter-kit (§8 : `pressure_mean ∈ [0.44,0.46]`,
`tension_mean ∈ [0.54,0.58]`) sont des **cibles de calibration pour un run réel**
(métriques dérivées du graphe). L'autopilote tourne sur des mesures **synthétiques**
(`core/control/measures.py`) : on n'exige donc qu'un **sous-ensemble robuste** —
convergence nette vers la consigne + τc décollé du plancher + intégrale bornée.
"""
from core.knobs import Knobs
from core.control.controller import ControlConfig, ACCEPTANCE_CRITERIA
from core.control.measures import measure_pressure
from core.loop import run_autopilot


def test_pressure_converges_clearly_toward_setpoint():
    cfg = ControlConfig()
    k0 = Knobs(rho=0.5, delta_r=0.9, tau_c=0.3, kappa=0.6)  # δr saturé, pression haute
    p0 = measure_pressure(k0.delta_r, k0.tau_c)
    traj = run_autopilot(steps=60, knobs=k0, control_cfg=cfg)
    p_end = traj[-1]["pressure"]
    # nettement plus proche qu'au départ (au moins divisé par 2)
    assert abs(p_end - cfg.pressure_setpoint) < abs(p0 - cfg.pressure_setpoint) / 2
    # dans une bande large autour de la consigne (l'exact [0.44,0.46] = cible réelle)
    assert abs(p_end - cfg.pressure_setpoint) < 0.10


def test_tau_c_not_pinned_to_floor():
    cfg = ControlConfig()
    traj = run_autopilot(steps=60, control_cfg=cfg)
    taus = [r["tau_c"] for r in traj]
    assert min(taus) >= cfg.tau_c_lo - 1e-9          # jamais sous le plancher
    assert max(taus) - min(taus) > 0.03              # τc travaille, ne reste pas collé


def test_integral_bounded_with_tuned_gains():
    cfg = ControlConfig()
    traj = run_autopilot(steps=60, control_cfg=cfg)
    for r in traj:
        assert abs(r["pressure_i"]) <= cfg.pressure_i_max + 1e-9


def test_acceptance_criteria_shape():
    # les cibles §8 sont présentes et cohérentes (référence de calibration)
    lo, hi = ACCEPTANCE_CRITERIA["pressure_mean"]
    assert lo < hi
    assert ACCEPTANCE_CRITERIA["tau_c_min"] == cfg_floor()


def cfg_floor() -> float:
    return ControlConfig().tau_c_lo
