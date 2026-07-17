"""P1 — garde-fous : zone morte (hystérésis), clamp, période réfractaire."""
from core.state import CognitiveState
from core.knobs import Knobs
from core.config import SmoothingConfig
from core.control.guards import clamp_and_hysteresis, refractory_ok


def test_hysteresis_dead_zone_keeps_current():
    st = CognitiveState(knobs=Knobs(rho=0.50, delta_r=0.50, tau_c=0.50, kappa=0.50))
    sm = SmoothingConfig(hysteresis_eps=0.05)
    # cible à +0.02 (< eps) sur rho => inchangé ; +0.20 sur tau_c (> eps) => bouge
    target = {"rho": 0.52, "delta_r": 0.50, "tau_c": 0.70, "kappa": 0.50}
    out = clamp_and_hysteresis(st, target, sm)
    assert out["rho"] == 0.50       # zone morte
    assert out["tau_c"] == 0.70     # au-delà de la zone morte


def test_clamp_bounds():
    st = CognitiveState(knobs=Knobs(rho=0.5, delta_r=0.5, tau_c=0.5, kappa=0.5))
    sm = SmoothingConfig(hysteresis_eps=0.0)
    out = clamp_and_hysteresis(st, {"rho": 2.0, "delta_r": -1.0, "tau_c": 0.5, "kappa": 0.5}, sm)
    assert out["rho"] == 1.0
    assert out["delta_r"] == 0.0


def test_refractory_period():
    st = CognitiveState()
    st.last_update_ms = 1000
    sm = SmoothingConfig(refractory_ms=1200)
    st.set_clock(1000 + 1199)
    assert refractory_ok(st, sm) is False
    st.set_clock(1000 + 1200)
    assert refractory_ok(st, sm) is True
