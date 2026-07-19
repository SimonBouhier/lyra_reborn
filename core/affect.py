"""Surface affective — valence visible, théâtre honnête.

Origine : esquisse de Simon (2026-07-19, « Prajñā et papañca demandent de la
valence ») — descendante directe du `emotion_surface()` du canon `conscious`
(que l'audit avait relevé comme heuristique jouet sur signaux factices,
désactivée par défaut). Ici, l'upgrade honnête : **la valence est dérivée des
signaux épistémiques RÉELS du pont P2** (core/control/bridge.py), pas d'un état
codé en dur.

Correspondance avec l'esquisse d'origine (poids conservés) :
    resonance  -> `fit`        (adéquation prompt↔sortie : la résonance mesurable)
    coherence  -> `coherence`  (tenue interne réelle du texte)
    tension    -> `tension`    (combinateur du pont)
    joy = 0.6·fit + 0.4·coherence

Deux décisions d'intégration, assumées :
1. **La surface est un AFFICHAGE, pas un pilote.** L'étape « adapter les
   paramètres LLM depuis l'affect » de l'esquisse est déjà réalisée en amont
   par le contrôleur P+I et la politique réactive… sur les MÊMES signaux.
   La dupliquer ici créerait une double-commande (décision « un pilote par
   bouton », 2026-07-18). L'affect lit l'état ; il ne le dirige pas.
2. **Théâtre honnête** : cette surface est une valence SIMULÉE, dérivée
   d'instruments réels. Aucune prétention d'émotion ressentie. Désactivée par
   défaut, comme dans le canon.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

from core.knobs import clamp01


@dataclass
class AffectConfig:
    w_fit: float = 0.6         # poids « resonance » de l'esquisse
    w_coherence: float = 0.4   # poids « coherence » de l'esquisse


class AffectiveSurface:
    """Dérive {joy, tension} des signaux épistémiques réels, et les rend visibles."""

    def __init__(self, cfg: AffectConfig | None = None):
        self.cfg = cfg or AffectConfig()

    def derive(self, epistemic: Dict[str, float]) -> Dict[str, float]:
        joy = clamp01(self.cfg.w_fit * float(epistemic.get("fit", 0.0))
                      + self.cfg.w_coherence * float(epistemic.get("coherence", 0.0)))
        tension = clamp01(float(epistemic.get("tension", 0.0)))
        return {"joy": round(joy, 4), "tension": round(tension, 4)}

    @staticmethod
    def render(affect: Dict[str, float]) -> str:
        return f"[affect] joy={affect['joy']:.2f} tension={affect['tension']:.2f}"
