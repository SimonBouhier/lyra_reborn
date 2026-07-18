"""P2 — le pont : signaux épistémiques réels + régulation P+I de la vraie boucle."""
import os
import pytest

from core.control.bridge import EpistemicBridge
from core.control.controller import PIController, ControlConfig
from core.knobs import Knobs
from core.llm import EchoClient
from core.loop import LyraLoop
from core.state import CognitiveState
from core.config import SmoothingConfig
from core.metrics.cheap import hedge_score


def _cheap(prompt, output, truncated=False):
    d = hedge_score(prompt, output)
    d["truncated"] = float(truncated)
    return d


def test_signals_in_range_and_directionally_correct():
    b = EpistemicBridge()
    opts = {"num_predict": 100}

    struct_out = "# Plan\n- point un du plan\n- point deux du plan\n- conclusion nette\n"
    repet_out = "le même segment répété encore " * 8
    e_struct = b.derive(struct_out, opts, _cheap("fais un plan structuré", struct_out))
    e_repet = b.derive(repet_out, opts, _cheap("fais un plan structuré", repet_out))

    for e in (e_struct, e_repet):
        for k in ("coherence", "fit", "pressure", "tension"):
            assert 0.0 <= e[k] <= 1.0
    # un texte structuré est plus cohérent qu'un texte qui s'emballe
    assert e_struct["coherence"] > e_repet["coherence"]


def test_pressure_is_budget_utilization():
    b = EpistemicBridge()
    out = "dix mots exactement pour tester la pression du budget ici"
    e_small = b.derive(out, {"num_predict": 20}, _cheap("q", out))
    e_big = b.derive(out, {"num_predict": 2000}, _cheap("q", out))
    assert e_small["pressure"] > e_big["pressure"]   # même sortie, budget serré ⇒ pression haute
    assert e_big["pressure"] < 0.02


def test_truncation_penalizes_fit():
    b = EpistemicBridge()
    out = "réponse coupée en plein"
    opts = {"num_predict": 100}
    e_ok = b.derive(out, opts, _cheap("question réponse coupée", out, truncated=False))
    e_tr = b.derive(out, opts, _cheap("question réponse coupée", out, truncated=True))
    assert e_tr["fit"] < e_ok["fit"]


def test_bridged_loop_regulates_delta_r_upward_on_low_pressure():
    """EchoClient produit ~10 tokens pour un budget de ~700 ⇒ pression ≈ 0 ⇒ le
    P+I doit OUVRIR δr (plus de budget) au fil des tours — régulation réelle."""
    loop = LyraLoop(EchoClient(), state=CognitiveState(),
                    smoothing=SmoothingConfig(refractory_ms=0, hysteresis_eps=0.0),
                    controller=PIController(ControlConfig()))
    dr0 = loop.state.knobs.delta_r
    for _ in range(6):
        res = loop.generate("Explique un concept en détail.")
    assert res.epistemic is not None
    assert res.epistemic["pressure"] < 0.1
    assert loop.state.knobs.delta_r > dr0        # δr s'est ouvert


def test_responsibility_split_pi_vs_reactive():
    """κ reste piloté par le réactif (aucune répétition ⇒ κ immobile), pendant
    que δr/τc bougent sous le P+I : un seul pilote par bouton."""
    loop = LyraLoop(EchoClient(), state=CognitiveState(),
                    smoothing=SmoothingConfig(refractory_ms=0, hysteresis_eps=0.0),
                    controller=PIController(ControlConfig()))
    k0 = loop.state.knobs.kappa
    dr0 = loop.state.knobs.delta_r
    for _ in range(4):
        loop.generate("Analyse posée et directe.")
    assert abs(loop.state.knobs.kappa - k0) < 1e-9
    assert loop.state.knobs.delta_r != dr0


def test_pi_moves_delta_r_even_with_default_hysteresis():
    """Régression (constatée en live 2026-07-18) : avec l'hystérésis PAR DÉFAUT
    (0.05), les petits pas du P+I (~0.02/tour) étaient bloqués ⇒ δr/τc figés.
    Le mode pont applique désormais δr/τc directement : ils doivent bouger."""
    loop = LyraLoop(EchoClient(), state=CognitiveState(),
                    smoothing=SmoothingConfig(refractory_ms=0),  # hysteresis 0.05 par défaut
                    controller=PIController(ControlConfig()))
    dr0 = loop.state.knobs.delta_r
    for _ in range(4):
        loop.generate("Développe le sujet en profondeur.")
    assert loop.state.knobs.delta_r != dr0       # plus jamais figé par la zone morte


def test_without_controller_behavior_unchanged():
    loop = LyraLoop(EchoClient(), state=CognitiveState(),
                    smoothing=SmoothingConfig(refractory_ms=0))
    res = loop.generate("Question simple.")
    assert res.epistemic is None                 # pas de pont ⇒ pas de signaux


@pytest.mark.skipif(not os.getenv("LYRA_LIVE"), reason="nécessite Ollama (LYRA_LIVE=1)")
def test_live_bridge_on_real_model():
    """Smoke réel : un tour sur Ollama, signaux dérivés d'une vraie génération."""
    from core.llm import OllamaClient
    loop = LyraLoop(OllamaClient(), state=CognitiveState(),
                    smoothing=SmoothingConfig(refractory_ms=0),
                    controller=PIController(ControlConfig()))
    res = loop.generate("Explique en trois points courts ce qu'est la récursivité.")
    assert res.output.strip()                    # vraie génération non vide
    assert res.epistemic is not None
    for k in ("coherence", "fit", "pressure", "tension"):
        assert 0.0 <= res.epistemic[k] <= 1.0
    assert res.modulated is True
