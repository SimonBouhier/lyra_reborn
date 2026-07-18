"""Pont P2 : signaux épistémiques RÉELS dérivés d'une vraie génération.

C'est le chaînon qui manquait (cf. BUILD_STATUS « note d'architecture ») : le
contrôleur P+I régulait une dynamique synthétique (`measures.py`, étiquetée
jouet) ; ici, cohérence / fit / pression sont dérivés de la génération réelle,
pour que le P+I calibré (B03+P1P2) régule enfin du réel.

Définitions v1 (décision datée 2026-07-18, cf. manifeste/VOCABULAIRE.md) :
- **coherence** — tenue interne du texte : structure + absence d'emballement
  (répétitions). Signal : `struct` et `repeat4` de core/metrics/cheap.py.
- **fit** — adéquation prompt↔sortie : recouvrement de mots-clés, pénalisé si
  troncature (une réponse coupée ne « colle » pas à la demande).
- **pressure** — charge réelle : utilisation du budget de génération
  (tokens produits / num_predict). C'est mécaniquement le signal que δr pilote
  (δr → num_predict), donc la boucle pression→δr du P+I devient physique.
- **tension** — combinateur commun (même formule que l'autopilote : la
  synthéticité était dans les ENTRÉES, pas dans la règle de combinaison).

Les pondérations sont de la CONFIG calibrable (jamais des constantes enfouies —
leçon `KAPPA_C`) ; défauts choisis pour placer des sorties typiques dans des
plages saines, à recalibrer sur runs réels contre les critères §8.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict

from core.knobs import clamp01
from core.metrics.cheap import tokens
from core.control.measures import measure_tension  # combinateur pur coh/fit/press


@dataclass
class BridgeConfig:
    w_struct: float = 0.5        # part de la structure dans la cohérence
    w_norepeat: float = 0.5      # part de l'anti-emballement dans la cohérence
    repeat_gain: float = 5.0     # amplification du taux de 4-grammes répétés
    fit_gain: float = 2.5        # gain sur kw_overlap (Jaccard brut est bas)
    trunc_penalty: float = 0.15  # pénalité de fit si troncature suspectée


class EpistemicBridge:
    """Dérive {coherence, fit, pressure, tension} d'un tour de génération réel."""

    def __init__(self, cfg: BridgeConfig | None = None):
        self.cfg = cfg or BridgeConfig()

    def derive(self, output: str, options: Dict[str, Any],
               cheap: Dict[str, float]) -> Dict[str, float]:
        c = self.cfg
        struct = float(cheap.get("struct", 0.0))
        rep = float(cheap.get("repeat4", 0.0))
        ko = float(cheap.get("kw_overlap", 0.0))
        truncated = bool(cheap.get("truncated", 0.0))

        coherence = clamp01(c.w_struct * struct
                            + c.w_norepeat * (1.0 - min(1.0, rep * c.repeat_gain)))
        fit = clamp01(c.fit_gain * ko - (c.trunc_penalty if truncated else 0.0))
        budget = max(1, int(options.get("num_predict", 1)))
        pressure = clamp01(len(tokens(output)) / budget)
        tension = measure_tension(coherence, fit, pressure)

        return {"coherence": coherence, "fit": fit,
                "pressure": pressure, "tension": tension}
