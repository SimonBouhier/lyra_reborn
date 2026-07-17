"""Les quatre boutons cognitifs ρ/δr/τc/κ et leur mapping vers la génération.

SOURCE UNIQUE DE VÉRITÉ (règle §5 de la charte). Toute la douleur des deux lots
d'audit vient d'avoir eu 3 à 6 implémentations divergentes de ce mapping. Ici,
une seule.

Sémantique retenue (cf. manifeste/VOCABULAIRE.md) :
    ρ  (rho)     -> top_p        (structure / diversité contrôlée)
    δr (delta_r) -> num_predict  (dilatation du contexte / longueur)
    τc (tau_c)   -> temperature  (tension)
    κ  (kappa)   -> repeat_penalty (courbure / style, anti-répétition)

Mapping porté de conscious/config.py:KnobMapping (lot 1). Les noms d'options
sont ceux d'Ollama natif (num_predict, repeat_penalty), envoyés sous "options".
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict


def clamp01(x: float) -> float:
    x = float(x)
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


@dataclass
class Knobs:
    """Les 4 boutons, chacun dans [0, 1]."""
    rho: float = 0.50
    delta_r: float = 0.30
    tau_c: float = 0.80
    kappa: float = 0.60

    def clamped(self) -> "Knobs":
        return Knobs(clamp01(self.rho), clamp01(self.delta_r),
                     clamp01(self.tau_c), clamp01(self.kappa))

    def as_dict(self) -> Dict[str, float]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> "Knobs":
        return cls(rho=float(d["rho"]), delta_r=float(d["delta_r"]),
                   tau_c=float(d["tau_c"]), kappa=float(d["kappa"]))


@dataclass
class KnobMapping:
    """Bornes « matérielles » du LLM et projection boutons [0,1] -> options Ollama."""
    temperature_min: float = 0.10
    temperature_max: float = 1.20
    top_p_min: float = 0.20
    top_p_max: float = 0.98
    repeat_penalty_min: float = 1.00
    repeat_penalty_max: float = 1.50
    num_predict_min: int = 128
    num_predict_max: int = 2048

    def _lerp(self, lo: float, hi: float, t: float) -> float:
        return lo + (hi - lo) * clamp01(t)

    def to_generation_options(self, knobs: Knobs) -> Dict[str, float]:
        """Projette les 4 boutons vers les options de génération Ollama.

        Retourne un dict prêt à être placé sous la clé "options" du payload
        (cf. core/llm.py — c'est là qu'était le bug du canon `conscious`).
        """
        return {
            "temperature": round(self._lerp(self.temperature_min, self.temperature_max, knobs.tau_c), 4),
            "top_p": round(self._lerp(self.top_p_min, self.top_p_max, knobs.rho), 4),
            "repeat_penalty": round(self._lerp(self.repeat_penalty_min, self.repeat_penalty_max, knobs.kappa), 4),
            "num_predict": int(self._lerp(self.num_predict_min, self.num_predict_max, knobs.delta_r)),
        }
