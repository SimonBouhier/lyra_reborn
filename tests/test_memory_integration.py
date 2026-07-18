"""P3 — intégration : un mini-scénario où graphe + écologie + CBR coopèrent.

Anti « vert mais vide » : à la fin du scénario, le graphe est NON VIDE, un item
composté a été réveillé, et le rappel par cas retrouve l'épisode pertinent.
"""
from memory.graph.store import GraphStore
from memory.graph.injector import inject
from memory.ecology.ecology import MemoryEcology, Strate
from memory.cbr.memento import Memento, Case, Navigator


def test_full_memory_scenario():
    g = GraphStore()
    eco = MemoryEcology(defer_ms=1000)
    eco.set_clock(0)
    cbr = Memento()

    # 1) trois tours de conversation déposent des concepts + co-occurrences
    for turn, concepts in enumerate([("récursivité", "pile"),
                                     ("récursivité", "fractale"),
                                     ("fractale", "pile")]):
        for c in concepts:
            if g.node(c) is None:
                g.upsert_node(c, "concept")
        g.add_edge(*concepts)
        # chaque tour est trié dans l'écologie selon sa qualité mesurée
        eco.triage(f"tour_{turn}", {"concepts": concepts},
                   score=[0.9, 0.3, 0.0][turn])
        # ... et mémorisé comme cas
        cbr.add_case(Case(f"tour_{turn}",
                          {"coherence": 0.9 - 0.3 * turn, "tension": 0.3 + 0.3 * turn},
                          outcome={"fav_node": concepts[0]}))

    # 2) le graphe est réellement peuplé (anti-vide) et l'injection le résume
    assert g.counts() == {"nodes": 3, "edges": 3}
    assert "3 concepts" in inject(g)

    # 3) l'écologie a trié : 1 pouponnière, 1 journal, 1 compost
    assert eco.counts() == {"pouponniere": 1, "oubli": 1, "compost": 1}

    # 4) réveil du tour composté ; à t=1000, tour_1 (au journal depuis t=0) est
    #    AUSSI à échéance — les deux sont réévalués favorablement → pouponnière
    eco.wake_from_compost("tour_2")
    eco.set_clock(1000)
    trans = eco.revisit_due(lambda it: 0.8)
    assert ("tour_2", Strate.OUBLI, Strate.POUPONNIERE) in trans
    assert ("tour_1", Strate.OUBLI, Strate.POUPONNIERE) in trans
    assert eco.counts() == {"pouponniere": 3, "oubli": 0, "compost": 0}

    # 5) le CBR retrouve l'épisode calme pour un état calme
    nav = Navigator(g, cbr)
    s = nav.suggest({"coherence": 0.85, "tension": 0.3}, k=1, strategy="case_guided")
    assert s.retrieved[0][0] == "tour_0"
    assert s.next_targets == ["récursivité"]
