"""État cognitif de Lyra : boutons courants, historique, lissage EWMA.

Porté de conscious/state.py (lot 1). L'EWMA + l'horodatage servent les
garde-fous (hystérésis / réfractaire) de core/control/guards.py.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
import time

from core.knobs import Knobs


@dataclass
class Turn:
    prompt: str
    output: str
    metrics: Dict[str, float]


@dataclass
class CognitiveState:
    knobs: Knobs = field(default_factory=Knobs)
    last_update_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    history: List[Turn] = field(default_factory=list)
    last_prompt_keywords: List[str] = field(default_factory=list)
    last_topic_signature: List[str] = field(default_factory=list)
    _now_ms = None  # crochet de test (voir set_clock)

    def elapsed_since_update_ms(self) -> int:
        return self._clock() - self.last_update_ms

    def _clock(self) -> int:
        if self._now_ms is not None:
            return int(self._now_ms)
        return int(time.time() * 1000)

    def set_clock(self, ms: int) -> None:
        """Fige l'horloge (tests des garde-fous réfractaires)."""
        self._now_ms = ms

    def ewma_update(self, target: Dict[str, float], alpha: float) -> None:
        """Lissage exponentiel des boutons vers `target` (anti-oscillation)."""
        k = self.knobs
        for name in ("rho", "delta_r", "tau_c", "kappa"):
            old = getattr(k, name)
            new = float(alpha * float(target[name]) + (1.0 - alpha) * old)
            setattr(k, name, new)
        self.last_update_ms = self._clock()

    def push(self, prompt: str, output: str, metrics: Dict[str, float]) -> None:
        self.history.append(Turn(prompt=prompt, output=output, metrics=dict(metrics)))
        if len(self.history) > 50:
            self.history.pop(0)

    def to_dict(self) -> Dict[str, Any]:
        """État durable minimal ; l'horloge de test n'est jamais persistée."""
        return {
            "knobs": self.knobs.as_dict(),
            "last_update_ms": self.last_update_ms,
            "history": [
                {
                    "prompt": turn.prompt,
                    "output": turn.output,
                    "metrics": dict(turn.metrics),
                }
                for turn in self.history
            ],
            "last_prompt_keywords": list(self.last_prompt_keywords),
            "last_topic_signature": list(self.last_topic_signature),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CognitiveState":
        try:
            history_data = data["history"]
            if not isinstance(history_data, list) or len(history_data) > 50:
                raise ValueError("historique invalide ou non borné")
            history = []
            for row in history_data:
                if not isinstance(row, dict):
                    raise ValueError("tour d'historique invalide")
                prompt = row["prompt"]
                output = row["output"]
                metrics = row["metrics"]
                if not isinstance(prompt, str) or not isinstance(output, str):
                    raise ValueError("texte d'historique invalide")
                if not isinstance(metrics, dict):
                    raise ValueError("métriques d'historique invalides")
                history.append(Turn(prompt=prompt, output=output, metrics=dict(metrics)))
            keywords = data["last_prompt_keywords"]
            signature = data["last_topic_signature"]
            if not isinstance(keywords, list) or not all(
                isinstance(value, str) for value in keywords
            ):
                raise ValueError("mots-clés invalides")
            if not isinstance(signature, list) or not all(
                isinstance(value, str) for value in signature
            ):
                raise ValueError("signature de sujet invalide")
            return cls(
                knobs=Knobs.from_dict(data["knobs"]),
                last_update_ms=int(data["last_update_ms"]),
                history=history,
                last_prompt_keywords=list(keywords),
                last_topic_signature=list(signature),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"état cognitif invalide : {exc}") from exc
