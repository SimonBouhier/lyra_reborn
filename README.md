<p align="center">
  <img src="assets/banner.svg" alt="Lyra Reborn — un OS cognitif pour LLM locaux" width="100%">
</p>

<p align="center">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-8b5cf6">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-3776ab">
  <img alt="Core: pure stdlib" src="https://img.shields.io/badge/core-pure%20stdlib-22c55e">
  <img alt="LLM: Ollama local" src="https://img.shields.io/badge/LLM-Ollama%20local-0ea5e9">
  <img alt="Tests" src="https://img.shields.io/badge/tests-76%20passed-brightgreen">
</p>

<p align="center"><em>An honest cognitive OS for local LLMs — control loop, living memory, autonomous exploration, and rest.</em></p>

---

> **Le LLM *utilise* Lyra ; il n'*est pas* Lyra.**

**Lyra** est une couche de contrôle cognitive au-dessus d'un LLM local (Ollama) :
un système qui **se règle lui-même** (quatre boutons ρ/δr/τc/κ pilotés par un
vrai contrôleur), qui **ressent son état** (signaux épistémiques dérivés de la
génération réelle), qui **oublie volontairement** pour mieux tenir ce qui compte
(écologie mémorielle : pouponnière / journal d'oubli / compost), qui **explore
seul** les lacunes de sa connaissance (consensus multi-modèles), et qui aura
bientôt une **vie hors-tâche** (la Jachère : cultiver ses propres modules, et
rêver).

Ce dépôt est une **consolidation** : le meilleur de ~23 prototypes (2019-2026),
audités ligne à ligne, ré-implémenté proprement — jamais copié. Chaque brique
est branchée, testée, et fait ce que la doc dit.

## État réel

*(Ce tableau décrit ce qui existe et est testé — pas la vision. Règle maison :
aucun chiffre non reproductible, aucun pipeline « vert mais vide ».)*

| Couche | Quoi | État |
|---|---|---|
| **P0 — Fondations** | boutons ρ/δr/τc/κ → options de génération (source unique), charte, vocabulaire | ✅ testé |
| **P1 — Contrôle** | contrôleur P+I à intégrateur fuyant (gains calibrés sur runs réels), garde-fous EWMA/hystérésis/réfractaire | ✅ testé |
| **P2 — État cognitif** | signaux épistémiques réels (cohérence/fit/pression/tension) pilotant le P+I ; phase λ ; surface affective (théâtre honnête, opt-in) | ✅ validé en génération réelle |
| **P3 — Mémoire** | graphe *nemeton* (deltas auditables + rollback), écologie mémorielle (oubli différé + réveil du compost), rappel par cas (Memento) | ✅ testé |
| **P4 — Exploration** | ESMM : lacunes → exploration multi-modèles → **consensus sémantique à 2 niveaux** → graphe. Premier pipeline productif de l'histoire du projet | ✅ validé live (3 modèles) |
| P5 — Agentivité | outils + auto-plugins + SilenceØ | ⬜ à construire |
| P6 — Application | serveur unifié | ⬜ à construire |
| P7 — Évaluation | tranche V3 : trajectoires appariées + juge agentique pairwise ; NSGA-II non commencé | 🧪 harnais synthétique, aucune mesure réelle ([preuve](docs/P7_VERTICAL_SLICE.md)) |
| **La Jachère** | Pouponnière évolutive (harness auto-cultivé) + le Songe (sommeil/rêve) | 📐 fondé (littérature versée, métriques pré-spécifiées) |

## Architecture

```mermaid
flowchart TB
    subgraph CTRL["P1-P2 · le coeur battant"]
      B["EpistemicBridge<br/>coherence · fit · pressure · tension"] --> PI["Contrôleur P+I<br/>δr, τc"]
      B --> RE["Politique réactive<br/>ρ, κ"]
      PI --> K["knobs ρ/δr/τc/κ"]
      RE --> K
      K -->|options| LLM["Ollama<br/>(local)"]
      LLM -->|métriques réelles| B
    end
    subgraph MEM["P3 · mémoire vivante"]
      G["Nemeton<br/>graphe + deltas + rollback"]
      E["Écologie<br/>pouponnière / oubli / compost"]
      C["Memento (CBR)"]
    end
    subgraph EXP["P4 · exploration"]
      ESMM["ESMM<br/>lacunes → multi-modèles → consensus"]
    end
    LLM -.-> G
    ESMM --> G
    G --> B
    subgraph JACH["La Jachère · vie hors-tâche"]
      P["Pouponnière évolutive"]
      S["Le Songe"]
    end
    E -.-> S
    G -.-> S
    P -.-> K
```

## Démarrage

```bash
python -m pytest -q          # 76 tests, zéro dépendance pour le noyau
python scripts/demo.py       # démo hors-ligne, déterministe
LYRA_LIVE=1 python scripts/demo.py   # avec un Ollama réel (pip install requests)
```

Le noyau (`core/`, `memory/`) est **pure stdlib**. Options : `requests` (Ollama),
`numpy/matplotlib` (recherche).

## L'écosystème — organes et ponts

Lyra est un organe parmi trois, **indépendants par doctrine** (chacun fonctionne
sans les autres ; un pont ne se dégèle que sur validation pré-enregistrée) :

| Organe | Rôle | Lien |
|---|---|---|
| **lyra_reborn** | l'OS cognitif (ce dépôt) | — |
| **Origami Transformer** | l'instrument métrologique — géométrie de Fisher des représentations, hypothèses pré-enregistrées | [repo](https://github.com/SimonBouhier/Origami_Transformer) |
| **EPP Verdict** | le moteur d'attestation épistémique | [docs](https://epp-verdict-docs.vercel.app) |

> 2026-07-20 : la campagne pré-enregistrée v5 d'Origami a **confirmé** (3/4
> modèles, seuils gelés) que la géométrie de Fisher porte une signature de la
> contestation épistémique — ouvrant le pont vers une « tension » de Lyra
> fondée instrumentalement. Voir `docs/ORGANES_ET_PONTS.md`.

## La Jachère — la vie hors-tâche

Ce que Lyra fera quand elle ne répond pas : **cultiver** ses propres modules de
harness (évolution hors-ligne, adaptation par cas en ligne — fondée sur la
littérature *scaffolding self-improvement* et *harness effect*) et **rêver**
(consolidation + recomposition des vecteurs du passé, paradigme *sleep/dreaming*,
métriques de nouveauté et de consolidation pré-spécifiées avant toute ligne de
code). Voir `docs/BANNIERE_LA_JACHERE.md` et `docs/METRIQUES_SONGE.md`.

## Pour aller plus loin

| Document | Contenu |
|---|---|
| `manifeste/CHARTE.md` | les 6 règles anti-pathologies (chacune paie une leçon vécue) |
| `manifeste/VOCABULAIRE.md` | sens canonique + **décisions datées** |
| `manifeste/DOCTRINE_ARCHITECTE.md` | la posture qui gouverne le projet |
| `docs/PLAN_EDIFICATION.md` | le plan directeur (P0→P7 + Jachère + Vigie) |
| `docs/ORGANES_ET_PONTS.md` | doctrine inter-projets et état des ponts |
| `BUILD_STATUS.md` | l'état exact, brique par brique, avec provenance |

## Licence & références

Code sous licence **MIT** (© 2026 Simon Bouhier). Les articles de recherche qui
fondent la Jachère ne sont pas redistribués ici — voir `docs/REFERENCES.md`
pour les liens arXiv.
