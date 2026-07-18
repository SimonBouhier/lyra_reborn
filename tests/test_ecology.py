"""P3 — écologie mémorielle : triage, différé, réveil ; les 4 bugs LyrArc exclus."""
import pytest

from memory.ecology.ecology import MemoryEcology, Strate


def _eco() -> MemoryEcology:
    e = MemoryEcology(nursery_threshold=0.6, compost_threshold=0.05,
                      defer_ms=1000, max_defers=2)
    e.set_clock(0)
    return e


def test_triage_three_strata():
    e = _eco()
    assert e.triage("fort", "…", 0.9) is Strate.POUPONNIERE
    assert e.triage("moyen", "…", 0.3) is Strate.OUBLI
    assert e.triage("nul", "…", 0.0) is Strate.COMPOST
    assert e.counts() == {"pouponniere": 1, "oubli": 1, "compost": 1}


def test_score_history_append_only():
    # bug #2 LyrArc : scores écrasés à 0.0 à la relecture — ici, append-only
    e = _eco()
    e.triage("x", "…", 0.3)
    e.set_clock(1000)
    e.revisit_due(lambda it: 0.7)      # réévalué à la hausse
    it = e.items["x"]
    assert [s for _, s in it.score_history] == [0.3, 0.7]
    assert it.score == 0.7


def test_deferred_revisit_promotes():
    e = _eco()
    e.triage("x", "…", 0.3)            # → journal d'oubli, échéance à t=1000
    assert e.revisit_due(lambda it: 0.9) == []      # pas encore dû : rien (explicite)
    e.set_clock(1000)
    trans = e.revisit_due(lambda it: 0.9)
    assert trans == [("x", Strate.OUBLI, Strate.POUPONNIERE)]


def test_max_defers_leads_to_compost():
    e = _eco()
    e.triage("x", "…", 0.3)
    e.set_clock(1000)
    assert e.revisit_due(lambda it: 0.3) == []      # score toujours partiel : re-différé
    assert e.items["x"].defers == 1
    e.set_clock(2000)
    trans = e.revisit_due(lambda it: 0.3)           # 2e report = max → compost
    assert trans == [("x", Strate.OUBLI, Strate.COMPOST)]


def test_compost_wake_and_full_revival_cycle():
    # « réveil des tâches mortes » : un item composté peut revivre entièrement
    e = _eco()
    e.triage("mort", "…", 0.0)
    assert e.items["mort"].strate is Strate.COMPOST
    e.wake_from_compost("mort")
    assert e.items["mort"].strate is Strate.OUBLI
    assert e.items["mort"].revivals == 1
    e.set_clock(1000)
    trans = e.revisit_due(lambda it: 0.95)
    assert trans == [("mort", Strate.OUBLI, Strate.POUPONNIERE)]
    # réveiller un item non composté échoue bruyamment
    with pytest.raises(KeyError):
        e.wake_from_compost("mort")


def test_indexes_are_real_sets_and_flat_storage():
    # bugs #3 et #4 LyrArc : stockage plat + index en vrais sets
    e = _eco()
    e.triage("x", {"payload": 1}, 0.9)
    assert isinstance(e.index[Strate.POUPONNIERE], set)
    assert e.items["x"].content == {"payload": 1}   # pas de wrapper de wrapper
    # re-trier un item ne le duplique pas
    e.triage("x", {"payload": 1}, 0.2)
    assert e.counts() == {"pouponniere": 0, "oubli": 1, "compost": 0}


def test_persistence_roundtrip():
    e = _eco()
    e.triage("a", "…", 0.9)
    e.triage("b", "…", 0.3)
    e2 = MemoryEcology.from_dict(e.to_dict())
    assert e2.counts() == e.counts()
    assert e2.items["b"].strate is Strate.OUBLI
    assert e2.items["a"].score == 0.9
