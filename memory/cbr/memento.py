"""Memento — raisonnement par cas (CBR) + navigateur à 4 stratégies.

Porté du design de `session_2/IspaceNav.zip` (audité : la formulation la plus
saine du volet « ispace » ; ses descendants dans la famille Uni avaient cassé
`/ispace/suggest` en lisant un attribut inexistant). Ici la `Suggestion` est un
dataclass aux champs EXPLICITES — la classe de bug est structurellement exclue.

Périmètre honnête : ce module retrouve des cas similaires et propose des cibles
de navigation. La projection état→options de génération reste dans `core/knobs`
(une seule source de vérité — charte §5) ; l'ancien `project_surcouche` aux
constantes magiques n'est PAS reproduit.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import math

from memory.graph.store import GraphStore

# ordre canonique des features d'état (aligné sur les signaux P1/P2)
FEATURE_ORDER: List[str] = ["coherence", "fit", "pressure", "tension", "delta_r", "tau_c"]


def cosine(a: List[float], b: List[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    da = math.sqrt(sum(x * x for x in a)) + 1e-9
    db = math.sqrt(sum(y * y for y in b)) + 1e-9
    return num / (da * db)


@dataclass
class Case:
    """Un épisode mémorisé : vecteur d'état + issue observée."""
    id: str
    features: Dict[str, float]
    outcome: Dict[str, Any] = field(default_factory=dict)   # ex. {"fav_node": "...", "notes": "..."}


@dataclass
class Suggestion:
    """Champs explicites (le bug `/ispace/suggest` lisait un attribut inexistant)."""
    reason: str
    strategy: str
    next_targets: List[str] = field(default_factory=list)
    retrieved: List[Tuple[str, float]] = field(default_factory=list)  # (case_id, similarité)


class Memento:
    """Banc de cas : rappel des K plus proches par cosinus sur le vecteur d'état."""

    def __init__(self, order: Optional[List[str]] = None):
        self.order = list(order or FEATURE_ORDER)
        self._cases: Dict[str, Case] = {}

    def add_case(self, case: Case) -> None:
        self._cases[case.id] = case

    def __len__(self) -> int:
        return len(self._cases)

    def _vec(self, feats: Dict[str, float]) -> List[float]:
        return [float(feats.get(k, 0.0)) for k in self.order]

    def retrieve(self, query: Dict[str, float], k: int = 4) -> List[Tuple[Case, float]]:
        qv = self._vec(query)
        scored = [(c, cosine(qv, self._vec(c.features))) for c in self._cases.values()]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


class Navigator:
    """4 stratégies nommées (design IspaceNav) sur le nemeton + le banc de cas."""

    def __init__(self, graph: GraphStore, memento: Optional[Memento] = None):
        self.graph = graph
        self.memento = memento

    def suggest(self, state: Dict[str, float], k: int = 4,
                strategy: str = "balanced") -> Suggestion:
        targets: List[str] = []
        retrieved: List[Tuple[str, float]] = []

        if strategy == "stabilize":
            reason = "stabilize : viser les personas de rigueur/calme"
            for n in self.graph.list_nodes(type="persona", limit=50):
                if n.data.get("style") in ("rigor", "cool", "sparse"):
                    targets.append(n.id)
        elif strategy == "explore":
            reason = "explore : viser les intents à forte nouveauté"
            for n in self.graph.list_nodes(type="intent", limit=50):
                if float(n.data.get("novelty", 0.0)) > 0.5:
                    targets.append(n.id)
        elif strategy == "case_guided":
            if self.memento is None or len(self.memento) == 0:
                # explicite, pas silencieux : la stratégie exige un banc non vide
                return Suggestion(reason="case_guided : banc de cas vide — aucun rappel possible",
                                  strategy=strategy)
            reason = "case_guided : rappel des cas les plus proches"
            for case, sim in self.memento.retrieve(state, k=k):
                retrieved.append((case.id, round(sim, 4)))
                fav = case.outcome.get("fav_node")
                if fav:
                    targets.append(fav)
        else:
            strategy = "balanced"
            reason = "balanced : compromis par défaut"

        if not targets:
            for t in ("artifact", "intent", "state", "concept"):
                targets.extend(n.id for n in self.graph.list_nodes(type=t, limit=10))

        return Suggestion(reason=reason, strategy=strategy,
                          next_targets=targets[:k], retrieved=retrieved)
