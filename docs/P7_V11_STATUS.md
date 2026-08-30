# P7 — statut de la campagne V11

**Préinscription gelée :** `4005f82d080755fbf98552ef5730a45307b3a3e5`
(`PREREGISTRATION_v11.md`), estampille `cd034bc`
**Amendements incorporés :** `docs/P7_V10_PRERUN_AMENDMENT.md`,
`docs/P7_V10_PRODUCER_CONTEXT_AMENDMENT.md`
**Prédécesseur :** `docs/P7_V10_STATUS.md` (V10 arrêtée après Q0)

**Verdict de campagne : `V11_ARRETEE_APRES_CALIBRATION` — `H11 UNTESTED`.**

Q0 franchie. Q1 échouée. Le jeu tenu n'a jamais été lu.

## Exécutions

| phase | run | statut |
|---|---|---|
| Q0 | `p7_v11_q0_20260830T185626.486422Z` | `Q0_PASSED` — 18/18 |
| Calibration | `p7_v11_calibration_20260830T185956.636038Z` | Q1 échouée |

## Intégrité de l'exécution

Contrairement aux neuf arrêts précédents, aucun élément du dispositif n'a
failli. Ollama **0.33.2** au manifeste et constatée à la fin de chaque bloc
producteur et du bloc juge. Les quatre modèles montés entiers en VRAM
(`size_vram == size`) au contexte 32 768, preuves inscrites au manifeste. Q0
exécutée à neuf sous ce gel, jamais reprise de V10. Round-robin complet, aucune
relance sélective. **432 appels producteur, zéro erreur de transport. 146
appels juge, 146 valides et wire-clean — 100 %.**

L'échec est un résultat de mesure, pas une défaillance instrumentale.

## Q1 — échec sur un seul critère

| critère | exigé | observé |
|---|---|---|
| round-robin complet, sans relance sélective | oui | **oui** |
| gagnant indépendant du départage lexical | oui | **oui** |
| même gagnant dans ≥ 2 des 3 retraits de source | ≥ 2 | **3** (`creative`) |
| résolution des comparaisons complètes | ≥ 50 % | **49,4 %** (40/81) |

Il manquait **une comparaison**. Le §« Ce que la porte a préservé » explique
pourquoi la franchir aurait été pire que l'échouer.

## Résultat 1 — la stabilité du juge est indiscernable du hasard

C'est le résultat principal de la campagne.

Chaque paire est jugée deux fois, candidats intervertis. Un juge qui répond au
contenu donne deux fois la même réponse ; un juge dont la réponse ne dépend pas
du contenu voit ses deux réponses coïncider **une fois sur deux par
construction**. Le hasard n'est donc pas à 0 % : il est à **50 %**.

```
stabilité observée        40/73 = 54,8 %
intervalle de confiance   [43,4 % – 65,7 %]   ← contient 50 %
p bilatéral vs hasard     0,48
seuil de discernabilité   ≥ 45/73 = 61,6 %    (observé : 40)
```

Par producteur : `mistral` 19/35 (54 %), `gemma3` 8/12 (67 %),
`granite3.3` 13/26 (50 %). Les trois intervalles contiennent 50 %.

**Aucun TIE, aucun INVALID sur 73 comparaisons jugées.** Les 33
non-résolutions viennent toutes du juge qui inverse sa préférence quand on
échange les candidats — pas d'une indécision assumée ni d'un défaut de format.

On ne peut donc pas rejeter l'hypothèse que, sur ce matériau, le juge répond
sans lien avec le contenu. Ce n'est pas un jugement sur le modèle : le même
juge a fait 18/18 sur les fixtures Q0 et 24/24 à son admission v2. C'est un
constat sur la **résolution de l'instrument** quand les deux candidats sont
deux sorties du même petit modèle sur le même texte.

## Résultat 2 — erreur méthodologique : le seuil est posé sur le plancher du hasard

**À consigner comme défaut de la préinscription, pas des modèles.**

La prérég V10 annonçait une transposition « mécanique et exhaustive » du panel
bi-juge vers le juge unique, en conservant les seuils « inchangés ». Le seuil
de résolution de 50 % a bien été conservé — mais **le plancher du hasard, lui,
a bougé**.

Sous pur hasard, sans TIE :

| design | condition de résolution | plancher du hasard | seuil | marge |
|---|---|---|---|---|
| V8 — panel de 2 juges | les deux stables **et** d'accord | 0,5 × 0,5 × 0,5 = **12,5 %** | 50 % | ×4 |
| V10/V11 — juge unique | stable après inversion | **50 %** | 50 % | **×1** |

En V8, exiger 50 % de résolution plaçait la barre à quatre fois le bruit. En
juge unique, la même valeur numérique place la barre **exactement sur le
bruit** : une campagne peut franchir Q1 tout en étant statistiquement
indiscernable du hasard.

Le défaut est né au gel V10 et a été reconduit tel quel au gel V11. Ni la
rédaction des préinscriptions, ni la construction du scoreur, ni la relecture
avant lancement ne l'ont vu. Il a été mis au jour par une question de Simon
Bouhier à la lecture des résultats, le 2026-08-31.

Portée : ce défaut n'invalide pas l'exécution de V11 — il en éclaire le seuil.
Toute reprise de ce design devra **redériver ses seuils depuis le plancher du
hasard de sa propre structure**, et non recopier les valeurs numériques d'un
design à la combinatoire différente.

## Résultat 3 — budget d'écriture et contrat producteur sont incompatibles

53 trajectoires sur 144 échouent au tour 3 avec « final output is not strict
JSON ». Exactement **53 appels de tour 3 se terminent en `done_reason:
"length"`** : le modèle est coupé à son plafond de tokens en plein objet JSON.
La correspondance est exacte — tous les échecs objectifs sont des troncatures
de budget, aucun n'est une faute de contenu.

| preset | δr | `num_predict` | échecs /36 |
|---|---|---|---|
| `default` | 0,30 | 320 | 26 |
| `strict` | 0,35 | 352 | 20 |
| `focused` | 0,45 | 416 | 6 |
| `creative` | 0,75 | 608 | 1 |

Monotone. Plus largement, **259 des 432 appels producteur** finissent en
`length`.

Conséquence : la calibration n'a pas comparé des qualités de politique
éditoriale, elle a comparé **la capacité de chaque preset à terminer le
formulaire JSON obligatoire**. `creative` l'emporte parce qu'il est le seul à
avoir la place de finir. Le mapping 128–768 (V8) et les longueurs minimales du
contrat fermé (V6) ont été gelés séparément et leur interaction n'a jamais été
confrontée.

Le drapeau de troncature du harnais (`truncation_suspect`) n'a rien détecté :
il compare un nombre de **mots** à un budget de **tokens**, et ne se déclenche
donc quasiment jamais. Le signal exploitable est `done_reason`, journalisé par
le client producteur.

## Observations mineures

- **8 paires complètes non empaquetées** : `candidate decision must equal the
  parsed turn 3 output`. Le contrôle d'égalité stricte de `eval/p7_evidence.py`
  (gelé) entre la sortie brute et la décision validée après normalisation
  Pydantic écarte ~10 % des paires éligibles. La porte s'est jouée à une
  comparaison ; ce contrôle y a matériellement contribué.
- **Littéral non reparamétré** : le champ `status` du résumé de calibration
  affiche `V10_ABORTED_BEFORE_HELDOUT` au lieu de `V11_…`. Défaut d'affichage,
  sans effet sur les portes ni sur les verdicts.

## Ce que la porte a préservé

La porte C4 du jeu tenu exige **≥ 75 % de stabilité** du juge. On en observe
54,8 %, avec une borne haute d'intervalle à 65,7 % — **le seuil est au-dessus
de tout l'intervalle de confiance**.

Si Q1 avait été franchie d'une comparaison, le jeu tenu aurait consommé 900
appels producteur et 360 appels juge, plusieurs heures durant, pour échouer
très probablement sur C4 et rendre `H11_INCONCLUSIVE` — en ayant dépensé les
60 cas tenus. C'est une inférence, non une mesure, mais elle repose sur une
grandeur mesurée sur 73 comparaisons.

**Les 60 cas tenus n'ont jamais été lus ni générés.** Ils restent intacts.

## Ce qui survit, ce qui meurt

**Meurt :**

- H11 dans V11 : `UNTESTED` ;
- la calibration comme sélecteur de politique : elle sélectionne un budget ;
- le design juge-unique en comparaison par paires **tel qu'instancié** — sa
  stabilité est indiscernable du hasard sur du matériau réel, et aucun réglage
  de budget producteur ne corrige cela.

**Survit :**

- **le jeu tenu : 60 cas, jamais lus** — le seul actif irremplaçable ;
- le corpus, les graines, la sélection, le scellement ;
- le harnais complet, éprouvé en conditions réelles : verrous, preuves GPU,
  contrôle de version, ordre gelé des appels, journal sans contenu, 100 %
  d'appels juge valides. La prérég autorise explicitement cette continuation
  d'ingénierie indépendamment du verdict ;
- Q0 sur 0.33.2 — avec la réserve, établie ici, qu'elle ne prédit pas le
  comportement du juge en campagne ;
- **trois résultats méthodologiques** : le seuil sur le plancher du hasard,
  l'incompatibilité budget/contrat, et la non-représentativité du matériau de
  qualification.

## Leçons

1. **Un seuil hérité doit être redérivé, pas recopié.** Une valeur numérique
   conserve son sens seulement si la structure combinatoire sous-jacente est
   inchangée. C'est le résultat le plus transférable de cette campagne.
2. **Le matériau de qualification doit ressembler au matériau de mesure.** Q0
   n'éprouve le juge que sur des fixtures à dominance sémantique franche, alors
   que la campagne lui soumet deux sorties presque identiques du même modèle.
   Q0 ne pouvait structurellement pas détecter le problème — et cela était
   visible avant le run.
3. **Deux paramètres gelés séparément doivent être confrontés avant le gel.**
   Le budget de sortie et la longueur minimale du contrat ne l'ont jamais été.
4. **Une porte qui coupe est une porte qui fonctionne.** Q1 a arrêté la
   campagne avant de dépenser l'actif irremplaçable sur un instrument sans
   résolution. C'est le comportement attendu d'un pré-enregistrement, pas son
   échec.

## Clause de portée

Aucun énoncé de ce document ne porte sur H11, ni sur la qualité éditoriale des
politiques comparées. Les constats portent sur l'**instrument** et sur la
**préinscription**. Conformément à `docs/P7_V10_PRERUN_AMENDMENT.md`, un
résultat négatif n'établit pas l'absence d'effet : il établit l'absence de
preuve d'un effet *selon cet instrument gelé*, lequel s'avère ici sans
résolution démontrable sur le matériau visé.
