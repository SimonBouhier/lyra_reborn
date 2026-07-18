"""P3 — Memento/CBR : rappel par similarité + navigateur à 4 stratégies."""
from memory.graph.store import GraphStore
from memory.cbr.memento import Memento, Case, Navigator


def _bank() -> Memento:
    m = Memento()
    m.add_case(Case("calme", {"coherence": 0.9, "fit": 0.8, "pressure": 0.3,
                              "tension": 0.3, "delta_r": 0.3, "tau_c": 0.2},
                    outcome={"fav_node": "N_calme"}))
    m.add_case(Case("tendu", {"coherence": 0.3, "fit": 0.3, "pressure": 0.9,
                              "tension": 0.9, "delta_r": 0.8, "tau_c": 0.9},
                    outcome={"fav_node": "N_tendu"}))
    return m


def _graph() -> GraphStore:
    g = GraphStore()
    g.upsert_node("P_rigor", "persona", {"style": "rigor"})
    g.upsert_node("P_fun", "persona", {"style": "playful"})
    g.upsert_node("I_new", "intent", {"novelty": 0.8})
    g.upsert_node("I_old", "intent", {"novelty": 0.1})
    g.upsert_node("N_calme", "concept")
    return g


def test_retrieve_nearest_by_cosine():
    m = _bank()
    hot = {"coherence": 0.35, "fit": 0.3, "pressure": 0.85, "tension": 0.88,
           "delta_r": 0.75, "tau_c": 0.85}
    top = m.retrieve(hot, k=1)
    assert top[0][0].id == "tendu"
    assert top[0][1] > 0.95


def test_strategies_target_the_right_nodes():
    nav = Navigator(_graph(), _bank())
    s = nav.suggest({}, strategy="stabilize")
    assert s.next_targets == ["P_rigor"]           # style rigor seulement
    s = nav.suggest({}, strategy="explore")
    assert s.next_targets == ["I_new"]             # novelty > 0.5 seulement


def test_case_guided_returns_explicit_retrievals():
    nav = Navigator(_graph(), _bank())
    calm = {"coherence": 0.85, "fit": 0.8, "pressure": 0.3, "tension": 0.3,
            "delta_r": 0.3, "tau_c": 0.25}
    s = nav.suggest(calm, k=2, strategy="case_guided")
    assert s.retrieved and s.retrieved[0][0] == "calme"   # champ explicite (bug Uni exclu)
    assert "N_calme" in s.next_targets


def test_case_guided_empty_bank_is_explicit_not_silent():
    nav = Navigator(_graph(), Memento())
    s = nav.suggest({}, strategy="case_guided")
    assert "vide" in s.reason
    assert s.next_targets == [] and s.retrieved == []


def test_balanced_fallback_fills_targets():
    nav = Navigator(_graph())
    s = nav.suggest({}, k=3, strategy="balanced")
    assert len(s.next_targets) == 3
