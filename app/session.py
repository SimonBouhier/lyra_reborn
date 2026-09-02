"""Première couche de la porte P6 : un tour de conversation traverse P0–P4.

Chemin (plan §10.1, Démo D) :
  lecture d'état → injection nemeton bornée → génération modulée →
  graphe (récolte bornée) → écologie → cas.

Anti « vert mais vide » : après un prompt qui porte au moins un concept,
le graphe n'est plus vide. Un prompt vide lève une erreur, il n'est pas avalé.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import json
import math
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple
import time
import uuid

from core.config import SmoothingConfig
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


SESSION_STATE_VERSION = 1


class SessionStateError(ValueError):
    """Un état durable ne respecte pas le contrat de session courant."""


class SessionPersistence(Protocol):
    def save(self, state: Dict[str, Any]) -> None: ...

    def load(self, session_id: str) -> Dict[str, Any] | None: ...

    def list_summaries(self) -> List[Dict[str, Any]]: ...


def _default_backend_resolver(label: str) -> Tuple[Any, str]:
    """Restaure uniquement le moteur hors-ligne connu, sans substitution."""
    if label != "premières couches":
        raise RuntimeError(
            f"aucun résolveur n'est configuré pour le moteur persisté : {label}"
        )
    return EchoClient(), label


def _make_loop(
    llm,
    refractory_ms: int = 1200,
    state: Optional[CognitiveState] = None,
) -> LyraLoop:
    return LyraLoop(
        llm,
        mapping=KnobMapping(),
        state=state or CognitiveState(),
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
                 refractory_ms: int = 1200,
                 backend_label: Optional[str] = None,
                 state: Optional[CognitiveState] = None):
        self.id = session_id or uuid.uuid4().hex[:12]
        self.llm = llm or EchoClient()
        self.backend_label = backend_label or getattr(self.llm, "model", "inconnu")
        self.loop = _make_loop(
            self.llm,
            refractory_ms=refractory_ms,
            state=state,
        )
        # Premier tour : la période réfractaire ne doit pas avaler la première
        # parole. Un état restauré conserve au contraire son horodatage exact.
        if state is None:
            self.loop.state.last_update_ms = 0
        self.graph = GraphStore()
        self.ecology = MemoryEcology()
        self.memento = Memento()
        self.navigator = Navigator(self.graph, self.memento)
        self.created = time.time()
        self.turns: int = 0

    def use_backend(self, llm: Any, label: str) -> None:
        """Remplace le moteur de cette session sans affecter les autres."""
        self.llm = llm
        self.loop.llm = llm
        self.backend_label = label

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
            "moteur": self.backend_label,
        }

    def to_state(self) -> Dict[str, Any]:
        """Sérialise tout l'état nécessaire pour poursuivre après redémarrage."""
        try:
            return {
                "schema_version": SESSION_STATE_VERSION,
                "id": self.id,
                "backend_label": self.backend_label,
                "created": self.created,
                "turns": self.turns,
                "smoothing": asdict(self.loop.smoothing),
                "cognitive_state": self.loop.state.to_dict(),
                "controller": {"pressure_i": self.loop.controller.pressure_i},
                "graph_limits": {
                    "max_nodes": self.graph.max_nodes,
                    "max_edges": self.graph.max_edges,
                },
                "graph": json.loads(self.graph.snapshot()),
                "ecology": self.ecology.to_dict(),
                "memento": self.memento.to_dict(),
            }
        except (TypeError, ValueError, OverflowError, RuntimeError) as exc:
            raise SessionStateError(
                f"impossible de sérialiser la session {self.id} : {exc}"
            ) from exc

    @classmethod
    def from_state(
        cls,
        data: Dict[str, Any],
        *,
        backend: Tuple[Any, str],
    ) -> "LyraConversation":
        """Reconstruit une session et refuse tout état partiel ou incohérent."""
        try:
            if not isinstance(data, dict):
                raise ValueError("racine non objet")
            version = int(data["schema_version"])
            if version != SESSION_STATE_VERSION:
                raise ValueError(f"version non supportée : {version}")
            session_id = data["id"]
            backend_label = data["backend_label"]
            if not isinstance(session_id, str) or not session_id:
                raise ValueError("identifiant vide")
            if not isinstance(backend_label, str) or not backend_label:
                raise ValueError("étiquette de moteur vide")
            llm, resolved_label = backend
            if resolved_label != backend_label:
                raise ValueError("résolution du moteur incohérente")

            smoothing_data = data["smoothing"]
            if not isinstance(smoothing_data, dict):
                raise ValueError("configuration de lissage invalide")
            smoothing = SmoothingConfig(**smoothing_data)
            if not (
                math.isfinite(smoothing.ewma_alpha)
                and 0.0 <= smoothing.ewma_alpha <= 1.0
                and math.isfinite(smoothing.hysteresis_eps)
                and smoothing.hysteresis_eps >= 0.0
                and smoothing.refractory_ms >= 0
            ):
                raise ValueError("configuration de lissage hors bornes")
            cognitive_state = CognitiveState.from_dict(data["cognitive_state"])
            if not all(
                math.isfinite(value) and 0.0 <= value <= 1.0
                for value in cognitive_state.knobs.as_dict().values()
            ):
                raise ValueError("boutons cognitifs hors bornes")

            created = float(data["created"])
            turns = int(data["turns"])
            if not math.isfinite(created) or created <= 0:
                raise ValueError("horodatage de création invalide")
            if turns < 0:
                raise ValueError("nombre de tours négatif")

            graph_limits = data["graph_limits"]
            if not isinstance(graph_limits, dict):
                raise ValueError("bornes du graphe invalides")
            max_nodes = int(graph_limits["max_nodes"])
            max_edges = int(graph_limits["max_edges"])
            if max_nodes <= 0 or max_edges <= 0:
                raise ValueError("bornes du graphe non positives")
            graph_data = data["graph"]
            if not isinstance(graph_data, dict):
                raise ValueError("graphe invalide")
            graph = GraphStore.from_snapshot(
                json.dumps(graph_data, ensure_ascii=False, allow_nan=False),
                max_nodes=max_nodes,
                max_edges=max_edges,
            )
            ecology = MemoryEcology.from_dict(data["ecology"])
            memento = Memento.from_dict(data["memento"])

            expected_history = min(turns, 50)
            if len(cognitive_state.history) != expected_history:
                raise ValueError("historique incomplet")
            if len(memento) != turns:
                raise ValueError("banc de cas incomplet")
            if sum(ecology.counts().values()) != turns:
                raise ValueError("écologie mémorielle incomplète")

            pressure_i = float(data["controller"]["pressure_i"])
            if not math.isfinite(pressure_i):
                raise ValueError("intégrale du contrôleur invalide")

            conv = cls(
                llm=llm,
                session_id=session_id,
                refractory_ms=smoothing.refractory_ms,
                backend_label=backend_label,
                state=cognitive_state,
            )
            conv.loop.smoothing = smoothing
            if abs(pressure_i) > conv.loop.controller.cfg.pressure_i_max:
                raise ValueError("intégrale du contrôleur hors bornes")
            conv.loop.controller.pressure_i = pressure_i
            conv.graph = graph
            conv.ecology = ecology
            conv.memento = memento
            conv.navigator = Navigator(conv.graph, conv.memento)
            conv.created = created
            conv.turns = turns
            return conv
        except SessionStateError:
            raise
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise SessionStateError(f"état de session invalide : {exc}") from exc


class SessionBook:
    """Registre vivant avec restauration paresseuse depuis un dépôt local."""

    def __init__(
        self,
        llm_factory: Optional[Callable[[], Tuple[Any, str]]] = None,
        backend_resolver: Optional[Callable[[str], Tuple[Any, str]]] = None,
        storage: Optional[SessionPersistence] = None,
    ):
        self._llm_factory = llm_factory or (
            lambda: (EchoClient(), "premières couches")
        )
        self._backend_resolver = backend_resolver or _default_backend_resolver
        self._storage = storage
        self._sessions: Dict[str, LyraConversation] = {}

    def create(
        self,
        session_id: Optional[str] = None,
        refractory_ms: int = 1200,
        backend: Optional[Tuple[Any, str]] = None,
    ) -> LyraConversation:
        if session_id and session_id in self._sessions:
            raise ValueError(f"session déjà existante : {session_id}")
        if session_id and self._storage is not None:
            if self._storage.load(session_id) is not None:
                raise ValueError(f"session déjà existante : {session_id}")
        llm, label = backend if backend is not None else self._llm_factory()
        conv = LyraConversation(
            llm=llm,
            session_id=session_id,
            refractory_ms=refractory_ms,
            backend_label=label,
        )
        self._sessions[conv.id] = conv
        return conv

    def require(self, session_id: str) -> LyraConversation:
        """Retourne une session existante ; ne crée jamais pendant une lecture."""
        conv = self._sessions.get(session_id)
        if conv is not None:
            return conv
        if self._storage is not None:
            state = self._storage.load(session_id)
            if state is not None:
                conv = LyraConversation.from_state(
                    state,
                    backend=self._backend_resolver(state.get("backend_label", "")),
                )
                self._sessions[conv.id] = conv
                return conv
        raise KeyError(f"session inconnue : {session_id}")

    def persist(self, conv: LyraConversation) -> None:
        if self._storage is not None:
            self._storage.save(conv.to_state())

    def restore(self, state: Dict[str, Any]) -> LyraConversation:
        label = state.get("backend_label", "")
        conv = LyraConversation.from_state(
            state,
            backend=self._backend_resolver(label),
        )
        self._sessions[conv.id] = conv
        return conv

    def rollback(
        self,
        session_id: str,
        previous_state: Optional[Dict[str, Any]],
    ) -> None:
        """Annule une mutation mémoire sans toucher à l'état SQLite antérieur."""
        if previous_state is None:
            self._sessions.pop(session_id, None)
            return
        self.restore(previous_state)

    def list_sessions(self) -> List[Dict[str, Any]]:
        if self._storage is not None:
            return self._storage.list_summaries()
        return [
            {
                "id": conv.id,
                "moteur": conv.backend_label,
                "tours": conv.turns,
                "created": conv.created,
                "updated": conv.created,
            }
            for conv in sorted(
                self._sessions.values(),
                key=lambda item: item.created,
                reverse=True,
            )
        ]
