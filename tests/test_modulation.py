"""P1 — LA preuve de modulation (charte §3).

Boutons différents ⇒ options de génération différentes ⇒ sortie (face-modèle)
différente. C'est le test qui interdit la « modulation illusoire » constatée
dans Lyra_Core (où seul τc agissait).
"""
from core.knobs import Knobs, KnobMapping
from core.llm import EchoClient
from core.state import CognitiveState
from core.config import SmoothingConfig
from core.loop import LyraLoop


def test_different_knobs_yield_different_options():
    m = KnobMapping()
    o1 = m.to_generation_options(Knobs(rho=0.2, delta_r=0.2, tau_c=0.1, kappa=0.2))
    o2 = m.to_generation_options(Knobs(rho=0.9, delta_r=0.9, tau_c=0.9, kappa=0.9))
    assert o1 != o2
    for key in ("temperature", "top_p", "repeat_penalty", "num_predict"):
        assert o1[key] != o2[key]


def test_modulation_changes_model_facing_output():
    m = KnobMapping()
    echo = EchoClient()
    o1 = m.to_generation_options(Knobs(tau_c=0.1))
    o2 = m.to_generation_options(Knobs(tau_c=0.9))
    out1 = echo.generate("même prompt", o1)
    out2 = echo.generate("même prompt", o2)
    assert out1 != out2  # la modulation atteint réellement le modèle


def test_loop_runs_and_modulates():
    # refractory=0 pour forcer une re-modulation en un seul tour
    loop = LyraLoop(EchoClient(), state=CognitiveState(),
                    smoothing=SmoothingConfig(refractory_ms=0))
    res = loop.generate("Explique la récursivité avec un exemple.", task_type="focused")
    assert res.output  # non vide
    assert set(res.options) == {"temperature", "top_p", "repeat_penalty", "num_predict"}
    assert res.modulated is True
    # les overrides de tâche 'focused' se reflètent dans les boutons utilisés
    assert res.knobs_used["kappa"] == 0.70


def test_task_overrides_do_not_leak_into_persistent_state():
    """Réalignement 2026-07-18 : les masques de tâche ne contaminent pas la base.

    Sous le design hérité du canon, des tours répétés en 'focused' (kappa
    override = 0.70) tiraient l'état persistant vers 0.70 via l'EWMA. Désormais
    la politique réactive module l'état de base : sans répétitions détectées,
    kappa n'a aucune raison de bouger.
    """
    loop = LyraLoop(EchoClient(), state=CognitiveState(),
                    smoothing=SmoothingConfig(refractory_ms=0))
    k0 = loop.state.knobs.kappa  # 0.60 par défaut
    for _ in range(5):
        res = loop.generate("Analyse ce point précis maintenant.", task_type="focused")
        assert res.modulated is True
        assert res.knobs_used["kappa"] == 0.70  # le masque s'applique bien au tour
    # ... mais la base n'a pas dérivé vers le masque
    assert abs(loop.state.knobs.kappa - k0) < 1e-9
