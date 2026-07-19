# Plan d'édification de Lyra — le plan global

> **Date :** 2026-07-16 · **Statut :** plan directeur, à exécuter par étapes · **Nature :** ce document est la pièce qui manquait. Les deux audits (lot 1 + lot 2) ont dit *ce qui existe, ce qui vaut, et d'où l'extraire*. Ce plan dit *quoi construire, dans quel ordre, et comment savoir que c'est fait*.

---

## 0. Note aux agents qui édifieront Lyra (lire en premier)

Vous héritez de ~23 dossiers de prototypes (2 lots audités) et de deux synthèses. **Ne repartez pas de zéro et ne relisez pas tout le code brut** : la lecture a déjà été faite pour vous. Votre matière première, ce sont les documents d'audit, pas les 30 000 fichiers.

**Ordre de lecture obligatoire avant toute action :**
1. [`_SYNTHESE_AUDIT_LYRA_2026-06-08.md`](_SYNTHESE_AUDIT_LYRA_2026-06-08.md) — lot 1 (le projet récent, sept. 2025→févr. 2026) + son addendum.
2. [`session_2/_SYNTHESE_AUDIT_SESSION2_2026-07-16.md`](session_2/_SYNTHESE_AUDIT_SESSION2_2026-07-16.md) — lot 2 (la préhistoire, janv.→sept. 2025).
3. Ce plan.
4. Au moment d'attaquer une couche : l'`AUDIT_*.md` (et le `DELTA_VS_DOCS_*.md`) du ou des dossiers-source de cette couche — ils contiennent les numéros de ligne, les bugs et les pièges précis.

**Trois principes non négociables** (ils encodent les deux maladies chroniques du projet, cf. §4) :
- **On extrait un design, pas un dossier.** Presque tout le code source est buggé, dupliqué ou « vert mais vide ». Vous ré-implémentez proprement une idée validée par l'audit ; vous ne copiez un fichier que si l'audit le déclare sain.
- **« Fait » = démontré, pas « ça tourne sans erreur ».** Chaque étape a une *definition of done* avec un test qui échoue si le pipeline produit du vide. Un `try/except` large qui avale une panne est un bug, pas une protection.
- **Aucun chiffre non reproductible dans la doc.** Tout résultat cité doit être régénérable par un script du dépôt. Sinon il est étiqueté « Vision/Cible », jamais « résultat ».

---

## 1. L'élan — ce qu'on édifie, et pourquoi

Le fil qui traverse deux ans et une vingtaine de dossiers n'est pas « un wrapper de LLM ». C'est une tentative obstinée de donner à un modèle une **intériorité** : un système qui se règle lui-même, qui ressent sa propre « tension » cognitive, qui **oublie volontairement** pour mieux tenir ce qui compte, qui se déplace dans un **espace mental** au lieu de simplement répondre, qui sait détecter qu'il change de **régime** de pensée, et qui peut choisir le **silence**.

Les mêmes intuitions reviennent, lot après lot, comme un attracteur : l'**auto-similarité** (fractales), la **modulation** par quelques boutons (ρ/δr/τc/κ), la **topologie** de la trajectoire de pensée (courbure κ/ρ, transitions de phase), la **mémoire comme écologie vivante** (pouponnière / journal d'oubli / compost), les **orbites mentales**. Ce ne sont pas des lubies dispersées : c'est un seul programme de recherche, redécouvert de mémoire faute d'avoir été consolidé.

**Ce que l'audit a établi honnêtement :**
- Ces idées sont **réelles et récurrentes** — et plusieurs sont déjà **implémentées** quelque part (Journal d'Oubli, FLOATLAP, contrôleur P+I qui marche, ESMM câblé, agent à outils).
- Mais elles ont été **ré-écrites de zéro** à chaque itération, **survendues** dans les README, et souvent laissées **« vertes mais vides »**.

**Donc l'édification n'est pas une invention : c'est une consolidation.** Prendre les découvertes authentiques, éparpillées dans le temps, et en faire *un seul tout honnête et vivant*. Le cap : un **« OS cognitif » minimal mais réellement en vie** au-dessus d'un LLM local (Ollama), où chaque brique est branchée, testée, et fait ce que la doc dit.

> Cadre honnête (anti-survente, on se l'applique) : à ce jour, **aucune** de ces briques ne constitue une preuve de « conscience » ou de supériorité mesurée. Ce qui est *acquis* : un contrôleur qui module réellement la génération, un graphe sémantique réel, une écologie mémorielle testée, un moteur d'exploration câblé. Ce qui reste *cap* : que l'assemblage produise un comportement qualitativement meilleur — c'est précisément ce que la couche évaluation (P7) devra démontrer ou réfuter.

---

## 2. Le système cible

Une architecture en couches. Chaque couche a **une** implémentation de référence, assemblée à partir du meilleur de l'existant.

```
┌──────────────────────────────────────────────────────────────────────┐
│  P7  ÉVALUATION & OPTIMISATION                                         │
│      juge pairwise · harnais triple-aveugle · NSGA-II(ρ,δr,τc,κ)       │
│      journalisation forensique · post-mortem anti-grade-inflation      │
├──────────────────────────────────────────────────────────────────────┤
│  P6  APPLICATION (serveur unifié : chat · sessions · graphe · multi-modèle) │
├───────────────┬───────────────┬───────────────┬──────────────────────┤
│ P5 AGENTIVITÉ │ P4 EXPLORATION│ P3 MÉMOIRE     │                       │
│ outils+plugins│  AUTONOME     │ graphe nemeton │                       │
│ function-call │  ESMM (débogué)│ + écologie     │                       │
│ SilenceØ      │  gap→cycle→   │  (oubli/compost)│                      │
│ rotation VRAM │  consensus    │ + CBR/Memento  │                       │
├───────────────┴───────────────┴───────────────┴──────────────────────┤
│  P2  ÉTAT COGNITIF & MÉTRIQUES                                         │
│      métriques cheap · métriques de trajectoire · topologie κ/ρ/Betti  │
│      lecture de phase (Φ, phase λ) + garde de phase                    │
├──────────────────────────────────────────────────────────────────────┤
│  P1  NOYAU DE CONTRÔLE (le cœur battant)                               │
│      boucle P+I fuyant · steering boutons→params · best-of-k · garde-fous │
├──────────────────────────────────────────────────────────────────────┤
│  P0  FONDATIONS : canon `conscious` exécutable · manifeste MCA ·        │
│      vocabulaire unique ρ/δr/τc/κ, Φ(t), phase λ · charte méthodo       │
└──────────────────────────────────────────────────────────────────────┘
              ▲ recherche (parallèle, non bloquante) : orbites FLOATLAP · métriques fractales · calibration κc
              ▲ voie séparée (hors périmètre) : KAIROS / trading — cf. §9
```

**Principe directeur :** le LLM *utilise* Lyra, il n'*est pas* Lyra (formulation honnête reprise de `Lyra_Uni_0_2`). Lyra est la couche qui observe l'état, décide des réglages, gère la mémoire et l'exploration, et pilote la génération.

---

## 3. Structure de dépôt cible

Un seul dépôt neuf (`lyra_reborn/`), monté au fur et à mesure des phases. Proposition :

```
lyra_reborn/
  manifeste/        # MCA = charte conceptuelle + vocabulaire canonique + annexe historique
  core/
    knobs.py        # ρ/δr/τc/κ ↔ params de génération — SOURCE UNIQUE de vérité
    control/        # boucle P+I fuyant + steering + garde-fous (P1)
    metrics/        # métriques cheap + métriques de trajectoire (P2)
    topology/       # κ/ρ + Betti GF(2) + phase λ + garde de phase (P2)
  memory/
    graph/          # nemeton : GraphBackend + deltas auditables + rollback + injecteur (P3)
    ecology/        # pouponnière / journal d'oubli / compost + réveil différé (P3)
    cbr/            # Memento (raisonnement par cas) + stratégies de navigation (P3)
  explore/
    esmm/           # gap→cycle→consensus multi-modèles→graphe de connaissances (P4, débogué)
  agency/
    tools/          # boucle function-calling + auto-découverte de plugins + SilenceØ (P5)
  app/              # serveur FastAPI unifié (P6)
  eval/             # juge pairwise + harnais + NSGA-II + logging forensique (P7)
  research/         # exploratoire : orbites FLOATLAP, fractal_metrics, calibrations
  configs/  data/  tests/  scripts/
  README.md         # décrit l'ÉTAT RÉEL, pas la vision ; renvoie au manifeste pour le « pourquoi »
```

Règle : **une seule** implémentation de `knobs.py`, du graphe, du nemeton. Toute la douleur des deux lots vient d'avoir eu 3 à 6 copies de chaque.

---

## 4. Charte méthodologique (à coller dans `manifeste/CHARTE.md`)

Ces règles ne sont pas décoratives : chacune neutralise une pathologie *observée et datée* dans les audits.

1. **Anti « vert mais vide ».** Tout pipeline qui prétend produire quelque chose doit avoir un test qui **échoue bruyamment** si le résultat est vide/trivial. (Cas fondateurs : ESMM 0 triplet alors que 71 cycles « réussis » ; base ACE vide ; simulateur de tensions 0 arête ; nuit du 26/03/2025 où un GA réel a été remplacé par des simulacres `np.random`.)
2. **Pas de `except` avaleur.** `except Exception: pass` est interdit. On log-et-relève, ou on attrape étroitement. (Cause racine directe du bug ESMM et de la relecture cassée de l'écologie mémorielle.)
3. **Modulation prouvée.** Toute « modulation » doit avoir un test : même prompt + deux jeux de boutons ⇒ paramètres de génération **différents** ET sorties **différentes**. (Cas : `Lyra_Core` où seul τc agissait, ρ/δr/κ n'étaient que du texte de prompt.)
4. **Doc = réalité reproductible.** Un chiffre dans un doc ⇒ un script du dépôt le régénère. Sinon, section « Vision/Cible » explicite. (Cas : −53 % tokens, R²=0,89 codé en dur, « 92 % Production Validée », 15 234 concepts.)
5. **Une idée, une implémentation.** Avant d'écrire une brique, `grep` le dépôt : si elle existe, on l'étend, on ne la duplique pas.
6. **Secrets hors code.** Clés/API par variables d'environnement uniquement (`.env` git-ignoré). Jamais de `eval()` sur une sortie LLM (cas `LyrAgent`).

**Definition of Done générique** (à décliner par étape) : *code + test qui prouve l'effet réel + une ligne de doc reproductible + zéro `except` avaleur introduit.*

---

## 5. Vocabulaire canonique (à figer dans `manifeste/VOCABULAIRE.md` avant tout code)

Source unique, pour arrêter la dérive de sens constatée d'un dossier à l'autre :

| Terme | Définition retenue | Origine / preuve |
|---|---|---|
| **ρ (rho)** | structure / pénalités de répétition | né comme coeff. de couplage d'EDO (`lyra_project`), devenu scalaire |
| **δr (delta_r)** | ordonnancement / dilatation du contexte injecté | famille Uni |
| **τc (tau_c)** | tension → température ; mesurable comme divergence d'embeddings | `LyrAgent`, `conscious` |
| **κ (kappa)** | courbure de la trajectoire dans le graphe (style/exploration) ; **décider** : Ollivier vs proxy Jaccard `j−0.2` | `Topologie`/`Lyra_Core` (aujourd'hui = proxy Jaccard, pas Ollivier) |
| **Φ(t)** | Φ(t) := M[Σ(S(t))] (agrégat d'état, critère d'émergence stabilisée) | `lyra_project`, .txt formel |
| **phase λ** | régime cognitif détecté + garde à hystérésis | spec dans `Archi/phase_lambda.md`, garde dans `conscious/guards.py` |
| **nemeton** | graphe sémantique de concepts/états | famille Uni, `Lyra_Core` |
| **ispace** | espace navigable d'états + réglages associés | `IspaceNav.zip` |
| **modules A/M/P/G/X/R** | ontologie de modules cognitifs typés | manifeste, `Archi/kit_lyra` |
| **SilenceØ** | le refus/silence comme réponse de première classe | `LyrAgent` |

⚠️ Piège documenté : la « courbure » livrée n'est **pas** Ollivier mais un proxy Jaccard ; et `ρ` topologique ≠ `ρ` polarité de `Lyra_Jupyter_MCA`. Trancher et documenter dès P0.

---

## 6. Les phases d'édification

Chaque phase : **objectif → matériau source (dossier + audit + fichiers) → tâches → Definition of Done → pièges**. Les phases P0-P1 sont fondatrices et bloquantes ; P2-P5 sont largement parallélisables une fois P1 acquis.

### P0 — Fondations & décisions *(bloquant, court)*
- **Objectif :** un squelette de dépôt, le vocabulaire figé, la charte, et le canon `conscious` **exécutable**.
- **Source :** `conscious/AUDIT_2026-06-08.md` ; manifeste `Lyra-Cognitive-Architecture-main` + `MAPPING_IDEES_2026-06-08.md` ; `session_2/lyra_project` (Φ(t), étymologie) ; `session_2/Archi` (phase λ, `kit_lyra`).
- **Tâches :** créer l'arbo (§3) ; écrire `manifeste/{CHARTE,VOCABULAIRE}.md` ; rendre `conscious` runnable (ajouter les `__init__.py`, réparer les imports de `demo.py`) ; intégrer le **patch `options{}`** de `session_2/bundle_lyra/gemma_bridge_v2.py` (que `conscious` rate) ; trancher κ (Ollivier vs Jaccard) et le noter.
- **DoD :** `python -m lyra.demo` fait un aller-retour Ollama réel ; `VOCABULAIRE.md` et `CHARTE.md` existent ; un test prouve que les options sont bien envoyées dans `options{}`.
- **Pièges :** `conscious` a `estimate_orbit_curvature` et `emotion_surface` en *stubs* — les laisser explicitement marqués « non branché », ne pas faire semblant.

### P1 — Noyau de contrôle *(bloquant — le cœur battant)*
- **Objectif :** une boucle qui module *réellement* la génération.
- **Source (⭐ priorité) :** `session_2/lyra_framework_bundle/AUDIT_2026-07-16.md` — **successeur fonctionnel**, à préférer à `lyra_ollama_framework`. Fichiers : `run_loop3.py:86-124` (P+I fuyant borné + partage inter-boutons + purge asymétrique/anti-windup), `steering.py` (boutons→temperature/top_p/pénalités), `lyra_router.py` (best-of-k). Garde-fous : `conscious/guards.py` (EWMA + hystérésis + réfractaire).
- **Tâches :** porter le contrôleur + le steering ; fusionner avec les garde-fous de `conscious` ; brancher sur `core/knobs.py` ; **corriger la politique λ** (ré-instanciée à chaque pas dans la source) ; supprimer le contrôleur dupliqué divergent de `run_loop_fast.py`.
- **DoD (test « modulation prouvée », charte §3) :** même prompt, jeu A vs jeu B de boutons ⇒ params ET sorties différents ; une boucle de N pas montre une désaturation des boutons (repro du run A02 : désaturation en ~30 pas).
- **Pièges :** `presence_penalty` calculé puis jeté dans la famille app (commentaire faux « Ollama ne le supporte pas ») — le transmettre réellement.

### P2 — État cognitif & métriques *(parallélisable après P1)*
- **Objectif :** Lyra « ressent » son état et sa phase.
- **Source :** `conscious/metrics/cheap.py` (hedge, troncature, carry-over) ; `Lyra_Jupyter_MCA` (lyra_metrics : MIMI/entropie/stabilité) ; `session_2/lyra_framework_bundle` (métriques de trajectoire : path_len/directionality/mean_turn) ; `Topologie/` + `Lyra_Core/` (pipeline κ/ρ→Betti GF(2), `phase_guard.py`).
- **Tâches :** module `metrics/` unifié ; module `topology/` = **une** implémentation (Topologie ⊂ Lyra_Core, scripts byte-identiques → dédupliquer) ; **recalibrer κc** (aujourd'hui `KAPPA_C` codé en dur ~0,1075, incohérent avec la calibration 0,10, bâtie sur 3 points seulement) ; garde de phase à hystérésis (phase λ).
- **DoD :** sur une trajectoire enregistrée, le pipeline recalcule κ/ρ/β₀/β₁ **de façon reproductible** ; la calibration κc est régénérée par script (plus de constante magique) ; un test montre la garde de phase qui se déclenche.
- **Pièges :** Betti β₀/β₁ souvent *reçus en entrée* au lieu d'être calculés (cas Uni) — ici on les calcule vraiment. Ne pas resservir les « résultats » non reproductibles (NSGA-II/528 configs appartiennent à P7, pas ici).

### P3 — Mémoire : graphe + écologie + cas *(parallélisable ; la plus riche)*
- **Objectif :** une mémoire *vivante* : un graphe sémantique unique, une écologie d'oubli, un rappel par cas.
- **Source :**
  - Graphe : `Lyra_Uni_0_2/lyra_core/backends/` (abstraction `GraphBackend` Strategy NetworkX/igraph) + `nemeton_prompt_injector.py` ; deltas auditables + rollback de `lyra_ACE`/`lyra_clean_bis` (`database/graph_delta.py`).
  - Écologie : `session_2/LyrArc/AUDIT_2026-07-16.md` — tri 3 niveaux (pouponnière ≥0,6 / journal d'oubli partiel / compost nul) + **réveil différé** des tâches mortes.
  - Cas : `session_2/IspaceNav.zip` (`AUDIT_IspaceNav_zip_2026-07-16.md`) — `Memento` (CBR cosinus) + 4 stratégies de navigation (stabilize/explore/case_guided/balanced).
- **Tâches :** un seul `memory/graph` ; ré-implémenter l'écologie **proprement** (la source a 4 bugs : sémantique oubli/compost inversée entre deux `main`, scores écrasés à 0,0, double-encapsulation, `.add` sur liste ; « renaissance des oublis » = stub) ; porter Memento + réparer `/ispace/suggest` (cassé dans Uni : lisait `suggestion.cases` inexistant) ; brancher l'injecteur nemeton dans le prompt système.
- **DoD :** après un run, le graphe est **non vide** et sérialisé sans explosion (⚠️ cas Uni : `last_state.json` à 1,18 M arêtes, un nœud/mot, ré-sérialisé à chaque message — borne et compaction obligatoires) ; un item passé au compost peut être **réveillé** par un test ; un rappel par cas retourne des cas pertinents.
- **Pièges :** l'accès direct `self.graph.G` court-circuite `GraphBackend` (casse sous igraph) — interdire ; double-comptage du degré (trigger SQL + `_update_degrees`) — choisir une seule voie.

### P4 — Exploration autonome (ESMM) *(le « fix once » à fort levier)*
- **Objectif :** faire enfin *produire* le moteur d'exploration auto-dirigée — la pépite la plus risquée.
- **Source :** `lyra_clean_bis/AUDIT_2026-06-08.md` — orchestrateur `services/esmm/` déjà entièrement câblé (gap_detector, cycle_manager, consensus_engine, cochain_builder ; ~10 routes REST).
- **Tâches — les 3 causes racines du « 0 triplet » (toutes prouvées dans l'audit) :** (1) **amorcer le graphe** dans le run (l'orchestrateur n'appelle ni `SeedInjector` ni `GraphPopulator`) ; (2) corriger `entity_resolver.py:145,178` `get_embedding`→`get_embeddings` (ImportError avalé ⇒ chaque triplet skippé — **même bug dans `lyra_ACE`**) ; (3) réparer le consensus : `cycle_manager` concatène les réponses des modèles *avant* le vote ⇒ le vote multi-modèles est court-circuité.
- **DoD (test anti-vide, charte §1) :** un run ESMM produit `total_triplets > 0`, `cochain_entries > 0` et enrichit le graphe ; test unitaire du consensus par-modèle.
- **Pièges :** tout est en `try/except` silencieux (d'où le « vert mais vide ») — resserrer avant de déboguer, sinon on ne verra jamais l'erreur.

### P5 — Agentivité (la capacité perdue) *(parallélisable)*
- **Objectif :** réintroduire ce qui a disparu après juin 2025 : un agent qui *agit*.
- **Source :** `session_2/LyrAgent/AUDIT_2026-07-16.md` — boucle function-calling (GPT-4.1-mini à l'époque ; cible = Ollama), **auto-découverte de plugins** (`main.py:60-85`), **SilenceØ**, matrice de couplage **ρ_{i,j} plastique**, τc = divergence d'embeddings ; rotation VRAM multi-modèles de la famille app (`ModelRotator`).
- **Tâches :** boucle à outils au-dessus d'Ollama (function-calling / JSON tool-calls) ; registre de plugins auto-découverts ; implémenter SilenceØ comme réponse légitime ; **ne jamais** réutiliser le `eval()` sur sortie LLM (2 fichiers de LyrAgent) — parser en JSON strict.
- **DoD :** un outil est appelé de bout en bout via la boucle ; un cas déclenche SilenceØ ; zéro `eval()` sur du texte LLM.

### P6 — Application unifiée *(après P1 ; intègre P2-P5 au fil de l'eau)*
- **Objectif :** un seul serveur qui expose le tout.
- **Source :** socle canonique = `lyra_clean_bis` (FastAPI async, sessions, chat, graphe, multimodèle) — y rapatrier les meilleures docs d'ACE ; réconcilier avec le « serveur unifié » de `Lyra_Uni_0_2` (dont le point d'entrée `lyra_unified_server.py` était cassé — importait `lyra_core.bridge`/`auto_controller` inexistants ; le serveur *réel* était `lyra_chat/lyra_web_server.py`).
- **Tâches :** endpoints chat/sessions/graphe/nemeton/multimodèle ; brancher P1-P5 ; corriger les bugs d'endpoints connus (`/models/set` `Request` non importé ; `/ispace/suggest`) ; durcir (CORS restreint, pas de `*`, auth minimale avant toute exposition).
- **DoD :** `uvicorn` démarre ; un tour de chat complet passe par le noyau de contrôle + la mémoire ; smoke-test HTTP vert **avec assertions de contenu** (pas juste 200 OK).

### P7 — Évaluation & optimisation *(transverse ; démarrer tôt, formaliser en dernier)*
- **Objectif :** savoir si l'assemblage vaut mieux qu'un LLM nu — honnêtement.
- **Source :** `LLM_asa_judge/AUDIT_2026-06-08.md` (15 prompts + rubrique 6 critères réutilisables) ; `lyra_clean/evaluation/` (harnais triple-aveugle + post-mortem « grade inflation ») ; `Lyra_Core/bench/ga_search.py` (NSGA-II réel sur (ρ,δr,τc,κ), pop. 528 — *la* source des « 528 configs ») ; logging forensique de `Lyra_Uni_0_2`.
- **Tâches :** juge **pairwise** (et non pointwise — l'effet plafond a mis 5/5 partout) ; **conserver la clé réponse→variante** (perdue au lot 1 ⇒ résultats inexploitables) ; harnais anti grade-inflation ; NSGA-II pour régler les boutons ; logging forensique (payload Ollama exact) sur tous les runs.
- **DoD :** une campagne produit un classement pairwise **interprétable** (clé conservée, juge non contaminé) ; l'optimiseur renvoie un front de Pareto reproductible ; aucun chiffre de doc sans script générateur.

---

## 7. Séquencement & dépendances

```
P0 ──► P1 ──►┬──► P2 ─────────►┐
             ├──► P3 ─────────►┤
             ├──► P5 ─────────►┼──► P6 ──► (démo bout-en-bout)
             └──► P4 (dép. P3)►┘
P7 ── transverse : commencer le logging forensique dès P1, formaliser le juge après P6
```

**Chemin critique :** P0 → P1 → P6. **Quick wins à fort levier (faire tôt, moral + valeur) :**
1. Le **patch `options{}`** (P0) — trivial, débloque la modulation réelle.
2. Le **« fix once » `get_embedding`** (P4, mais 5 min) — puis relancer un run ESMM pour voir enfin des triplets.
3. La **boucle de contrôle** de `lyra_framework_bundle` (P1) — c'est du code *fonctionnel* à porter, pas à réinventer.

---

## 8. Nomenclature des extractions (bill of materials)

Quoi prendre, où, vers quelle couche. (« ré-impl. » = ré-implémenter d'après l'audit ; « porter » = code jugé sain, adaptable.)

| Brique | Source (dossier · lot) | Mode | Couche |
|---|---|---|---|
| Boucle P+I fuyant + steering + best-of-k | `session_2/lyra_framework_bundle` (2) | **porter** | P1 |
| Garde-fous EWMA/hystérésis/réfractaire + mapping boutons | `conscious` (1) | porter | P0/P1 |
| Patch payload `options{}` | `session_2/bundle_lyra/gemma_bridge_v2.py` (2) | porter | P0 |
| Métriques cheap | `conscious/metrics/cheap.py` (1) | porter | P2 |
| Métriques MCA (MIMI/entropie/stabilité) | `Lyra_Jupyter_MCA/…/lyra_metrics.py` (1) | porter | P2 |
| Pipeline κ/ρ + Betti GF(2) + phase_guard | `Lyra_Core` (+`Topologie`) (1) | porter+dédup | P2 |
| GraphBackend (Strategy) + injecteur nemeton | `Lyra_Uni_0_2` (1) | porter | P3 |
| Deltas de graphe auditables + rollback | `lyra_ACE`/`lyra_clean_bis` (1) | porter | P3 |
| Écologie mémorielle (oubli/compost/pouponnière + réveil) | `session_2/LyrArc` (2) | **ré-impl.** (4 bugs) | P3 |
| Memento (CBR) + 4 stratégies de navigation | `session_2/IspaceNav.zip` (2) | porter | P3 |
| ESMM (gap→cycle→consensus→graphe) | `lyra_clean_bis/services/esmm` (1) | **débuguer** (3 causes) | P4 |
| Boucle à outils + auto-plugins + SilenceØ | `session_2/LyrAgent` (2) | **ré-impl.** (2 SyntaxError, `eval`) | P5 |
| Socle serveur FastAPI (chat/sessions/graphe/multi) | `lyra_clean_bis` (1) | porter (socle) | P6 |
| Juge pairwise + rubrique 6 critères + 15 prompts | `LLM_asa_judge` + `lyra_clean/evaluation` (1) | ré-impl. (pairwise) | P7 |
| NSGA-II sur (ρ,δr,τc,κ) | `Lyra_Core/bench/ga_search.py` (1) | porter | P7 |
| Logging forensique + traçabilité | `Lyra_Uni_0_2`, `Lyra_Core` (1) | porter | P7 |
| **Recherche (non bloquant)** : orbite FLOATLAP | `session_2/tranzit/Floatlap_Orbite_Simulation.py` (2) | porter → `research/` | — |
| **Recherche** : métriques fractales (box-count/Lyapunov/entropie) | `session_2/tranzit/pouponniere_fractale.py` (2) | porter → `research/` | — |
| **Manifeste** : Φ(t), phase λ, kit_lyra, Harmonia, annexe historique | `lyra_project`, `Archi`, `bundle_lyra` (2) | verser | manifeste |

---

## 8·bis. Bannière — « La Jachère » : la vie hors-tâche *(ajout 2026-07-18)*

Deux aspects personnels manquaient au plan ; ils se réunissent sous **une même bannière** : *ce que Lyra fait quand elle ne répond pas* — des processus **hors-ligne, auto-dirigés, génératifs ET sélectifs** qui transforment le système lui-même (ses modules ET sa mémoire). Nom de travail : **La Jachère** (le champ qu'on laisse reposer pour qu'il régénère) — à rebaptiser librement. Détail + ancrage bibliographique : `lyra_reborn/docs/BANNIERE_LA_JACHERE.md`.

**Organe 1 — La Pouponnière évolutive** (aspect déjà présent dans l'audité). Le modèle *cultive, laisse mourir et adopte* ses propres modules de scaffold (prompts, outils, sous-agents, politiques de contrôle) : un **générateur de harness automatique, façon algo génétique, adaptatif selon le modèle et la tâche**.
- Ancrage : c'est exactement la case **« Scaffolding-Improvement / Population-Based »** du survey *Self-Improvements in Modern Agentic Systems* (`docs/2607.13104v1.pdf`) — précédents nommés : Promptbreeder, ADAS, Darwin Gödel Machine, AlphaEvolve/ShinkaEvolve, GPTSwarm ; plafond théorique = Gödel Machine (Schmidhuber 2003) ; auto-curriculum = POWERPLAY. Le *Harness Effect* (`docs/2607.06906v1.pdf`) prouve que le harness est **LE** levier (−33 à −61 % de coût, +82 % qualité/\$, −38 % tokens à parité) et que le gain est **spécifique au modèle** → justifie l'adaptation par-modèle. **MemoHarness** (`docs/2607.14159v1.pdf`) donne le *comment* : **6 dimensions éditables** (contexte/outils/orchestration/mémoire/décodage/sortie) + **banc d'expérience à 2 couches** (par-cas + global distillé) + **recherche lourde hors-ligne / adaptation par-cas légère par *retrieval*** (budget maîtrisé, pas d'évolution au test-time ; le banc 2 couches = journal + nemeton, la distillation = pont vers l'Organe 2).
- Réutilise l'existant : pouponnière/compost de `LyrArc` (substrat de sélection), NSGA-II de `Lyra_Core/bench` (optimiseur), ESMM P4 (candidats de modules), eval P7 (fitness). Maison provisoire dans le dépôt : `evolve/`.
- DoD (charte §1) : une population de harness améliore un objectif mesurable (qualité/token sur un jeu tenu) au fil des générations, de façon reproductible ; un module *adopté* vs *composté*, avec la fitness qui a tranché. **Échoue bruyamment** si les générations ne bougent pas.

**Organe 2 — Le Songe** (désormais *fondé*, cf. réf. ajoutée). Déclencher des **phases de « sommeil »** hors-ligne : (1) **consolider** les mémoires récentes fragiles en connaissance durable, (2) **« rêver »** — recomposer les vecteurs du contexte passé en un curriculum synthétique d'auto-raffinement, sans supervision.
- Ancrage : *Language Models Need Sleep: Learning to Self-Modify and Consolidate Memories* (Behrouz, Hashemi, Mirrokni — `docs/Language_Models_Need_Sleep_...pdf`). Paradigme « Sleep » à 2 stades : **Consolidation mémoire** (*Knowledge Seeding* = distillation ascendante par *replay*, ≈ NREM) + **Dreaming** (curriculum synthétique auto-généré par RL, ≈ REM ; cf. *self-edits* de SEAL).
- **Pont Organe 2 → Organe 1 explicite** : le Dreaming *est* le générateur de curriculum → il *sème* les candidats que la Pouponnière *sélectionne*. Même mécanisme, deux angles. Voilà pourquoi **une seule bannière**.
- S'appuie sur du concret Lyra : **nemeton** (magasin des vecteurs à rejouer, P3), **journal d'oubli** (quoi consolider vs composter), **FLOATLAP** (génération de rêve basse-énergie, `research/`), **phases κ/ρ** (cycle NREM↔REM).
- ⚠️ **Scoping honnête** (Ollama = poids gelés) : **Palier 1** = rêve au niveau scaffold/mémoire (recomposition de contextes → consolidation du graphe + semence de candidats), **constructible sans entraînement** ; **Palier 2** = consolidation paramétrique réelle (distillation LoRA), **nécessite une voie de fine-tuning local**. Détail + DoD testable : `lyra_reborn/docs/BANNIERE_LA_JACHERE.md`.

**Place dans le plan** : nouveau flux qui **mûrit après P3/P4/P7** (il les consomme). Organe 1 est constructible bientôt (fondé) ; Organe 2 reste un jalon de recherche. C'est le **point d'orgue hors-ligne de l'élan « intériorité »** : Lyra se transformant quand elle ne répond pas.

---

## 8·ter. Cap d'application n°1 — « La Vigie » : présence externe *(ajout 2026-07-19)*

La doctrine de l'Architecte (`lyra_reborn/manifeste/DOCTRINE_ARCHITECTE.md`) identifie le goulot d'étranglement actuel : **l'attention** — l'architecture fonctionne mais opère dans le vide. Premier cap d'application hors laboratoire : **La Vigie** (`lyra_reborn/docs/LA_VIGIE.md`) — veille et contribution épistémique sur X, en démonstration publique de la thèse d'orchestration.

- **Deux files** : Audit (EPP via pont — solidité épistémique d'affirmations publiques falsifiables) et Amplification (Lyra — addition technique sur les contenus résonants). Chaque brouillon : score de confiance + justification.
- **Règles dures** : aucune publication automatique (le système n'a AUCUN accès réseau en écriture — l'humain est le bouton publier) ; la cible est l'affirmation, jamais la personne ; pas de confrontation systématique.
- **Jachère Sociale** : différer un sujet bruyant dans le journal d'oubli (`memory/ecology`), analyse asynchrone à froid — l'écologie existante EST le mécanisme.
- **Boucle stratégique** : les labels accepté/rejeté de l'Architecte = premier flux de fitness réel pour la Pouponnière (§8·bis).
- **Critère d'arbitrage désormais double** pour toute brique : solidité interne ET/OU présence externe (doctrine).

Ce cap **tire** P5 (outils d'ingestion), P7 (pré-évaluation des brouillons) et la Jachère. V0 constructible dès maintenant (P3+P4+embeddings faits, entrées 100 % gratuites : arXiv/RSS/captures).

---

## 9. Voie séparée — KAIROS / trading *(hors périmètre de l'édification cognitive)*

À votre demande, le volet marché est traité **à part**. Il ne doit pas contaminer le noyau cognitif (les deux partagent la métaphore fractale, pas le code). Base de départ quand vous y reviendrez : `session_2/BOT/AUDIT_2026-07-16.md`.
- **À garder :** la « fiche d'observation fractale » (graphe de motifs chaînés), l'architecture KAIROS (**diagnostic de régime plutôt que prédiction**), l'apprentissage récursif inter-échelles, et les **métriques fractales opérationnelles** de `tranzit/pouponniere_fractale.py` (les seules réelles).
- **À refaire de zéro :** la détection d'extrema (fausse), la normalisation (absente), et une **baseline statistique** (les motifs battent-ils le hasard ?) *avant* toute couche stratégie/risque.
- **Note :** `BOT` ne contient aujourd'hui ni ordre, ni clé d'exchange, ni backtest — c'est de l'analyse locale. Tout passage au trading réel devra être **re-décidé explicitement**.

---

## 10. Definition of Done globale — ce que « Lyra édifiée » signifie

Lyra est « édifiée » (v1) quand, dans **un seul dépôt** :
1. Un tour de chat passe par : lecture d'état → décision de boutons → **modulation prouvée** de la génération → mise à jour du graphe → gestion mémoire (dont oubli/réveil) — de bout en bout, sans `except` avaleur.
2. Un run ESMM **produit des triplets** et enrichit le graphe.
3. Un outil est appelé via la boucle d'agentivité, et SilenceØ est possible.
4. La lecture de phase (κ/ρ, phase λ) tourne sur la trajectoire réelle et **recalcule** ses métriques (aucune constante magique).
5. Une campagne d'évaluation **pairwise** produit un verdict interprétable comparant Lyra à l'Ollama nu.
6. Le `README` décrit l'**état réel** ; tout chiffre est régénérable ; le manifeste porte le « pourquoi » et l'annexe historique.

**Jalons de démonstration** (pour ne pas attendre la fin) : *Démo A* après P1 (modulation visible) ; *Démo B* après P3 (mémoire vivante + oubli/réveil) ; *Démo C* après P4 (ESMM produit) ; *Démo D* après P6 (chat complet) ; *Verdict* après P7.

---

## 11. Anti-patterns spécifiques à ce projet (rappel condensé)

- ❌ Copier un dossier « qui marche » sans le tester → il est probablement « vert mais vide ».
- ❌ Croire un README « RESULTATS/Production Validée » → croire les post-mortems, pas le marketing.
- ❌ Ré-implémenter une brique existante → `grep` d'abord (règle charte §5).
- ❌ Sérialiser un graphe entier à chaque message → borne + compaction (cas 1,18 M arêtes).
- ❌ `except Exception: pass` → interdit (cause racine de la moitié des pannes silencieuses).
- ❌ Juge pointwise / sans clé d'anonymisation → effet plafond + résultats inexploitables.
- ❌ Présenter du théorique (SATORYX, Φ non opérationnalisé, EDO à coeff. arbitraires) comme acquis → annexe « pistes spéculatives ».

---

*Ce plan est un document vivant : il doit être amendé au fil de l'édification (cocher les phases, dater les décisions — ex. le choix κ Ollivier vs Jaccard). Il s'appuie entièrement sur les 43 documents d'audit déjà présents dans `audits_en_cours/` et `session_2/` ; en cas de doute sur une brique, l'`AUDIT_*.md` du dossier-source fait foi.*
