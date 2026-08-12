# BUILD STATUS — où en est l'édification

Pont entre le **plan directeur** (`docs/PLAN_EDIFICATION.md`) et le code. Tenu à jour
à chaque phase. Les audits détaillés (43 documents, avec numéros de ligne et bugs)
vivent dans le dossier d'audit `../audits_en_cours/` (lots 1 & 2) — s'y référer pour
chaque brique à extraire.

## Fait ✅ (testé)

| Phase | Brique | Fichiers | Source portée |
|---|---|---|---|
| P0 | Squelette + charte + vocabulaire | `manifeste/`, `pyproject.toml` | plan §3–§5 |
| P0 | Boutons ρ/δr/τc/κ + mapping (source unique) | `core/knobs.py` | `conscious/config.py` |
| P0 | Correctif `options{}` | `core/llm.py` | `bundle_lyra/gemma_bridge_v2.py` |
| P1 | Métriques cheap | `core/metrics/cheap.py` | `conscious/metrics/cheap.py` |
| P1 | Garde-fous (clamp/hystérésis/réfractaire) + EWMA | `core/control/guards.py`, `core/state.py` | `conscious/guards.py,state.py` |
| P1 | Politique réactive | `core/control/reactive.py` | `conscious/policies/modulator.py` |
| P1 | Contrôleur P+I fuyant (**gains calibrés B03+P1P2** ; critères §8 → `tests/test_control_criteria.py`) | `core/control/controller.py` | `lyra_framework_bundle/src/run_loop3.py` + `docs/STARTER_KIT_ATELIER_B03_P1P2.md` |
| P1 | Boucle réelle + autopilote | `core/loop.py` | consolidation |
| P2 (acompte) | Politique de phase λ | `core/control/phase.py` | `lyra_framework_bundle/.../policies.py` |
| **P3** | Nemeton : graphe typé + **deltas auditables/rollback** + bornes bruyantes + compaction + primitif `is_novel_link` k=2 (Songe §1d) | `memory/graph/store.py` | design `lyra_clean_bis` (deltas) + famille Uni ; **un seul** chemin de degré (bug double-comptage exclu) |
| **P3** | Injecteur nemeton **borné** (jamais de graphe entier dans un prompt) | `memory/graph/injector.py` | `Lyra_Uni_0_2/nemeton_prompt_injector.py` |
| **P3** | Écologie mémorielle : pouponnière/journal d'oubli/compost + **réveil différé** + réveil du compost — les **4 bugs LyrArc explicitement exclus** | `memory/ecology/ecology.py` | ré-impl. du design `session_2/LyrArc` |
| **P3** | Memento (CBR cosinus) + Navigator 4 stratégies, `Suggestion` à champs explicites (bug `/ispace/suggest` exclu) | `memory/cbr/memento.py` | port du design `session_2/IspaceNav.zip` |
| **P4** | ESMM : lacunes (isolated/unstable/bridge/contradiction) → exploration multi-modèles séquentielle → **consensus sémantique à 2 niveaux** → graphe + cochaîne épistémique v1. Les 3 causes racines historiques exclues par construction + la **4ᵉ découverte en live** (impasse de l'accord lexical inter-modèles) résolue par matcher mxbai τ=0.78. **Premier run productif de l'histoire du projet** : 6 triplets consensuels commis (gemma3+mistral+llama3.1) | `explore/esmm/` (triplets, gaps, consensus, matcher, orchestrator, **textsim, relations**) + `core/embeddings.py` | ré-impl. du design `lyra_clean_bis/services/esmm` + **récolte EPP_Verdict** (cascade ADR-011-v2, groupes de relations ADR-006) |

Preuves : `python -m pytest` (dont `test_modulation.py` = la modulation est réelle,
`test_controller.py` = le P+I régule et reste borné).

## Note d'architecture (importante, honnête)

Il y a **deux** chemins de modulation, volontairement séparés tant que le pont P2
n'est pas fait :

1. **Réactif** (`reactive.py`, chemin RÉEL de `LyraLoop`) : de vraies métriques
   cheap sur une vraie génération pilotent les boutons.
2. **P+I** (`controller.py`, `run_autopilot`) : régule une dynamique épistémique
   **synthétique** (`core/control/measures.py`, formules-jouets honnêtement
   étiquetées, issues de `lyra_framework_bundle`).

**Pont P2 : FAIT (2026-07-18)** — `core/control/bridge.py` dérive
coherence/fit/pressure/tension de la génération réelle ; `LyraLoop(controller=…)`
active le mode pont (P+I → δr/τc en application directe ; réactif → ρ/κ).
**Validé en génération réelle** (gemma3 via Ollama : δr 0.300→0.357 en 3 tours
sous pression réelle 0.20 < consigne 0.45). `measures.py` ne sert plus qu'à
l'autopilote (démo/tests de la loi de commande), comme étiqueté. Reste P2 :
volet topologie (κ/ρ + Betti + calibration κc) et calibration du pont
(`fit_gain`) sur campagne réelle.

**Quirk hérité du canon — RÉSOLU (décision Simon, 2026-07-18)** : dans le canon
`conscious`, les *task overrides* fuyaient dans l'état persistant via l'EWMA
(porté trop fidèlement d'un programme corrompu). Réaligné : la politique réactive
module désormais l'**état de base** (`self.state.knobs`) ; les overrides restent
des **masques transitoires de projection** du tour. Preuve :
`tests/test_modulation.py::test_task_overrides_do_not_leak_into_persistent_state`.

## Stubs — dossiers-ancres, à construire

| Phase | Dossier | Quoi | Source (audit) — mode |
|---|---|---|---|
| P2 | `core/topology/` | κ/ρ + Betti GF(2) + garde de phase | **REPORTÉ (décision Simon 2026-07-18)** : un programme plus abouti existe hors périmètre — sa conclusion : « je me compliquais la vie pour rien ». Investigation à part entière quand Simon l'ouvrira ; ne PAS porter l'ancien pipeline d'ici là |
| ~~P3~~ | ~~`memory/`~~ | **FAIT** — voir tableau ci-dessus. Notes de périmètre : implémentation mémoire pure-stdlib (persistance JSON) ; le Strategy multi-backend NetworkX/igraph d'Uni_0_2 volontairement simplifié en **une** implémentation propre derrière la même API (charte §5 — on ajoutera un backend si un besoin de perf le prouve) ; pas d'embeddings encore (arrivent avec le pont P2/éval) | — |
| ~~P4~~ | ~~`explore/esmm/`~~ | **FAIT** — voir tableau ci-dessus. Restes : cochaîne 5D complète (v1 = support/diversité/sources), adaptation dynamique du plan de cycles, recalibration τ_obj sur campagne large | — |
| P5 | `agency/tools/` | function-calling + auto-plugins + SilenceØ | `session_2/LyrAgent` — **ré-impl.** (pas de `eval()`) |
| P6 | `app/` | serveur FastAPI unifié | `lyra_clean_bis` (socle) — porter |
| P7 | `eval/` | **V6 ARRÊTÉE AVANT CALIBRATION** : Gemma lit SOURCE + traces puis répète SOURCE au lieu de vérifier/juger. Décision requise : evidence pack déterministe (recommandé) ou juge agentique plus capable | `docs/P7_V6_STATUS.md` |
| — | `research/` | orbites FLOATLAP, métriques fractales, calibrations | `session_2/tranzit` — exploratoire |

## Bannière « La Jachère » — vie hors-tâche (nouveau flux, cf. plan §8·bis)

Flux qui **mûrit après P3/P4/P7** (il les consomme). Détail : `docs/BANNIERE_LA_JACHERE.md`.

| Organe | Quoi | Statut | Source / ancrage |
|---|---|---|---|
| 1 — Pouponnière évolutive | le modèle cultive/élague/adopte ses modules de scaffold (harness auto-généré, génétique, adaptatif par-modèle) | **fondé, constructible après P3/P7** — maison provisoire `evolve/` | survey `docs/2607.13104v1.pdf` (Population-Based scaffolding SI) + `docs/2607.06906v1.pdf` (Harness Effect) + `docs/2607.14159v1.pdf` (MemoHarness : 6 dims + banc 2 couches + hors-ligne/en-ligne) + pouponnière `LyrArc` + NSGA-II `Lyra_Core` |
| 2 — Le Songe | phases de « sommeil » : consolidation (Knowledge Seeding/replay) + Dreaming (curriculum synthétique auto-généré) | **FONDÉ** (papier *LMs Need Sleep*). **Palier 1** (rêve scaffold/mémoire) constructible sans entraînement, après P3 ; **Palier 2** (consolidation paramétrique LoRA) nécessite une voie de fine-tuning local | `docs/Language_Models_Need_Sleep_...pdf` ; s'appuie sur nemeton (P3), journal d'oubli, FLOATLAP, phases κ/ρ (NREM↔REM) ; **métriques figées : `docs/METRIQUES_SONGE.md`** |

## Organes & ponts (doctrine inter-projets)

Décision Simon 2026-07-18 : `lyra_reborn` = OS cognitif ; **EPP_Verdict** =
moteur d'attestation (organe indépendant, ESMM mûr — jamais audité, hors lots) ;
**Origami_Transformer** = instrument métrologique (géométrie de Fisher ; H-C v5
pré-enregistrée = signature de la contestation épistémique). Indépendance
stricte, ponts = contrats minces dégelés sur validation uniquement. Détail :
`docs/ORGANES_ET_PONTS.md`. D'autres organes viendront.

## Cap d'application n°1 — « La Vigie » (doctrine 2026-07-19)

Doctrine de l'Architecte versée (`manifeste/DOCTRINE_ARCHITECTE.md`) : le goulot
est l'ATTENTION → présence externe. POC : `docs/LA_VIGIE.md` — veille +
brouillons X validés à la main (files Audit/Amplification, Jachère Sociale =
l'écologie existante, labels = fitness de la Pouponnière). Règles dures : zéro
écriture réseau, la cible est l'affirmation jamais la personne. V0 constructible
(P3+P4+embeddings faits ; entrées gratuites arXiv/RSS/captures). Critère
d'arbitrage double désormais : solidité interne ET/OU présence externe.

**V0-q (2026-08-09) :** frontière de quarantaine Lyra implémentée dans
`agency/tools/vigie/quarantine.py` : subprocess sans shell, environnement sans
secrets hérités, identité liée au SHA-256, schéma fermé et échec explicite vers
`QUARANTINE`. Tests de frontière et transport hostile dans
`tests/test_vigie_quarantine.py`. Le sidecar autonome EPP est implémenté sans
import de la base ou du pipeline historique, avec connexion directe à Ollama
sur `127.0.0.1`, modèles explicites et unanimité pour `PASS/REJECT`. Sa qualité
sur modèles live n'est pas encore revendiquée. Voir `docs/VIGIE_QUARANTINE.md`.

## Quick wins restants (fort levier, cf. plan §7)

- ~~⭐ P4 « fix once »~~ **FAIT et dépassé** : l'ESMM ré-implémenté produit ses
  premiers triplets consensuels (cf. tableau P4). La découverte en prime : le
  « fix once » n'aurait PAS suffi — l'accord lexical inter-modèles était une
  4ᵉ cause racine invisible à l'audit, résolue par consensus sémantique.
