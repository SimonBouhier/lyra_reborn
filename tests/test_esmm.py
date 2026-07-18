"""P4 — ESMM : extraction stricte, lacunes, consensus par-modèle, run anti-vide."""
import json
import pytest

from memory.graph.store import GraphStore
from explore.esmm.triplets import extract_triplets, Triplet
from explore.esmm.gaps import GapDetector
from explore.esmm.consensus import vote
from explore.esmm.orchestrator import EsmmOrchestrator, EsmmEmptyRun


# ---------------------------------------------------------------- extraction

def test_extract_valid_json_fr_and_en_keys():
    txt = 'Voici : {"triplets": [{"sujet": "fractale", "predicat": "modélise", "objet": "récursivité"}, {"subject": "graphe", "predicate": "contient", "object": "concepts"}]}'
    ext = extract_triplets("m1", txt)
    assert len(ext.triplets) == 2
    assert ext.errors == []


def test_extract_failures_are_counted_never_swallowed():
    assert extract_triplets("m", "").errors == ["réponse vide"]
    assert "aucun JSON" in extract_triplets("m", "pas de json ici").errors[0]
    assert "JSON invalide" in extract_triplets("m", '{"triplets": [oops}').errors[0]
    ext = extract_triplets("m", '{"triplets": [{"sujet": "a", "predicat": "", "objet": "b"}]}')
    assert ext.triplets == [] and "incomplet" in ext.errors[0]


def test_signature_is_normalization_invariant():
    a = Triplet("  Fractale ", "MODÉLISE", "récursivité.")
    b = Triplet("fractale", "modélise", "récursivité")
    assert a.signature() == b.signature()


# ---------------------------------------------------------------- lacunes

def test_gap_taxonomy():
    g = GraphStore()
    for c in ("seul", "pont", "x", "y", "faible", "z", "c1", "c2"):
        g.upsert_node(c, "concept")
    # pont : x-pont-y sans lien x-y ; renforcées pour ne pas être 'unstable'
    g.add_edge("pont", "x"); g.add_edge("pont", "x")
    g.add_edge("pont", "y"); g.add_edge("pont", "y")
    # faible : un seul lien à count=1
    g.add_edge("faible", "z")
    # contradiction
    g.add_edge("c1", "c2", type="conflicts_with")
    types = {(gap.type, gap.node_id) for gap in GapDetector(g).detect(limit=20)}
    assert ("isolated", "seul") in types
    assert ("bridge", "pont") in types
    assert ("unstable", "faible") in types
    assert ("contradiction", "c1") in types


# ---------------------------------------------------------------- consensus

def _ext(model, trips):
    return extract_triplets(model, json.dumps(
        {"triplets": [{"sujet": s, "predicat": p, "objet": o} for s, p, o in trips]}))


def test_consensus_requires_min_agree_distinct_models():
    e1 = _ext("m1", [("a", "lie", "b"), ("a", "lie", "c")])
    e2 = _ext("m2", [("a", "lie", "b")])
    e3 = _ext("m3", [("x", "lie", "y")])
    res = vote([e1, e2, e3], min_agree=2)
    assert len(res.accepted) == 1
    assert res.accepted[0].supporters == ["m1", "m2"]
    assert res.rejected == 2         # (a,lie,c) et (x,lie,y) sous le seuil


def test_one_model_votes_once_even_if_it_repeats():
    e1 = _ext("m1", [("a", "lie", "b"), ("a", "lie", "b"), ("a", "lie", "b")])
    res = vote([e1], min_agree=2)
    assert res.accepted == [] and res.rejected == 1   # 3 répétitions ≠ 3 votes


def test_pair_level_consensus_with_different_predicates():
    """Constat live 2026-07-18 : deux modèles nomment le même LIEN avec des
    prédicats différents ⇒ accord de niveau « pair », prédicat déterministe."""
    e1 = _ext("m1", [("fractale", "est_un", "objet géométrique")])
    e2 = _ext("m2", [("La fractale", "exemple_de", "l'objet géométrique")])  # articles ≠
    res = vote([e1, e2], min_agree=2)
    assert len(res.accepted) == 1
    ct = res.accepted[0]
    assert ct.level == "pair"
    assert ct.supporters == ["m1", "m2"]
    assert ct.triplet.predicate == "est_un"      # départage lexicographique déterministe


def test_exact_level_when_predicates_agree():
    e1 = _ext("m1", [("a", "cause", "b")])
    e2 = _ext("m2", [("a", "cause", "b")])
    res = vote([e1, e2], min_agree=2)
    assert res.accepted[0].level == "exact"


def test_lexical_match_key_catches_hyphen_variants():
    e1 = _ext("m1", [("fractale", "propriete_de", "auto-similarité")])
    e2 = _ext("m2", [("fractale", "propriete_de", "autosimilarité")])
    res = vote([e1, e2], min_agree=2)
    assert len(res.accepted) == 1 and res.accepted[0].level == "exact"


def test_semantic_matcher_clusters_paraphrases():
    """Le matcher (ici factice, en live : cosinus mxbai ≥ 0.78) fusionne les
    objets paraphrasés — le déblocage du consensus inter-modèles constaté."""
    synonyms = {frozenset({"figure géométrique", "forme géométrique"})}

    def fake_matcher(a, b):
        return frozenset({a.lower(), b.lower()}) in synonyms

    e1 = _ext("m1", [("fractale", "est_un", "figure géométrique")])
    e2 = _ext("m2", [("fractale", "est_un", "forme géométrique")])
    e3 = _ext("m3", [("fractale", "partie_de", "mathématiques")])
    res = vote([e1, e2, e3], min_agree=2, matcher=fake_matcher)
    assert len(res.accepted) == 1
    ct = res.accepted[0]
    assert ct.supporters == ["m1", "m2"]
    assert ct.level == "exact"                    # même prédicat des deux côtés
    assert res.rejected == 1                      # mathématiques : 1 seul soutien


def test_parse_errors_surface_in_result():
    bad = extract_triplets("casse", "je ne parle pas JSON")
    res = vote([bad, _ext("ok", [("a", "lie", "b")])], min_agree=2)
    assert "casse" in res.parse_errors


# ---------------------------------------------------------------- orchestrateur

class FakeClient:
    """Client factice : renvoie un JSON déterministe fonction du concept exploré."""
    def __init__(self, style="agree"):
        self.style = style
        self.calls = 0

    def generate(self, prompt, options):
        self.calls += 1
        concept = prompt.split("«")[1].split("»")[0].strip()
        if self.style == "agree":
            return json.dumps({"triplets": [
                {"sujet": concept, "predicat": "est lié à", "objet": f"{concept}_voisin"},
                {"sujet": concept, "predicat": "illustre", "objet": "récursivité"},
            ]})
        if self.style == "garbage":
            return "désolé, je préfère la prose libre."
        return json.dumps({"triplets": [
            {"sujet": concept, "predicat": "contredit", "objet": "autre_chose"}]})


def test_refuses_to_run_on_empty_graph():
    orch = EsmmOrchestrator(GraphStore(), {"m1": FakeClient(), "m2": FakeClient()})
    with pytest.raises(EsmmEmptyRun, match="graine"):
        orch.run(seeds=(), cycles=1)


def test_min_agree_needs_enough_models():
    with pytest.raises(ValueError):
        EsmmOrchestrator(GraphStore(), {"m1": FakeClient()}, min_agree=2)


def test_run_produces_triplets_and_enriches_graph():
    """DoD P4 (plan §6) : accepted > 0, cochain_entries > 0, graphe enrichi."""
    g = GraphStore()
    orch = EsmmOrchestrator(g, {"m1": FakeClient("agree"), "m2": FakeClient("agree"),
                                "m3": FakeClient("garbage")})
    report = orch.run(seeds=["fractale"], cycles=2)
    assert report.accepted > 0
    assert report.cochain_entries > 0
    assert report.nodes_added > 0 and report.edges_added > 0
    assert g.counts()["nodes"] > 1 and g.counts()["edges"] > 0
    # le modèle en panne est diagnostiqué, pas avalé
    assert report.parse_errors.get("m3", 0) > 0
    # la cochaîne épistémique est réellement posée sur les nœuds
    seeded = g.node("fractale")
    assert seeded.data.get("cochain", {}).get("support", 0) > 0
    assert set(seeded.data["cochain"]["sources"]) == {"m1", "m2"}


def test_empty_run_fails_loudly():
    """Anti « vert mais vide » : 0 triplet accepté ⇒ EsmmEmptyRun avec diagnostic."""
    g = GraphStore()
    orch = EsmmOrchestrator(g, {"m1": FakeClient("garbage"), "m2": FakeClient("garbage")})
    with pytest.raises(EsmmEmptyRun, match="0 triplet"):
        orch.run(seeds=["fractale"], cycles=1)
