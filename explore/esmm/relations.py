"""Vocabulaire de relations — groupes de synonymes, source unique de vérité.

Récolte du design `EPP_Verdict/services/esmm/relation_vocabulary.py` (ADR-006 :
« SOURCE OF TRUTH: do NOT define local synonym groups elsewhere »), adapté à nos
canoniques FRANÇAIS (ceux du prompt et du graphe, cf. orchestrator.PREDICATE_VOCAB).

Rôle : les modèles répondent parfois avec des variantes ou de l'anglais
(« type_of », « is_a », « fait partie de »…). Le pliage vers le canonique fait
converger les prédicats AVANT le vote → davantage d'accords de niveau « exact ».
Repli : Jaro-Winkler > 0.9 entre prédicats normalisés (comme EPP)."""
from __future__ import annotations
from typing import Dict, Set

from explore.esmm.textsim import jaro_winkler

# canoniques = nos 8 prédicats (français, snake_case) + synonymes FR/EN.
# Correspondance avec les groupes EPP : USES→utilise, IS_A→est_un,
# PART_OF→partie_de, CAUSES→cause, RELATES_TO/DEPENDS_ON→lie_a,
# PREVENTS→oppose_a, HAS→propriete_de (possession d'attribut), instance_of
# distingué chez nous (exemple_de).
RELATION_GROUPS: Dict[str, Set[str]] = {
    "est_un": {"est_un", "est_une", "est", "is_a", "type_of", "is_type_of",
               "kind_of", "is_kind_of", "sorte_de", "type_de"},
    "partie_de": {"partie_de", "part_of", "component_of", "belongs_to",
                  "member_of", "subset_of", "contained_in", "fait_partie_de",
                  "appartient_a", "compose"},
    "propriete_de": {"propriete_de", "propriété_de", "has", "contains",
                     "includes", "possesses", "a_pour_propriete", "caracterise",
                     "presente", "possede"},
    "cause": {"cause", "causes", "leads_to", "results_in", "produces",
              "triggers", "creates", "generates", "outputs", "provoque",
              "entraine", "produit", "genere", "engendre"},
    "utilise": {"utilise", "uses", "requires", "needs", "employs", "utilizes",
                "emploie", "necessite", "requiert", "depends_on", "relies_on",
                "depend_de", "based_on", "repose_sur"},
    "exemple_de": {"exemple_de", "instance_of", "example_of", "illustre",
                   "illustrates", "exemplifie"},
    "oppose_a": {"oppose_a", "opposé_à", "s_oppose_a", "prevents", "blocks",
                 "inhibits", "contredit", "contradicts", "conflicts_with",
                 "empeche", "bloque"},
    "lie_a": {"lie_a", "lié_à", "relates_to", "related_to", "associated_with",
              "connected_to", "linked_to", "associe_a", "en_relation_avec",
              "connecte_a"},
}

_SYNONYM_MAP: Dict[str, str] = {
    syn: canon for canon, syns in RELATION_GROUPS.items() for syn in syns
}


def _norm(relation: str) -> str:
    return (relation or "").lower().strip().replace("-", "_").replace(" ", "_")


def canonical_relation(relation: str) -> str:
    """Prédicat → forme canonique. Inconnu : renvoyé normalisé tel quel
    (le consensus le traitera comme groupe à lui seul — pas de perte)."""
    return _SYNONYM_MAP.get(_norm(relation), _norm(relation))


def relations_compatible(a: str, b: str, jw_threshold: float = 0.9) -> bool:
    """Même groupe canonique, sinon repli Jaro-Winkler (seuil EPP : 0.9)."""
    ca, cb = canonical_relation(a), canonical_relation(b)
    if ca == cb:
        return True
    return jaro_winkler(ca, cb) > jw_threshold
