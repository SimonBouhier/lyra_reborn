"""Première couche de la porte P6 : un tour de conversation traverse P0–P4.

Chemin (plan §10.1, Démo D) :
  lecture d'état → injection nemeton bornée → génération modulée →
  graphe (récolte bornée) → écologie → cas.

Anti « vert mais vide » : après un prompt qui porte au moins un concept,
le graphe n'est plus vide. Un prompt vide lève une erreur, il n'est pas avalé.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import time
import uuid

from core.control.controller import PIController
from core.knobs import KnobMapping
from core.llm import EchoClient
from core.loop import LyraLoop
from core.state import CognitiveState
from memory.cbr.memento import Case, Memento, Navigator
from memory.ecology.ecology import MemoryEcology
from memory.graph.injector import inject
from memory.graph.store import GraphStore

from app.harvest import harvest_concepts


def format_path_reply(rec: TurnRecord) -> str:
    """Réponse des premières couches : le chemin, pas une voix.

    Un dump `[echo temperature=…]` n'est pas une parole. Ce texte dit
    ce qui s'est vraiment passé, sans faire semblant d'être un modèle.
    """
    concepts = ", ".join(rec.concepts) if rec.concepts else "aucun concept retenu"
    k = rec.knobs_next
    return (
        "Tour pris. Ce n'est pas une voix — c'est le chemin du plan.\n"
        f"Concepts : {concepts}.\n"
        f"Graphe : {rec.graph.get('nodes', 0)} nœuds, {rec.graph.get('edges', 0)} liens.\n"
        f"Réglage : ρ {k.get('rho', 0):.2f} · δr {k.get('delta_r', 0):.2f} "
        f"· τc {k.get('tau_c', 0):.2f} · κ {k.get('kappa', 0):.2f}.\n"
        f"Modulation : {'oui' if rec.modulated else 'pas ce tour'}."
    )


def _make_loop(llm, refractory_ms: int = 1200) -> LyraLoop:
    from core.config import SmoothingConfig
    return LyraLoop(
        llm,
        mapping=KnobMapping(),
        state=CognitiveState(),
        smoothing=SmoothingConfig(refractory_ms=refractory_ms),
        controller=PIController(),
    )


@dataclass
class TurnRecord:
    prompt: str
    output: str
    knobs_used: Dict[str, float]
    knobs_next: Dict[str, float]
    options: Dict[str, Any]
    metrics: Dict[str, float]
    modulated: bool
    graph: Dict[str, int]
    ecology: Dict[str, int]
    concepts: List[str]
    nemeton: str
    suggestion: Optional[str] = None


class LyraConversation:
    """Une session : une boucle, un graphe, une écologie, un banc de cas."""

    def __init__(self, llm=None, session_id: Optional[str] = None,
                 refractory_ms: int = 1200):
        self.id = session_id or uuid.uuid4().hex[:12]
        self.llm = llm or EchoClient()
        self.loop = _make_loop(self.llm, refractory_ms=refractory_ms)
        # Premier tour : la période réfractaire ne doit pas avaler la première parole.
        self.loop.state.last_update_ms = 0
        self.graph = GraphStore()
        self.ecology = MemoryEcology()
        self.memento = Memento()
        self.navigator = Navigator(self.graph, self.memento)
        self.created = time.time()
        self.turns: int = 0

    def turn(self, prompt: str, task_type: str = "general") -> TurnRecord:
        text = (prompt or "").strip()
        if not text:
            raise ValueError("prompt vide — un tour sans parole n'est pas un tour")

        nemeton = inject(self.graph)
        composed = text if self.graph.counts()["nodes"] == 0 else f"{nemeton}\n\n{text}"
        result = self.loop.generate(composed, task_type=task_type)
        self.turns += 1

        concepts = harvest_concepts(text)
        for cid in concepts:
            if self.graph.node(cid) is None:
                self.graph.upsert_node(cid, "concept")
        for a, b in zip(concepts, concepts[1:]):
            self.graph.add_edge(a, b, type="cooccur")

        hedge = float(result.metrics.get("hedge", 0.0))
        self.ecology.triage(
            f"tour_{self.turns}",
            {"prompt": text, "concepts": concepts},
            score=hedge,
        )

        epi = result.epistemic or {}
        features = {
            "coherence": float(epi.get("coherence", 0.0)),
            "fit": float(epi.get("fit", 0.0)),
            "pressure": float(epi.get("pressure", 0.0)),
            "tension": float(epi.get("tension", 0.0)),
            "delta_r": float(result.knobs_next.get("delta_r", 0.0)),
            "tau_c": float(result.knobs_next.get("tau_c", 0.0)),
        }
        fav = concepts[0] if concepts else None
        self.memento.add_case(Case(
            id=f"tour_{self.turns}",
            features=features,
            outcome={"fav_node": fav} if fav else {},
        ))
        suggestion = self.navigator.suggest(features, k=1, strategy="case_guided")

        return TurnRecord(
            prompt=text,
            output=result.output,
            knobs_used=result.knobs_used,
            knobs_next=result.knobs_next,
            options=result.options,
            metrics=result.metrics,
            modulated=result.modulated,
            graph=self.graph.counts(),
            ecology=self.ecology.counts(),
            concepts=concepts,
            nemeton=nemeton,
            suggestion=suggestion.reason,
        )

    def snapshot(self) -> Dict[str, Any]:
        knobs = self.loop.state.knobs.as_dict()
        return {
            "id": self.id,
            "tours": self.turns,
            "boutons": knobs,
            "graphe": self.graph.counts(),
            "memoire": self.ecology.counts(),
            "cas": len(self.memento),
            "nemeton": inject(self.graph),
        }


class SessionBook:
    """Registre en mémoire — une session par id, pas de base distante."""

    def __init__(self, llm_factory=None):
        self._llm_factory = llm_factory or EchoClient
        self._sessions: Dict[str, LyraConversation] = {}

    def get(self, session_id: Optional[str] = None,
            refractory_ms: int = 1200) -> LyraConversation:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        conv = LyraConversation(
            llm=self._llm_factory(),
            session_id=session_id,
            refractory_ms=refractory_ms,
        )
        self._sessions[conv.id] = conv
        return conv
