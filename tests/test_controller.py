"""P1 — contrôleur P+I : régulation réelle + anti-windup borné.

Preuve de la loi de commande sur la dynamique synthétique (autopilote) :
partant d'un δr saturé (pression trop haute), le contrôleur ramène la pression
vers sa consigne et désature δr, sans jamais laisser l'intégrale sortir de ses
bornes. (Reproduit l'esprit du run A02 de l'audit : désaturation en ~30 pas.)
"""
from core.knobs import Knobs
from core.control.controller import ControlConfig
from core.control.measures import measure_pressure
from core.loop import run_autopilot


def test_pi_regulates_pressure_toward_setpoint():
    cfg = ControlConfig()
    k0 = Knobs(rho=0.5, delta_r=0.9, tau_c=0.3, kappa=0.6)  # δr saturé
    p0 = measure_pressure(k0.delta_r, k0.tau_c)             # pression initiale (haute)
    traj = run_autopilot(steps=40, knobs=k0, control_cfg=cfg)

    p_end = traj[-1]["pressure"]
    # la pression finale est plus proche de la consigne qu'au départ
    assert abs(p_end - cfg.pressure_setpoint) < abs(p0 - cfg.pressure_setpoint)
    # δr a bien été désaturé
    assert traj[-1]["delta_r"] < k0.delta_r


def test_integral_stays_bounded():
    cfg = ControlConfig()
    traj = run_autopilot(steps=60, control_cfg=cfg)
    for row in traj:
        assert abs(row["pressure_i"]) <= cfg.pressure_i_max + 1e-9
