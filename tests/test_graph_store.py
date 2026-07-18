"""P3 — nemeton : mutations, deltas/rollback, bornes bruyantes, primitif k=2."""
import pytest

from memory.graph.store import GraphStore, GraphLimitExceeded
from memory.graph.injector import inject


def _mini() -> GraphStore:
    g = GraphStore()
    for cid in ("a", "b", "c", "d"):
        g.upsert_node(cid, "concept")
    g.add_edge("a", "b")
    g.add_edge("b", "c")
    return g


def test_basic_and_degree_single_path():
    g = _mini()
    assert g.counts() == {"nodes": 4, "edges": 2}
    # LE degré = taille de l'adjacence (pas de compteur parallèle à désynchroniser)
    assert g.degree("b") == 2
    assert g.degree("d") == 0
    # renforcement : re-poser l'arête incrémente le count
    assert g.add_edge("a", "b") == 2


def test_rollback_restores_exact_state():
    g = _mini()
    before = g.snapshot()
    g.upsert_node("e", "concept")
    g.add_edge("e", "a")
    g.add_edge("a", "b")     # renforcement (count 1→2)
    g.remove_edge("b", "c")
    assert g.rollback(4) == 4
    assert g.snapshot() == before  # état strictement identique


def test_limits_fail_loudly():
    g = GraphStore(max_nodes=2)
    g.upsert_node("a", "concept")
    g.upsert_node("b", "concept")
    with pytest.raises(GraphLimitExceeded):
        g.upsert_node("c", "concept")
    # pas de création implicite de nœud par une arête
    g2 = _mini()
    with pytest.raises(KeyError):
        g2.add_edge("a", "zzz")


def test_novel_link_k2_local():
    g = _mini()   # a-b, b-c ; d isolé
    assert g.is_novel_link("a", "d") is True          # aucun chemin
    assert g.is_novel_link("a", "b") is False         # arête directe
    assert g.is_novel_link("a", "c") is False         # voisin commun (b) à k=2
    # garde-fou hub : si b est traité comme hub, a-c redevient « neuf »
    assert g.is_novel_link("a", "c", hub_degree_cap=1) is True


def test_compact_prunes_weak_edges():
    g = _mini()
    g.add_edge("a", "b")          # a-b renforcée (count 2) ; b-c reste à 1
    removed = g.compact(min_count=2)
    assert removed == 1
    assert g.edge("b", "c") is None
    assert g.edge("a", "b") is not None


def test_snapshot_bounded_and_roundtrip():
    g = _mini()
    s = g.snapshot()
    g2 = GraphStore.from_snapshot(s)
    assert g2.counts() == g.counts()
    assert g2.edge("a", "b").count == g.edge("a", "b").count
    with pytest.raises(GraphLimitExceeded):
        g.snapshot(max_bytes=10)   # refuse de produire un monstre


def test_injector_bounded_and_non_empty():
    g = _mini()
    txt = inject(g, max_chars=200)
    assert txt.startswith("[NEMETON]")
    assert len(txt) <= 200
    assert "4 concepts" in txt
    assert inject(GraphStore()) == "[NEMETON] graphe vide."
