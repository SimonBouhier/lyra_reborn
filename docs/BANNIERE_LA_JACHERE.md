# La Jachère — la vie hors-tâche de Lyra

> **Alignement du 9 septembre 2026 :** les sources bibliographiques citées
> sont des pistes de lecture issues du cadrage antérieur. Le présent lot ne
> vérifie ni les articles ni leurs chiffres ; ces rapprochements ne sont pas
> des critères d'admission. La rédaction antérieure reste dans l'historique
> Git, à `15bcede4d1b876821524dd1f6d53c51879497c6a`.
> [ETAT_ACTUEL](ETAT_ACTUEL.md) porte la maturité locale ; le
> [registre](REGISTRE_INTENTIONS.md) conserve les intentions et leurs jalons.

> **Cadrage retenu le 7 septembre 2026 :** consolidation et recombinaison doivent
> fonctionner séparément, avec des échanges facultatifs vers la Pouponnière.
> La [note d'architecture détaillée](NOTE_ARCHITECTURE_JACHERE_CLOISONNEMENT_2026-09-07.md)
> fait référence pour les frontières, l'admission, les budgets, le retrait et
> les preuves attendues. Les rapprochements bibliographiques ci-dessous ne
> démontrent ni l'équivalence des mécanismes ni un bénéfice dans Lyra.

> **Bannière** réunissant deux aspects sous-représentés dans le plan. *Nom de
> travail* — à rebaptiser librement (autres pistes : « Hypnos », « Le Métabolisme »,
> « Le Songe et la Pouponnière », « Otium »).
>
> **Définition :** tout ce que Lyra fait *quand elle ne répond pas* — des processus
> **hors-ligne, auto-dirigés, à la fois génératifs et sélectifs**, qui transforment
> le système lui-même : ses **modules** (organe 1) et sa **mémoire** (organe 2).

## Pourquoi une seule bannière

Dans un esprit, le repos n'est pas l'inactivité. Le sommeil **consolide** la
mémoire *et* **élague/reconfigure** la structure ; le développement **cultive et
sélectionne** des modules. Les deux aspects sont les deux visages d'une même
chose : **l'auto-transformation au repos**. La bannière commune décrit cette
intention ; elle n'impose pas de dépendance entre les fonctions. Les échanges
seront facultatifs et qualifiés séparément (voir « le pont », plus bas).

C'est aussi le **point d'orgue de l'élan « intériorité »** : après le contrôle
(P1), la perception de soi (P2), la mémoire (P3), l'exploration (P4), l'agentivité
(P5) — la Jachère est le moment où Lyra travaille *sur elle-même*.

---

## Organe 1 — La Pouponnière évolutive

**Intention.** Le modèle *cultive, laisse mourir et adopte* ses propres modules de
scaffold (prompts, outils, sous-agents, politiques de contrôle) : un **générateur
de harness automatique, façon algorithme génétique, adaptatif selon le modèle et
la tâche qui le prend en main**.

**Ancrage bibliographique** (les deux PDFs déposés dans `docs/`) :

- **`2607.13104v1.pdf` — *Self-Improvements in Modern Agentic Systems: A Survey***
  (Ren, Chen, Guo… **J. Schmidhuber**, KAUST, juil. 2026). Formalise un agent =
  *modèle de fondation* + *scaffold* (prompts, mémoire, outils, logique de
  contrôle) ; l'auto-amélioration = un **opérateur de mise à jour auto-induit**
  portant soit sur les paramètres du modèle, soit sur le scaffold, selon la
  lecture historique à vérifier. La catégorie « Scaffolding-Improvement /
  Population-Based » est une piste de comparaison avec la Pouponnière, pas
  une identité établie. Précédents nommés à examiner avant réutilisation :
  - **Promptbreeder** — auto-amélioration *auto-référentielle* par évolution de prompts.
  - **ADAS** — *Open-Ended Search over Agent Designs* (recherche ouverte sur les architectures d'agents : agent initial → meilleur agent au fil des itérations).
  - **Darwin Gödel Machine**, **Gödel Agent** — réécriture de soi ; **AlphaEvolve / ShinkaEvolve** — évolution de programmes ; **GPTSwarm** — populations d'agents.
  - Plafond théorique : **Gödel Machine** (Schmidhuber 2003) — réécriture prouvée de son propre code.
  - Auto-curriculum : **POWERPLAY** (Schmidhuber) — chercher continuellement le problème non encore résolu le plus simple → génère sa propre difficulté croissante.
  - Le survey liste explicitement « **evaluation harnesses** », « **skill libraries** », « **autonomous tool creation** » comme cibles de scaffold self-improvement.

- **`2607.06906v1.pdf` — *The Harness Effect*** (Writer, Inc., juil. 2026).
  Piste de lecture : effet de l'orchestration sur le coût et la qualité selon
  le modèle et la tâche. Les chiffres du cadrage antérieur sont retirés de
  cette synthèse active jusqu'à vérification des conditions de l'article.
  L'intention Lyra de cultiver un scaffold adapté au modèle et à la tâche
  demeure ; son utilité devra être mesurée dans son propre périmètre.

- **`2607.14159v1.pdf` — *MemoHarness: Agent Harnesses That Learn from
  Experience***. Le *comment* concret. Décompose le harness en **six dimensions
  éditables** — *contexte, outils, orchestration, mémoire, décodage, sortie* ;
  apprend via un **banc d'expérience à deux couches** (diagnostics **par-cas** +
  **patterns globaux distillés**) ; **adapte le harness par cas via récupération,
  sans recherche au moment du test**. ⭐ **Séparation clé pour nous** : la
  **recherche évolutive lourde** se fait **hors-ligne** (= pendant la Jachère),
  l'**adaptation par-cas légère** se fait **en ligne** par simple *retrieval* — ce
  qui suggère une séparation de budgets à étudier. Le rapprochement entre ce
  banc et le journal/Nemeton de Lyra est une analogie de conception à vérifier,
  sans identité de stockage, de mécanisme ou de bénéfice démontrée. Un éventuel
  pont de consolidation relève du contrat Jachère et de ses preuves propres.

**Filiation et rôles envisagés.** La pouponnière/compost de `LyrArc` (auditée)
inspire le passage de « cultiver des tâches » à « cultiver des modules ».
L'écologie à trois niveaux fournit un design possible de sélection ; NSGA-II
de `Lyra_Core/bench` est une source historique d'optimisation multi-objectif.
ESMM pourrait proposer des candidats et un instrument adapté les évaluer.
Ces échanges ne sont pas implémentés par cette filiation ; ils n'imposent ni
l'ouverture de H11 ni la disponibilité de toute P7.

**Forme dans le dépôt** (proposition — à valider) : un flux `evolve/`. Une
**population** de modules-de-scaffold ; chacun a un *génome* = les **six
dimensions éditables** (contexte, outils, orchestration, mémoire, décodage, sortie
— cf. MemoHarness), une *fitness* (succès de tâche × économie de tokens — le
double levier du Harness Effect), des opérateurs *mutation/croisement*, une
*sélection*, et un cycle de vie *pouponnière → adoption / compost → mort*.
**Conditionné au modèle** : la population s'adapte au modèle qui la porte.
**Découpage MemoHarness** : la **recherche évolutive lourde** tourne **hors-ligne**
(pendant la Jachère) ; à l'inférence, on ne fait qu'une **adaptation par-cas
légère par *retrieval*** dans le banc d'expérience — jamais d'évolution au
test-time (budget maîtrisé).

**Definition of Done** (charte §1) : un run montre une population de harness
améliorant un objectif mesurable (p. ex. qualité-par-token sur un jeu de tâches
tenu) **au fil des générations**, de façon reproductible ; et l'on peut exhiber un
module *adopté* vs un module *composté* avec la fitness qui a tranché. **Échec
bruyant** si les générations ne changent pas la fitness (pas de « vert mais vide »).

---

## Organe 2 — Le Songe (phases de sommeil)

**Intention.** Déclencher des **phases de « sommeil »** hors-ligne où Lyra (1)
**consolide** ses mémoires récentes fragiles en connaissance durable, et (2)
**« rêve »** — recompose les vecteurs du contexte passé en un curriculum
synthétique pour se raffiner elle-même, sans supervision.

**Ancrage bibliographique** (la référence que tu as ajoutée) :

- **`Language_Models_Need_Sleep_Learning_to_Self-Modify.pdf` — *Language Models
  Need Sleep: Learning to Self-Modify and Consolidate Memories*** (Behrouz,
  Hashemi, **Mirrokni**, Google). Un paradigme **« Sleep »** inspiré du sommeil
  humain, en **deux stades** :
  1. **Consolidation mémoire** (≈ NREM / ondes lentes) : **Knowledge Seeding** —
     une distillation *ascendante* par **replay** où les mémoires court-terme
     fragiles (in-context) d'un « petit-soi » sont distillées vers les paramètres
     long-terme (voire un réseau plus grand), en préservant la connaissance.
     Mécanisme : *Generalized Distillation* (distillation on-policy + imitation par
     RL).
  2. **Dreaming** (≈ REM) : une phase d'**auto-amélioration** où le modèle
     **génère par RL un curriculum de données synthétiques (« rêves »)** pour
     répéter la connaissance nouvelle et raffiner l'existant, **sans humain**.
     Apparenté aux *self-edits* de **SEAL** (« rêves » dans leur terminologie).
     Moteur théorique : contrer l'**oubli catastrophique** ⇒ auto-amélioration
     itérative.

**Le pont vers l'Organe 1 est une proposition Lyra.** « Le rêve sème des
candidats que la Pouponnière sélectionne » décrit l'échange envisagé entre
recombinaison et sélection. Son identité avec le Dreaming de l'article n'est
pas établie. Production, sélection et admission gardent des résultats et des
droits propres, et leur coopération reste facultative.

**Filiation Lyra.** Nemeton (`memory/graph`, P3), journal d'oubli et compost,
FLOATLAP (`research/`) et transitions κ/ρ sont des sources de primitives ou de
questions pour le Songe. Le graphe actuel contient des nœuds et des arêtes ;
il ne constitue pas à lui seul le magasin vectoriel complet envisagé. Une
traversée numérique de FLOATLAP ne prouve pas la génération d'un rêve utile,
et les transitions de contrôle ne sont pas identifiées aux stades NREM/REM.

**⚠️ Scoping honnête (Ollama = poids gelés).** Le papier consolide en **espace
paramétrique** (distillation / RL fine-tuning). Lyra tourne sur des modèles
**gelés** (Ollama), sans infra d'entraînement. On construit donc en **deux
paliers** :
- **Palier 1 — Le Songe au niveau scaffold/mémoire (constructible SANS
  entraînement).** La phase de rêve génère des « rêves » = **contextes recomposés**
  à partir du nemeton (recombinaison/replay de fragments de trajectoire) qui
  servent à (a) consolider/réorganiser le graphe sémantique + le journal d'oubli,
  et (b) **semer des modules/tâches candidats pour la Pouponnière**. Zéro mise à
  jour de poids. C'est le « rêve de contexte ».
- **Palier 2 — Consolidation paramétrique (nécessite une voie d'entraînement).**
  Knowledge Seeding réel (distillation vers un adaptateur **LoRA** ou un modèle plus
  grand). À ouvrir seulement si/quand une brique de fine-tuning local est ajoutée.
  Marqué **« Cible »** d'ici là.

**Ancienne proposition de Definition of Done (Palier 1) — à réviser.**
Le verdict conjoint suivant n'est plus l'orientation retenue ; voir la note du
7 septembre. Il est conservé pour rendre l'évolution du cadrage explicite.
La proposition prévoyait une spécification figée + seuils :
`docs/METRIQUES_SONGE.md` (à pré-enregistrer avant le premier run réel). En bref,
une phase de sommeil passe **ssi**, sur un *lot* de rêves :
- **(a) Nouveauté** (bande bornée, ni copie ni bruit) : anti-copie `sim_max<τ_copie`
  **∧** ancrage `sim_max>τ_plancher` **∧** anti-plagiat de surface **∧** nouveauté
  compositionnelle **bornée** — lien neuf = *pas d'arête ni de voisin commun à
  profondeur k=2* (local O(deg), **jamais** de plus court chemin ni de PMI globale).
- **(b) Consolidation** (compression à information préservée) : compacité ↓ **∧**
  **modularité `ΔQ>0`** (juge de paix) + `Δβ₀≤0` **∧** **fidélité** sur une
  **fenêtre glissante** (les N dernières mémoires avant cette phase) qui ne chute
  pas. `β₁` = **observation seule**, hors objectif.
- **(c) Utilité aval** : au moins un rêve nourrit un module/tâche qui améliore une
  métrique tenue.

**Échec bruyant** si la médiane de nouveauté ≈ 0 (tout est copie) ou si la
compression fait chuter la fidélité récente (oubli déguisé). Deux **baselines**
bornent le sens : *rêve-copie* (doit échouer la nouveauté) et *rêve-nul* (doit
échouer l'ancrage). Seuils **calibrés, non codés en dur** (leçon `KAPPA_C`).

---

## Le pont (coopération facultative, à qualifier)

```
   Le SONGE  ──génère──►  contextes recomposés / associations neuves
       ▲                             │
       │                             ▼ sèment
   consolide                 modules & tâches candidats
   (nourrit le                       │
    magasin)                         ▼ sélectionne
   La POUPONNIÈRE ◄──adopte / composte──  (fitness = tâche × économie tokens)
```

Ce schéma décrit les échanges envisagés. La génération de candidats ne devient
pas une dépendance de la consolidation ni de la Pouponnière. Un éventuel retour
de sélection vers la génération est un pont distinct à qualifier ; aucune
boucle de confirmation automatique n'est autorisée par ce schéma.

## Place dans le plan

Flux inscrit au [plan actif](PLAN_EDIFICATION.md), avec primitives de mémoire,
sources autorisées et instruments adaptés comme dépendances à préciser. Cela
n'impose ni réouverture de H11, ni V12, ni achèvement de toute P7 pour travailler
sur les contrats et composants. Les fonctions et leurs ponts restent à
construire ou qualifier. P6 reste prioritaire ; la note du 7 septembre fixe
les responsabilités et le retrait, sans abandon du palier paramétrique futur.
