"""État cognitif de Lyra : boutons courants, historique, lissage EWMA.

Porté de conscious/state.py (lot 1). L'EWMA + l'horodatage servent les
garde-fous (hystérésis / réfractaire) de core/control/guards.py.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
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
