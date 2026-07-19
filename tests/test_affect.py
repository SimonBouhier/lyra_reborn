"""Surface affective : valence dérivée des signaux réels, affichage sans pilotage."""
from core.affect import AffectiveSurface
from core.llm import EchoClient
from core.loop import LyraLoop
from core.state import CognitiveState
from core.config import SmoothingConfig


def test_derive_maps_real_signals_with_sketch_weights():
    s = AffectiveSurface()
    high = s.derive({"fit": 0.8, "coherence": 0.9, "tension": 0.3})
    low = s.derive({"fit": 0.1, "coherence": 0.2, "tension": 0.9})
    assert high["joy"] > low["joy"]
    assert low["tension"] > high["tension"]
    # poids de l'esquisse : joy = 0.6*fit + 0.4*coherence
    assert abs(high["joy"] - (0.6 * 0.8 + 0.4 * 0.9)) < 1e-6
    for v in (*high.values(), *low.values()):
        assert 0.0 <= v <= 1.0


def test_surface_appended_when_enabled_absent_by_default():
    on = LyraLoop(EchoClient(), state=CognitiveState(),
                  smoothing=SmoothingConfig(refractory_ms=0),
                  enable_affective_surface=True)
    res = on.generate("Explique la récursivité simplement.")
    assert res.affect is not None
    assert "[affect] joy=" in res.output and "tension=" in res.output

    off = LyraLoop(EchoClient(), state=CognitiveState(),
                   smoothing=SmoothingConfig(refractory_ms=0))
    res_off = off.generate("Explique la récursivité simplement.")
    assert res_off.affect is None
    assert "[affect]" not in res_off.output


def test_affect_is_readout_not_a_second_pilot():
    """La surface ne touche PAS aux options de génération : mêmes boutons,
    mêmes options, avec ou sans surface (« un pilote par bouton »)."""
    a = LyraLoop(EchoClient(), state=CognitiveState(),
                 smoothing=SmoothingConfig(refractory_ms=0),
                 enable_affective_surface=True)
    b = LyraLoop(EchoClient(), state=CognitiveState(),
                 smoothing=SmoothingConfig(refractory_ms=0))
    ra = a.generate("Même prompt exactement.")
    rb = b.generate("Même prompt exactement.")
    assert ra.options == rb.options
    # et la partie générée (avant la surface) est identique
    assert ra.output.split("\n\n[affect]")[0] == rb.output
