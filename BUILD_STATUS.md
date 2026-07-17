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
| P1 | Contrôleur P+I fuyant | `core/control/controller.py` | `lyra_framework_bundle/src/run_loop3.py:59-130` |
| P1 | Boucle réelle + autopilote | `core/loop.py` | consolidation |
| P2 (acompte) | Politique de phase λ | `core/control/phase.py` | `lyra_framework_bundle/.../policies.py` |

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

**Chantier P2 = le pont :** remplacer les mesures synthétiques par des signaux
épistémiques dérivés des vraies métriques (cohérence/fit/pression réels), pour que
le P+I régule la vraie génération. Ne PAS faire semblant que measures.py mesure du
réel (charte §1, §4).

## Stubs — dossiers-ancres, à construire

| Phase | Dossier | Quoi | Source (audit) — mode |
|---|---|---|---|
| P2 | `core/topology/` | κ/ρ + Betti GF(2) + garde de phase | `Lyra_Core` (+`Topologie`) — porter+dédup ; **recalibrer κc** |
| P3 | `memory/graph/` | nemeton : GraphBackend + deltas + rollback + injecteur | `Lyra_Uni_0_2`, `lyra_clean_bis` — porter |
| P3 | `memory/ecology/` | pouponnière / journal d'oubli / compost + réveil différé | `session_2/LyrArc` — **ré-impl.** (4 bugs) |
| P3 | `memory/cbr/` | Memento (CBR) + 4 stratégies de navigation | `session_2/IspaceNav.zip` (+ client `bundle_lyra`) — porter |
| P4 | `explore/esmm/` | gap→cycle→consensus→graphe | `lyra_clean_bis/services/esmm` — **débuguer** (3 causes : amorcer le graphe ; `get_embedding`→`get_embeddings` ; consensus par-modèle) |
| P5 | `agency/tools/` | function-calling + auto-plugins + SilenceØ | `session_2/LyrAgent` — **ré-impl.** (pas de `eval()`) |
| P6 | `app/` | serveur FastAPI unifié | `lyra_clean_bis` (socle) — porter |
| P7 | `eval/` | juge **pairwise** + harnais + NSGA-II + logging forensique | `LLM_asa_judge`, `lyra_clean/evaluation`, `Lyra_Core/bench/ga_search.py` |
| — | `research/` | orbites FLOATLAP, métriques fractales, calibrations | `session_2/tranzit` — exploratoire |

## Quick wins restants (fort levier, cf. plan §7)

- ⭐ **P4 « fix once »** : `get_embedding`→`get_embeddings` puis relancer un run ESMM
  pour voir enfin des triplets. ~5 min de code, débloque la pépite n°1.
