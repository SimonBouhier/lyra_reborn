"""P2 (acompte) — politique de phase λ : déclenchement + cooldown."""
from core.control.phase import PolicyLambda, LambdaConfig


def test_lambda_triggers_above_threshold_and_boosts_tau():
    lam = PolicyLambda(LambdaConfig(threshold=0.90, tau_gain=1.04, tau_bias=0.015, cooldown=5))
    active, tau = lam.step(coherence=0.95, tau_c=0.30)
    assert active is True
    assert tau > 0.30  # léger boost


def test_lambda_cooldown_prevents_flapping():
    lam = PolicyLambda(LambdaConfig(threshold=0.90, cooldown=3))
    lam.step(coherence=0.95, tau_c=0.30)      # entre en phase λ
    active, _ = lam.step(coherence=0.10, tau_c=0.30)  # sortie -> démarre le cooldown
    assert active is False
    # pendant le cooldown, même une cohérence haute ne réactive pas immédiatement
    active2, _ = lam.step(coherence=0.99, tau_c=0.30)
    assert active2 is False
