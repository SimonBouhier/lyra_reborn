"""Démo A — la modulation est réelle et visible (P1).

Usage :
    python scripts/demo.py            # hors-ligne (EchoClient), déterministe
    LYRA_LIVE=1 python scripts/demo.py  # branche un Ollama réel (nécessite `requests`)

Montre : deux profils de boutons produisent des options différentes qui
atteignent réellement le modèle ; puis un autopilote P+I qui désature δr.
"""
from __future__ import annotations
import os
import sys

# racine du dépôt sur sys.path (permet `python scripts/demo.py` depuis n'importe où)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# console Windows en UTF-8 (sinon cp1252 ne sait pas afficher accents/symboles)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from core.knobs import Knobs, KnobMapping
from core.llm import EchoClient
from core.state import CognitiveState
from core.config import SmoothingConfig
from core.loop import LyraLoop, run_autopilot


def main() -> None:
    live = os.getenv("LYRA_LIVE") == "1"
    if live:
        from core.llm import OllamaClient
        client = OllamaClient()
        print(f"[live] Ollama modèle={client.model} base={client.base_url}")
    else:
        client = EchoClient()
        print("[offline] EchoClient (déterministe — ne produit pas de vrai texte)")

    mapping = KnobMapping()
    print("\n--- Modulation : mêmes entrées, deux profils de boutons ---")
    for label, k in [("creatif", Knobs(rho=0.85, delta_r=0.75, tau_c=0.95, kappa=0.35)),
                     ("strict",  Knobs(rho=0.50, delta_r=0.35, tau_c=0.35, kappa=0.85))]:
        opts = mapping.to_generation_options(k)
        out = client.generate("Explique la récursivité en une phrase.", opts)
        print(f"  [{label}] options={opts}\n           sortie={out[:100]}")

    print("\n--- Boucle de contrôle (un tour, modulation activée) ---")
    loop = LyraLoop(client, state=CognitiveState(), smoothing=SmoothingConfig(refractory_ms=0))
    res = loop.generate("Donne trois idées structurées.", task_type="focused")
    print(f"  boutons utilisés : {res.knobs_used}")
    print(f"  boutons (prochain tour, après EWMA) : {res.knobs_next}")
    print(f"  modulé : {res.modulated} | tronqué : {res.truncated}")

    print("\n--- Autopilote P+I (dynamique synthetique, desaturation de delta_r) ---")
    traj = run_autopilot(steps=30, knobs=Knobs(rho=0.5, delta_r=0.9, tau_c=0.3, kappa=0.6))
    print(f"  pas 1  : delta_r={traj[0]['delta_r']:.3f}  pression={traj[0]['pressure']:.3f}")
    print(f"  pas 30 : delta_r={traj[-1]['delta_r']:.3f}  pression={traj[-1]['pressure']:.3f}  (consigne 0.45)")


if __name__ == "__main__":
    main()
