# Métriques du Songe (Organe 2) — spécification à pré-enregistrer

> Document **à geler** (seuils inclus) et committer **avant** que la boucle de
> sommeil ne lise de vraies données — pré-enregistrement au sens de la charte
> (§4) et du skill `preregistration`. Tant que l'Organe 2 n'a pas de code (il
> attend P3 = la mémoire), ce fichier est la *spec candidate* ; il sera figé
> après calibration, juste avant le premier run réel.

## Principe n°1 — toute métrique isolée est trichable → conjonction + baselines

La nouveauté seule se maximise par du **bruit** ; la consolidation seule par
l'**oubli**. Donc : chaque métrique est **appariée** à sa contre-métrique, le
verdict est une **conjonction**, on rapporte des **distributions sur un lot** de
rêves (jamais un nombre unique), et deux **baselines** bornent le sens (voir plus
bas).

## Principe n°2 — budget de calcul borné (aucun recalcul global par rêve)

Le Nemeton **croît** ; on ne recalcule jamais une quantité globale par paire
évaluée. Tout est **local et incrémental** : listes d'adjacence, plus proche
voisin par index ANN, compteurs de co-occurrence portés par les arêtes. Coût
d'une phase de sommeil = `O(#rêves × coût_local)`.

---

## Métrique 1 — Nouveauté (bande bornée : ni copie, ni bruit)

Cible : *recombinaison neuve de matériel réel*, pas distance brute. Un rêve passe
la nouveauté **ssi (1a ∧ 1b ∧ 1c ∧ 1d)** :

| # | Test | Règle | Coût |
|---|---|---|---|
| 1a | **Anti-copie** (embedding) | `sim_max = max cos(emb(rêve), emb(mémoire)) < τ_copie` | O(log) via ANN |
| 1b | **Ancrage** (anti-hallucination) | `sim_max > τ_plancher` — les constituants retrouvent de vrais nœuds | O(log) via ANN |
| 1c | **Anti-plagiat de surface** | plus long n-gramme commun / Jaccard 5-grammes `< τ_surface` (réutilise `core/metrics/cheap.py`) | O(len) |
| 1d | **Nouveauté compositionnelle BORNÉE** | le rêve relie deux concepts ancrés `c_i, c_j` : *neuf* ssi **pas d'arête directe ET aucun voisin commun à profondeur k=2** | **O(deg)** local |

**1d — précision (correction « systèmes réels »)** : on **ne calcule PAS** de plus
court chemin ni de matrice PMI globale (coût `≥ O(V+E)` par paire → paralysie sur
un graphe croissant). On teste l'**absence de lien à profondeur k=2** :
`voisins(c_i) ∩ voisins(c_j) = ∅` et pas d'arête directe ⇒ lien jugé neuf. C'est
un calcul **local** (borné par le degré des nœuds), O(1) en moyenne sur un graphe
à degré borné. La co-occurrence éventuellement consultée est un **compteur local
d'arête** (incrémental), jamais une PMI recalculée globalement. `k=2` est un
paramètre gelé (défaut 2).

---

## Métrique 2 — Consolidation (compression *à information préservée*)

« Mieux organisé » couplé à « sans rien perdre de récent ». Avant vs après une
phase de sommeil, sur le Nemeton. Verdict **= (2a ∧ 2b ∧ 2d)** ; **2c en
observation seule**.

| # | Test | Règle | Coût |
|---|---|---|---|
| 2a | **Compacité** | `Δ(paires quasi-dupliquées, cos>τ_dup) < 0` **et** arêtes-par-concept-couvert ↓ (dédup + élagage via journal d'oubli). MDL complet = optionnel, plus lourd | local/incrémental |
| 2b | **Structure — juge de paix** | **modularité de Newman `ΔQ > 0`** (+ `Δβ₀ ≤ 0` : fusion d'îlots, avec plancher anti-fragmentation sur le nb de composantes) | O(E) par phase, pas par paire |
| 2c | **β₁ — OBSERVATION seulement** | *hors objectif*. Loggé et interprété (Δβ₁<0 ≈ contradiction résolue ; Δβ₁>0 ≈ cycle vertueux découvert). **Ne conditionne jamais le verdict** | O(E) par phase |
| 2d | **Fidélité — fenêtre GLISSANTE** | récupération testée sur un **échantillon aléatoire des N dernières mémoires** acquises *juste avant cette* phase ; la précision **ne baisse pas**. (Bonus : qualité-par-token de l'injection de contexte sur cette fenêtre) | O(N requêtes) |

**2c — précision (correction β₁)** : la direction de β₁ est **ambiguë**, on ne la
met donc **pas** dans une fonction d'objectif stricte. Q tranche la structure
communautaire ; β₁ sert à *voir* si Lyra complexifie ou simplifie sa vision du
monde en dormant.

**2d — précision (correction holdout)** : le jeu tenu est une **fenêtre
glissante**, pas un ensemble figé. On veut prouver qu'elle **n'a pas détruit sa
veille**, pas qu'elle se souvient de sa naissance. L'oubli gracieux du lointain
est une **feature** (journal d'oubli / compost), pas un échec — donc la fidélité
ne se teste **que** sur le récent. (Option prudente : un petit ancrage long-terme
à rafraîchissement lent, *jamais* comme porte principale.)

---

## Baselines (bornes de sens — sans elles, les nombres ne veulent rien dire)

- **Rêve-copie** (replay verbatim d'un tour passé) → doit **échouer** la nouveauté (1a/1c).
- **Rêve-nul** (recombinaison aléatoire non ancrée) → doit **échouer** l'ancrage (1b) et/ou l'utilité aval.

Une vraie phase de sommeil doit **battre les deux**.

## Verdict d'une phase de sommeil (DoD Palier 1)

Sur un **lot** de rêves : (nouveauté OK en médiane) **∧** (consolidation 2a/2b/2d
OK) **∧** **utilité aval** (au moins un rêve nourrit un module/tâche qui améliore
une métrique tenue). **Échec bruyant** si la médiane de nouveauté ≈ 0 (tout est
copie) ou si la compression fait chuter la fidélité récente (oubli déguisé).

## Seuils = calibrés, datés, gelés (leçon `KAPPA_C`)

`τ_copie, τ_plancher, τ_surface, τ_dup, k(=2), N (fenêtre), plancher Q, plancher
β₀` : **calibrés sur un jeu tenu, jamais codés en dur**, datés dans
`manifeste/VOCABULAIRE.md`, puis **gelés (committés)** avant le premier run réel.

## Récap complexité (garantie anti-paralysie)

| Métrique | Classe de coût | Global ? |
|---|---|---|
| 1a/1b anti-copie/ancrage | O(log) ANN | non |
| 1c surface | O(len rêve) | non |
| 1d compositionnelle k=2 | O(deg) local | **non** |
| 2a compacité | local/incrémental | non |
| 2b/2c Q, β₀, β₁ | O(E) **par phase** | par phase, pas par paire |
| 2d fidélité fenêtre | O(N requêtes récentes) | non |
