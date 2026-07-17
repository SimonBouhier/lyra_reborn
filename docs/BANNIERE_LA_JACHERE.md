# La Jachère — la vie hors-tâche de Lyra

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
chose : **l'auto-transformation au repos**. Les unir n'est pas cosmétique — c'est
reconnaître qu'ils se nourrissent l'un l'autre (voir « le pont », plus bas).

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
  portant soit sur les paramètres du modèle, soit sur le scaffold. **Ton idée = la
  case « Scaffolding-Improvement / Population-Based » de leur taxonomie.**
  Précédents nommés directement exploitables :
  - **Promptbreeder** — auto-amélioration *auto-référentielle* par évolution de prompts.
  - **ADAS** — *Open-Ended Search over Agent Designs* (recherche ouverte sur les architectures d'agents : agent initial → meilleur agent au fil des itérations).
  - **Darwin Gödel Machine**, **Gödel Agent** — réécriture de soi ; **AlphaEvolve / ShinkaEvolve** — évolution de programmes ; **GPTSwarm** — populations d'agents.
  - Plafond théorique : **Gödel Machine** (Schmidhuber 2003) — réécriture prouvée de son propre code.
  - Auto-curriculum : **POWERPLAY** (Schmidhuber) — chercher continuellement le problème non encore résolu le plus simple → génère sa propre difficulté croissante.
  - Le survey liste explicitement « **evaluation harnesses** », « **skill libraries** », « **autonomous tool creation** » comme cibles de scaffold self-improvement.

- **`2607.06906v1.pdf` — *The Harness Effect*** (Writer, Inc., juil. 2026).
  Thèse : le **harness** (couche d'orchestration qui assemble le contexte, expose
  les outils, décide des tours) est **LE** levier — sur le coût *et* la qualité, un
  seul levier tiré une fois. En ne changeant **que** l'orchestration (tâches et
  modèles constants) : **−33 à −61 % de coût**, **+82 % de qualité/\$**, **−38 %
  de tokens à parité**, plus rapide. Point décisif pour nous : le gain est
  **spécifique au modèle** (« *the rate at which a model converts orchestration
  structure into quality* » diffère selon le modèle). → **Justification empirique**
  qu'un harness doit être **cultivé par-modèle et par-tâche** — exactement ton
  « s'adapte selon le modèle qui le prend en main ».

**Filiation Lyra.** C'est **la pouponnière/compost de `LyrArc`** (auditée), promue
de « cultiver des tâches » à « cultiver des modules ». L'écologie à 3 niveaux
(pouponnière ≥ seuil / journal d'oubli / compost) devient le **substrat de
sélection** ; le **NSGA-II** de `Lyra_Core/bench` est l'optimiseur multi-objectif ;
l'**ESMM** (P4) fournit des modules candidats ; l'**éval** (P7) fournit la fitness.

**Forme dans le dépôt** (proposition — à valider) : un flux `evolve/`. Une
**population** de modules-de-scaffold ; chacun a un *génome* (spec de
prompt/outil/politique), une *fitness* (succès de tâche × économie de tokens — le
double levier du Harness Effect), des opérateurs *mutation/croisement*, une
*sélection*, et un cycle de vie *pouponnière → adoption / compost → mort*.
**Conditionné au modèle** : la population s'adapte au modèle qui la porte.

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

**Le pont vers l'Organe 1 n'est plus une métaphore.** Le Dreaming *est* un
générateur de curriculum auto-généré. « Le rêve sème des candidats que la
Pouponnière sélectionne » et « le Dreaming du papier » sont **le même mécanisme**
vu sous deux angles : le Songe le *produit*, la Pouponnière le *sélectionne et le
pérennise*. (Et le Knowledge Seeding « petit-soi → plus grand » résonne avec la
croissance de la pouponnière.)

**Filiation Lyra.** Le **nemeton** (`memory/graph`, P3) = le magasin des vecteurs à
rejouer/recomposer ; le **journal d'oubli** = la sélection de ce qui mérite d'être
consolidé vs composté ; **FLOATLAP** (`research/`) = une traversée basse-énergie de
l'espace mental = une forme de génération de rêve déjà prototypée ; les
**transitions de phase κ/ρ** (P2) = le cycle **NREM ↔ REM**.

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

**Definition of Done (Palier 1, testable)** : une phase de sommeil produit des rêves
qui sont (a) **nouveaux** (nouveauté mesurable vs les tours passés — pas des
copies), (b) **consolidants** (le graphe/journal après sommeil est plus compact ou
mieux organisé, mesurable), et (c) **utiles en aval** (au moins un rêve nourrit une
tâche ou un module qui améliore une métrique tenue). **Échec bruyant** si les rêves
sont des copies ou restent sans effet (charte §1).

---

## Le pont (pourquoi les deux ne font qu'un)

```
   Le SONGE  ──génère──►  contextes recomposés / associations neuves
       ▲                             │
       │                             ▼ sèment
   consolide                 modules & tâches candidats
   (nourrit le                       │
    magasin)                         ▼ sélectionne
   La POUPONNIÈRE ◄──adopte / composte──  (fitness = tâche × économie tokens)
```

Le rêve **nourrit** la culture ; la culture **oriente** ce qui mérite d'être rêvé.
C'est la boucle hors-tâche de l'auto-transformation.

## Place dans le plan

Nouveau flux (cf. plan directeur §8·bis) qui **mûrit après P3/P4/P7** — il les
consomme. **Organe 1** est constructible bientôt (fondé sur les deux papiers +
l'audité). **Organe 2** reste en attente de tes références. Rien n'est codé tant
que ce document ne pointe pas vers des sources et une DoD testable.
