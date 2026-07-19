"""La boucle de contrôle — le cœur battant de Lyra (P1).

Deux chemins, volontairement distincts et honnêtes :

1) LyraLoop.generate() — le chemin RÉEL. Autour d'un vrai LLM : boutons courants
   -> options (avec le correctif options{}) -> génération -> métriques cheap
   RÉELLES -> politique réactive -> garde-fous -> EWMA. C'est la consolidation du
   canon `conscious` avec le mapping corrigé.

2) run_autopilot() — le régulateur P+I sur une dynamique SYNTHÉTIQUE (measures.py).
   Sert à démontrer/tester la loi de commande hors LLM. Ne produit aucun texte.

Le pont entre les deux (brancher le P+I sur de vraies métriques épistémiques) est
un chantier explicite de P2 — voir BUILD_STATUS.md. On ne le simule pas ici.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.knobs import Knobs, KnobMapping
from core.state import CognitiveState
from core.config import HeuristicThresholds, SmoothingConfig
from core.metrics.cheap import hedge_score, truncation_suspect, carryover_intrusion
from core.control.reactive import apply_task_overrides, decide_next_knobs
from core.control.guards import clamp_and_hysteresis, refractory_ok


@dataclass
class LoopResult:
    output: str
    options: Dict[str, Any]
    knobs_used: Dict[str, float]
    knobs_next: Dict[str, float]
    metrics: Dict[str, float]
    truncated: bool
    modulated: bool
    epistemic: Optional[Dict[str, float]] = None  # signaux réels (mode pont P2)
    affect: Optional[Dict[str, float]] = None     # surface affective (théâtre honnête)


class LyraLoop:
    """Enveloppe de contrôle autour d'un client LLM (`.generate(prompt, options)`).

    Deux modes de modulation de l'état de base :
    - sans `controller` : politique réactive seule (P1) ;
    - avec `controller` (PIController) : **pont P2** — partage des responsabilités,
      décision datée 2026-07-18 : le P+I régule **δr et τc** (consignes de
      pression/tension sur signaux épistémiques RÉELS via EpistemicBridge), la
      politique réactive garde **ρ et κ** (symptômes textuels). Un seul pilote
      par bouton — pas de double-commande.
    """

    def __init__(self, llm, mapping: Optional[KnobMapping] = None,
                 thresholds: Optional[HeuristicThresholds] = None,
                 smoothing: Optional[SmoothingConfig] = None,
                 state: Optional[CognitiveState] = None,
                 enable_carryover_guard: bool = True,
                 controller=None, bridge=None,
                 enable_affective_surface: bool = False):
        self.llm = llm
        self.mapping = mapping or KnobMapping()
        self.thresholds = thresholds or HeuristicThresholds()
        self.smoothing = smoothing or SmoothingConfig()
        self.state = state or CognitiveState()
        self.enable_carryover_guard = enable_carryover_guard
        self.controller = controller          # Optional[PIController]
        self.enable_affective_surface = enable_affective_surface
        # le pont fournit les signaux réels : requis par le contrôleur ET par la
        # surface affective (théâtre honnête = valence sur instruments réels)
        if bridge is None and (controller is not None or enable_affective_surface):
            from core.control.bridge import EpistemicBridge
            bridge = EpistemicBridge()
        self.bridge = bridge
        if enable_affective_surface:
            from core.affect import AffectiveSurface
            self._affect_surface = AffectiveSurface()
        else:
            self._affect_surface = None

    def generate(self, prompt: str, task_type: str = "general") -> LoopResult:
        # 1) boutons du tour = état courant + overrides de tâche
        knobs_used = apply_task_overrides(self.state.knobs, task_type)

        # 2) garde anti carry-over inter-prompts
        if self.enable_carryover_guard and self.state.history:
            prev_prompt = self.state.history[-1].prompt
            if carryover_intrusion(prev_prompt, prompt) > self.thresholds.max_intrusion_prev_prompt:
                self.state.last_topic_signature = []
                self.state.last_prompt_keywords = []

        # 3) boutons -> options (correctif options{} appliqué dans le client)
        options = self.mapping.to_generation_options(knobs_used)

        # 4) génération
        output = self.llm.generate(prompt, options)

        # 5) métriques cheap RÉELLES sur la sortie
        cheap = hedge_score(prompt, output)
        truncated = truncation_suspect(output, options["num_predict"], self.thresholds.trunc_margin)
        cheap["truncated"] = float(truncated)

        # 6) modulation (si période réfractaire écoulée) : réactif -> garde-fous -> EWMA
        # RÉALIGNEMENT (2026-07-18, décision Simon) : la politique réactive ajuste
        # l'ÉTAT DE BASE (self.state.knobs), PAS les boutons surchargés du tour.
        # Les task overrides sont des masques transitoires de projection ; dans le
        # canon `conscious` ils fuyaient dans l'état persistant via l'EWMA (design
        # hérité d'un programme corrompu — cf. BUILD_STATUS). Ici : les métriques
        # observées corrigent la personnalité de base, le masque reste un masque.
        modulated = False
        epistemic: Optional[Dict[str, float]] = None
        if self.bridge is not None:
            epistemic = self.bridge.derive(output, options, cheap)
        if refractory_ok(self.state, self.smoothing):
            reactive = decide_next_knobs(self.state.knobs, cheap)
            if self.controller is not None and epistemic is not None:
                # pont P2 : P+I pilote δr/τc sur signaux réels ; réactif garde ρ/κ.
                # δr/τc s'appliquent DIRECTEMENT (comme dans le framework source) :
                # la stabilité du P+I vient de ses bandes + fuite + anti-windup ;
                # l'hystérésis externe (0.05) bloquait ses petits pas (~0.02/tour)
                # — constaté en génération réelle le 2026-07-18, δr/τc figés.
                pi_knobs = self.controller.step(
                    self.state.knobs,
                    coherence=epistemic["coherence"],
                    fit=epistemic["fit"],
                    pressure=epistemic["pressure"],
                )
                self.state.knobs.delta_r = pi_knobs.delta_r
                self.state.knobs.tau_c = pi_knobs.tau_c
                # ρ/κ : chemin réactif classique (garde-fous + EWMA) ; δr/τc passés
                # à leur valeur courante ⇒ l'EWMA les laisse intacts.
                target = Knobs(rho=reactive.rho, kappa=reactive.kappa,
                               delta_r=self.state.knobs.delta_r,
                               tau_c=self.state.knobs.tau_c)
            else:
                target = reactive
            guarded = clamp_and_hysteresis(self.state, target.as_dict(), self.smoothing)
            self.state.ewma_update(guarded, alpha=self.smoothing.ewma_alpha)
            modulated = True

        # 7) surface affective optionnelle : AFFICHAGE de la valence dérivée des
        #    signaux réels — ne pilote rien (cf. core/affect.py). Comme dans le
        #    canon : appendue à la sortie, jamais silencieusement injectée avant.
        affect: Optional[Dict[str, float]] = None
        if self._affect_surface is not None and epistemic is not None:
            affect = self._affect_surface.derive(epistemic)
            output = f"{output}\n\n{self._affect_surface.render(affect)}"

        # 8) mémoire légère
        self.state.push(prompt=prompt, output=output, metrics=cheap)

        return LoopResult(
            output=output,
            options=options,
            knobs_used=knobs_used.as_dict(),
            knobs_next=self.state.knobs.as_dict(),
            metrics=cheap,
            truncated=truncated,
            modulated=modulated,
            epistemic=epistemic,
            affect=affect,
        )


# --------------------------------------------------------------------------
# Autopilote : régulateur P+I sur la dynamique synthétique (démo + tests)
# --------------------------------------------------------------------------
def run_autopilot(steps: int = 40, knobs: Optional[Knobs] = None,
                  control_cfg=None, lambda_cfg=None) -> List[Dict[str, float]]:
    """Fait tourner le contrôleur P+I sur les mesures synthétiques (measures.py).

    Retourne la trajectoire (une ligne par pas). Aucun texte, aucun LLM : c'est
    la preuve de la loi de commande, pas une génération.
    """
    from core.control.controller import PIController, ControlConfig
    from core.control.phase import PolicyLambda, LambdaConfig
    from core.control.measures import measure_coherence, measure_pressure, measure_fit, measure_tension

    k = (knobs or Knobs(rho=0.5, delta_r=0.9, tau_c=0.3, kappa=0.6))  # δr volontairement saturé
    pi = PIController(control_cfg or ControlConfig())
    lam = PolicyLambda(lambda_cfg or LambdaConfig())

    traj: List[Dict[str, float]] = []
    for step in range(1, steps + 1):
        coh = measure_coherence(k.rho, k.delta_r, k.tau_c)
        press = measure_pressure(k.delta_r, k.tau_c)
        fit = measure_fit(coh, press)

        lam_active, k.tau_c = lam.step(coh, k.tau_c)
        k = pi.step(k, coherence=coh, fit=fit, pressure=press)

        coh1 = measure_coherence(k.rho, k.delta_r, k.tau_c)
        press1 = measure_pressure(k.delta_r, k.tau_c)
        fit1 = measure_fit(coh1, press1)
        tens1 = measure_tension(coh1, fit1, press1)
        traj.append({
            "step": step, "coherence": coh1, "fit": fit1, "pressure": press1,
            "tension": tens1, "rho": k.rho, "delta_r": k.delta_r, "tau_c": k.tau_c,
            "lambda": float(lam_active), "pressure_i": pi.pressure_i,
        })
    return traj
