"""P2 (acompte) — métriques cheap : sanité de base."""
from core.metrics.cheap import (
    repeat4_rate, carryover_intrusion, structure_score, keyword_overlap, hedge_score,
)


def test_repeat4_detects_repetition():
    repet = "le chat noir dort " * 5
    varie = "un texte sans aucune répétition notable de quatre mots consécutifs ici voilà"
    assert repeat4_rate(repet) > 0.0
    assert repeat4_rate(varie) == 0.0


def test_carryover_high_when_same_topic():
    a = "parle-moi des trous noirs et de la relativité"
    b = "encore des trous noirs et la relativité générale"
    c = "donne une recette de tarte aux pommes"
    assert carryover_intrusion(a, b) > carryover_intrusion(a, c)


def test_structure_score_prefers_structured():
    plat = "phrase une. phrase deux. phrase trois."
    struct = "# Titre\n- point un\n- point deux\n- point trois\n"
    assert structure_score(struct) > structure_score(plat)


def test_hedge_score_keys():
    h = hedge_score("question", "# réponse\n- a\n- b")
    assert set(h) >= {"kw_overlap", "repeat4", "struct", "hedge"}
    assert 0.0 <= h["hedge"] <= 1.0
