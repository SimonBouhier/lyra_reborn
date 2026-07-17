"""P0 — mapping des boutons : monotonie, bornes, clamps."""
from core.knobs import Knobs, KnobMapping, clamp01


def test_clamp01():
    assert clamp01(-1) == 0.0
    assert clamp01(2) == 1.0
    assert clamp01(0.5) == 0.5


def test_knobs_clamped():
    k = Knobs(rho=1.5, delta_r=-0.2, tau_c=0.5, kappa=2.0).clamped()
    assert (k.rho, k.delta_r, k.tau_c, k.kappa) == (1.0, 0.0, 0.5, 1.0)


def test_mapping_monotone_temperature():
    m = KnobMapping()
    lo = m.to_generation_options(Knobs(tau_c=0.0))["temperature"]
    hi = m.to_generation_options(Knobs(tau_c=1.0))["temperature"]
    assert lo < hi
    assert m.temperature_min <= lo <= m.temperature_max
    assert m.temperature_min <= hi <= m.temperature_max


def test_mapping_keys_and_bounds():
    m = KnobMapping()
    o = m.to_generation_options(Knobs(rho=0.5, delta_r=0.5, tau_c=0.5, kappa=0.5))
    assert set(o) == {"temperature", "top_p", "repeat_penalty", "num_predict"}
    assert isinstance(o["num_predict"], int)
    assert m.num_predict_min <= o["num_predict"] <= m.num_predict_max
