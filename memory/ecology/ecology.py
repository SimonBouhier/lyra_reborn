"""Écologie mémorielle : pouponnière / journal d'oubli / compost + réveil différé.

Ré-implémentation PROPRE du design de `session_2/LyrArc` (audité : l'idée la plus
précieuse du lot 2 — le « Journal d'Oubli » que le lot 1 croyait orphelin). Le
tri à trois niveaux :
    score ≥ seuil_pouponnière  → POUPONNIÈRE (mémoire active)
    score partiel              → JOURNAL D'OUBLI (différé : on réévalue plus tard)
    score ≈ 0                  → COMPOST (dormant, mais réveillable — jamais détruit)

L'oubli n'est pas une suppression : c'est un DIFFÉRÉ (journal) ou une DORMANCE
(compost). Le « réveil des tâches mortes » de LyrArc était réel — il est ici de
première classe.

Les 4 bugs de la source, explicitement évités (cf. audit LyrArc §5) :
  1. sémantique oubli/compost inversée entre deux mains  → UNE seule fonction de
     triage, états nommés par Enum, aucune inversion possible ;
  2. scores écrasés à 0.0 à la relecture                → historique de scores
     APPEND-ONLY (`score_history`), jamais d'écrasement ;
  3. double-encapsulation des entrées                   → stockage plat, un seul
     dict `items`, pas de wrapper de wrapper ;
  4. `.add` sur une liste (AttributeError avalé)        → les index d'états sont
     des `set` réels, testés.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import time


class Strate(Enum):
    POUPONNIERE = "pouponniere"
    OUBLI = "oubli"          # journal d'oubli : réévaluation différée
    COMPOST = "compost"      # dormant, réveillable


@dataclass
class MemoryItem:
    id: str
    content: Any
    strate: Strate
    score_history: List[Tuple[float, float]] = field(default_factory=list)  # (ts, score) append-only
    created_ms: int = 0
    revisit_at_ms: Optional[int] = None   # pour OUBLI : échéance de réévaluation
    defers: int = 0                        # nb de reports successifs
    revivals: int = 0                      # nb de réveils depuis le compost

    @property
    def score(self) -> float:
        """Dernier score connu (l'historique n'est jamais écrasé — bug #2)."""
        return self.score_history[-1][1] if self.score_history else 0.0


class MemoryEcology:
    """Le tri vivant : triage, réévaluation différée, réveil du compost."""

    def __init__(self,
                 nursery_threshold: float = 0.6,
                 compost_threshold: float = 0.05,
                 defer_ms: int = 60_000,
                 max_defers: int = 3):
        self.nursery_threshold = nursery_threshold
        self.compost_threshold = compost_threshold
        self.defer_ms = defer_ms
        self.max_defers = max_defers
        self.items: Dict[str, MemoryItem] = {}      # stockage PLAT (bug #3)
        self.index: Dict[Strate, Set[str]] = {s: set() for s in Strate}  # sets réels (bug #4)
        self._now_ms: Optional[int] = None          # horloge injectable (tests)

    # ---------------- horloge ----------------
    def _clock(self) -> int:
        return int(self._now_ms) if self._now_ms is not None else int(time.time() * 1000)

    def set_clock(self, ms: int) -> None:
        self._now_ms = ms

    # ---------------- triage (LA fonction unique — bug #1) ----------------
    def _classify(self, score: float) -> Strate:
        if score >= self.nursery_threshold:
            return Strate.POUPONNIERE
        if score <= self.compost_threshold:
            return Strate.COMPOST
        return Strate.OUBLI

    def triage(self, id: str, content: Any, score: float) -> Strate:
        """Insère (ou re-trie) un item selon son score. Retourne sa strate."""
        now = self._clock()
        strate = self._classify(score)
        it = self.items.get(id)
        if it is None:
            it = MemoryItem(id=id, content=content, strate=strate, created_ms=now)
            self.items[id] = it
        else:
            self.index[it.strate].discard(id)
            it.strate = strate
            it.content = content
        it.score_history.append((now, float(score)))     # append-only (bug #2)
        it.revisit_at_ms = now + self.defer_ms if strate is Strate.OUBLI else None
        self.index[strate].add(id)
        return strate

    # ---------------- réévaluation différée (le cœur du Journal d'Oubli) ----------------
    def due_for_revisit(self) -> List[MemoryItem]:
        now = self._clock()
        return [self.items[i] for i in self.index[Strate.OUBLI]
                if self.items[i].revisit_at_ms is not None
                and self.items[i].revisit_at_ms <= now]

    def revisit_due(self, evaluator: Callable[[MemoryItem], float]
                    ) -> List[Tuple[str, Strate, Strate]]:
        """Réévalue les items du journal arrivés à échéance.

        `evaluator(item) -> score`. Promotion vers la pouponnière, report (jusqu'à
        `max_defers`, ensuite compost), ou compost direct. Retourne les
        transitions (id, avant, après) — un retour VIDE alors que des items
        étaient dus est détectable par l'appelant (anti « vert mais vide »).
        """
        transitions: List[Tuple[str, Strate, Strate]] = []
        now = self._clock()
        for it in self.due_for_revisit():
            old = it.strate
            new_score = float(evaluator(it))
            it.score_history.append((now, new_score))
            new = self._classify(new_score)
            if new is Strate.OUBLI:
                it.defers += 1
                if it.defers >= self.max_defers:
                    new = Strate.COMPOST      # trop de reports : dormance
                else:
                    it.revisit_at_ms = now + self.defer_ms
            if new is not Strate.OUBLI:
                it.revisit_at_ms = None
            if new is not old:
                self.index[old].discard(it.id)
                self.index[new].add(it.id)
                it.strate = new
                transitions.append((it.id, old, new))
        return transitions

    # ---------------- réveil du compost (les tâches mortes peuvent revivre) ----------------
    def wake_from_compost(self, id: str) -> MemoryItem:
        """Réveille un item composté → retour au journal d'oubli pour réévaluation.

        Lève KeyError si l'item n'est pas au compost (pas d'échec silencieux).
        """
        if id not in self.index[Strate.COMPOST]:
            raise KeyError(f"'{id}' n'est pas au compost")
        it = self.items[id]
        self.index[Strate.COMPOST].discard(id)
        it.strate = Strate.OUBLI
        it.defers = 0
        it.revivals += 1
        it.revisit_at_ms = self._clock() + self.defer_ms
        self.index[Strate.OUBLI].add(id)
        return it

    # ---------------- lectures & persistance ----------------
    def by_strate(self, strate: Strate) -> List[MemoryItem]:
        return [self.items[i] for i in sorted(self.index[strate])]

    def counts(self) -> Dict[str, int]:
        return {s.value: len(self.index[s]) for s in Strate}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "config": {"nursery_threshold": self.nursery_threshold,
                       "compost_threshold": self.compost_threshold,
                       "defer_ms": self.defer_ms, "max_defers": self.max_defers},
            "items": [{
                "id": it.id, "content": it.content, "strate": it.strate.value,
                "score_history": it.score_history, "created_ms": it.created_ms,
                "revisit_at_ms": it.revisit_at_ms, "defers": it.defers,
                "revivals": it.revivals,
            } for it in self.items.values()],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MemoryEcology":
        eco = cls(**d["config"])
        for r in d["items"]:
            it = MemoryItem(id=r["id"], content=r["content"],
                            strate=Strate(r["strate"]),
                            score_history=[tuple(x) for x in r["score_history"]],
                            created_ms=r["created_ms"],
                            revisit_at_ms=r["revisit_at_ms"],
                            defers=r["defers"], revivals=r["revivals"])
            eco.items[it.id] = it
            eco.index[it.strate].add(it.id)
        return eco
