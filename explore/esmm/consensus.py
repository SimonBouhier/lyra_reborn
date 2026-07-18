"""Consensus multi-modèles PAR-MODÈLE, à deux niveaux — le cœur de l'ESMM.

Cause racine n°3 du « 0 triplet » historique : le cycle_manager concaténait les
réponses des modèles AVANT le vote — le consensus était court-circuité. Ici, la
structure rend la régression impossible : `vote()` reçoit des `Extraction`
séparées par modèle.

Deux niveaux d'accord (décision datée 2026-07-18, après constat en génération
réelle : 38 propositions / 0 accord exact entre gemma3, mistral et llama3.1 —
les modèles hétérogènes formulent la même connaissance différemment) :
- **exact** : ≥ min_agree modèles distincts proposent le même (sujet, prédicat,
  objet) normalisé ;
- **pair**  : ≥ min_agree modèles distincts proposent le même LIEN (sujet,
  objet), avec des prédicats différents ; le prédicat retenu est le plus
  fréquent parmi les propositions (départage lexicographique, déterministe).

Dans les deux cas, l'exigence de fond demeure : la connaissance n'entre au
graphe que si PLUSIEURS modèles indépendants l'ont affirmée.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from explore.esmm.triplets import Extraction, Triplet, normalize_entity, match_key
from explore.esmm.relations import canonical_relation
from explore.esmm.textsim import jaro_winkler

# seuil de l'étage Jaro-Winkler de la cascade (récolte EPP, ADR-011-v2 : 0.9)
JW_THRESHOLD = 0.9


@dataclass
class ConsensusTriplet:
    triplet: Triplet             # prédicat = consensus (majoritaire si niveau pair)
    supporters: List[str]        # modèles distincts qui soutiennent le LIEN
    signature: str               # signature de paire (identité du lien)
    level: str                   # "exact" | "pair"


@dataclass
class ConsensusResult:
    accepted: List[ConsensusTriplet] = field(default_factory=list)
    rejected: int = 0            # liens proposés mais sous le seuil d'accord
    parse_errors: Dict[str, List[str]] = field(default_factory=dict)  # par modèle, JAMAIS avalés


def vote(extractions: List[Extraction], min_agree: int = 2,
         matcher: Optional[Callable[[str, str], bool]] = None) -> ConsensusResult:
    """`matcher(a, b) -> bool` : équivalence SÉMANTIQUE optionnelle entre objets
    (ex. cosinus mxbai ≥ τ_obj). Sans matcher : égalité lexicale stricte
    (`match_key`). Constat live 2026-07-18 : sans rapprochement sémantique, des
    modèles hétérogènes n'atteignent quasi jamais l'accord (« figure géométrique »
    vs « forme géométrique » : 56 propositions, 0 accepté)."""
    res = ConsensusResult()

    # clusters de liens : sujet identique (lexical strict) + objets équivalents
    # (lexical strict, sinon matcher sémantique). Regroupement glouton, ordre
    # d'arrivée stable → déterministe à extractions données.
    clusters: List[Dict] = []   # {skey, obj_repr, supporters:[], proposals:[(model, pred, t)]}

    def find_cluster(skey: str, obj: str) -> Optional[Dict]:
        """Cascade EPP (ADR-011-v2) : exact → Jaro-Winkler > 0.9 → matcher
        sémantique. Du moins cher au plus cher ; l'embedding n'est payé que si
        le lexical strict ET le flou déterministe ont échoué."""
        okey = match_key(obj)
        for cl in clusters:
            if cl["skey"] != skey:
                continue
            ckey = match_key(cl["obj_repr"])
            if ckey == okey:
                return cl
            if jaro_winkler(ckey, okey) > JW_THRESHOLD:
                return cl
            if matcher is not None and matcher(cl["obj_repr"], obj):
                return cl
        return None

    for ext in extractions:
        if ext.errors:
            res.parse_errors[ext.model] = list(ext.errors)
        voted = set()
        for t in ext.triplets:
            skey = match_key(t.subject)
            cl = find_cluster(skey, t.object)
            if cl is None:
                cl = {"skey": skey, "obj_repr": t.object, "supporters": [], "proposals": []}
                clusters.append(cl)
            cluster_id = id(cl)
            if cluster_id in voted:
                continue  # un modèle ne vote qu'une fois par lien
            voted.add(cluster_id)
            if ext.model not in cl["supporters"]:
                cl["supporters"].append(ext.model)
            # pliage du prédicat vers son canonique (récolte EPP relation_vocabulary,
            # ADR-006) : « type_of » et « est_un » votent ensemble → plus d'« exact »
            cl["proposals"].append((ext.model, canonical_relation(t.predicate), t))

    for cl in clusters:
        supporters = cl["supporters"]
        if len(supporters) < min_agree:
            res.rejected += 1
            continue
        # prédicat majoritaire, départage lexicographique (déterministe)
        pred_support: Counter = Counter()
        pred_example: Dict[str, Triplet] = {}
        for model, pred, t in cl["proposals"]:
            pred_support[pred] += 1
            pred_example.setdefault(pred, t)
        best_pred, best_n = sorted(pred_support.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        level = "exact" if best_n >= min_agree else "pair"
        base = pred_example[best_pred]
        res.accepted.append(ConsensusTriplet(
            triplet=Triplet(subject=base.subject, predicate=best_pred, object=base.object),
            supporters=sorted(supporters),
            signature=base.pair_signature(),
            level=level,
        ))

    res.accepted.sort(key=lambda c: (-len(c.supporters), c.signature))
    return res
