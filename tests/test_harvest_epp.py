"""Récolte EPP_Verdict : Jaro-Winkler stdlib, groupes de relations, cascade."""
from explore.esmm.textsim import jaro, jaro_winkler
from explore.esmm.relations import canonical_relation, relations_compatible
from explore.esmm.consensus import vote
from explore.esmm.triplets import extract_triplets
import json


# ------------------------------------------------- Jaro-Winkler (réf. classiques)

def test_jaro_winkler_reference_values():
    assert abs(jaro_winkler("martha", "marhta") - 0.9611) < 0.001
    assert abs(jaro_winkler("dwayne", "duane") - 0.8400) < 0.001
    assert abs(jaro("dixon", "dicksonx") - 0.7667) < 0.001
    assert jaro_winkler("a", "a") == 1.0
    assert jaro_winkler("", "abc") == 0.0
    assert jaro_winkler("abc", "xyz") == 0.0


def test_division_of_labor_accents_vs_typos():
    """Mesuré : les accents tombent SOUS le seuil JW 0.9 (0.877) — c'est donc
    match_key (pliage des diacritiques) qui les prend, en EXACT et gratuit.
    L'étage JW attrape les vraies coquilles proches."""
    from explore.esmm.triplets import match_key
    # accents : match_key les rend identiques
    assert match_key("géométrie fractale") == match_key("geometrie fractale")
    assert match_key("récursivité") == match_key("recursivite")
    # coquilles : JW > 0.9 (l'étage de la cascade)
    assert jaro_winkler("sierpinski", "sierpinsky") > 0.9
    assert jaro_winkler("mandelbrot", "mandelbrodt") > 0.9
    # ... sans fusionner des concepts distincts
    assert jaro_winkler("fractale", "mathematiques") < 0.9


# ------------------------------------------------- groupes de relations

def test_canonical_relation_folds_synonyms():
    assert canonical_relation("type_of") == "est_un"
    assert canonical_relation("IS_A") == "est_un"
    assert canonical_relation("fait partie de") == "partie_de"
    assert canonical_relation("leads_to") == "cause"
    assert canonical_relation("depends_on") == "utilise"   # choix EPP ADR-006 adapté
    assert canonical_relation("contredit") == "oppose_a"
    # inconnu : renvoyé normalisé, jamais perdu
    assert canonical_relation("Frôle De Près") == "frôle_de_près"


def test_relations_compatible_group_then_jw():
    assert relations_compatible("est_un", "kind_of") is True       # même groupe
    assert relations_compatible("cause", "causes") is True         # même groupe
    assert relations_compatible("est_un", "cause") is False        # groupes ≠, JW bas
    assert relations_compatible("propriete_de", "propriété_de") is True


# ------------------------------------------------- cascade dans le consensus

def _ext(model, trips):
    return extract_triplets(model, json.dumps(
        {"triplets": [{"sujet": s, "predicat": p, "objet": o} for s, p, o in trips]}))


def test_consensus_jw_tier_clusters_accent_variants_without_embeddings():
    e1 = _ext("m1", [("fractale", "lie_a", "geometrie fractale")])
    e2 = _ext("m2", [("fractale", "lie_a", "géométrie fractale")])
    res = vote([e1, e2], min_agree=2)          # AUCUN matcher sémantique fourni
    assert len(res.accepted) == 1
    assert res.accepted[0].supporters == ["m1", "m2"]
    assert res.accepted[0].level == "exact"


def test_consensus_predicate_folding_upgrades_to_exact():
    # « est_un » (fr) et « type_of » (en) = même canonique → niveau exact
    e1 = _ext("m1", [("fractale", "est_un", "objet mathématique")])
    e2 = _ext("m2", [("fractale", "type_of", "objet mathématique")])
    res = vote([e1, e2], min_agree=2)
    assert len(res.accepted) == 1
    ct = res.accepted[0]
    assert ct.level == "exact"
    assert ct.triplet.predicate == "est_un"    # le canonique, pas la variante
