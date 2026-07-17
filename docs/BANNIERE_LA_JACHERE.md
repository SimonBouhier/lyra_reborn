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

## Organe 2 — Le Songe (phase paradoxale)

**Intention.** Déclencher des **phases de « sommeil paradoxal »** où les **vecteurs
du contexte passé se recomposent** au fil d'un processus *encore à définir* —
consolidation *et* imagination, hors-ligne.

**Statut honnête (important).** Les deux PDFs fournis **ne couvrent pas** le
sommeil / rêve / *replay* / consolidation (vérifié : 0 occurrence). Cet organe
**attend les références que tu retrouveras**. D'ici là il reste un **jalon de
recherche** : *aucun code, aucun mécanisme inventé, aucun chiffre* (charte §1, §4).
On l'étiquette « Vision/Cible » jusqu'à ce qu'il soit défini et construit.

**Ce à quoi il se raccroche déjà dans Lyra** (pour qu'il ne parte pas de rien) :
- Le **nemeton** (`memory/graph`, P3) *est* le magasin des vecteurs de contexte à recomposer.
- **FLOATLAP** (`research/`, issu de `tranzit`) = errance basse énergie dans l'espace mental = une **traversée déjà onirique**, déjà prototypée.
- Le **journal d'oubli** (réévaluation différée du signal faible) ≈ ce que fait la consolidation.
- Les **transitions de phase κ/ρ** (P2) offrent un langage naturel pour des « stades de sommeil ».

**Familles de mécanismes à évaluer *quand tes références arriveront*** (pistes
honnêtes, pas des engagements) : *memory replay* / consolidation ; interpolation
ou diffusion en espace latent sur les embeddings stockés ; recombinaison
générative de fragments de trajectoire ; *sleep-time compute* (consolider pendant
l'inactivité) ; curricula auto-générés à partir des contextes recomposés (ce qui
**reboucle sur l'organe 1** et sur POWERPLAY).

**Definition of Done (le jour venu)** : une phase de repos produit des artefacts
recomposés qui sont (a) **pas de simples copies** des tours passés (nouveauté
mesurable), et (b) **utiles en aval** (nourrissent une tâche ou un module qui
améliore une métrique).

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
