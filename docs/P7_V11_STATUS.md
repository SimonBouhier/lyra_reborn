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

## Résultat 1 — le juge lit le contenu, faiblement, sous un fort biais de position

> **Corrigé le 2026-08-31.** La première rédaction de cette section concluait
> que la stabilité du juge était « indiscernable du hasard » (p = 0,48). Cette
> conclusion était **fausse** : elle supposait un plancher de hasard à 50 % au
> lieu de le dériver des marginales observées. Correction détaillée en fin de
> document ; les chiffres ci-dessous sont les corrigés.

Chaque paire est jugée deux fois, candidats intervertis. Les préférences brutes
du juge, sur les 146 appels, ne sont pas symétriques :

```
A       96/146 = 65,8 %      <- fort biais de position
B       40/146 = 27,4 %
TIE     10/146 =  6,8 %
INVALID  0/146 =  0,0 %
```

Sous l'hypothèse nulle « la réponse ne dépend pas du contenu », l'accord entre
les deux orientations après dé-inversion vaut `2ab + t²`, soit **36,5 %** — et
non 50 %. Les 50 % correspondent au cas particulier `a = b = 0,5`, `t = 0` :
c'est le *maximum* de cette expression, pas le plancher général.

```
accord observé            po = 54,8 %   (40/73)
accord attendu au hasard  pe = 36,5 %
kappa de Cohen                 0,288    IC95 [0,108 – 0,468]
p unilatéral vs pe = 36,5 %    0,0011
```

**Le juge lit donc bien le contenu.** L'accord corrigé du hasard est
significatif mais faible — « fair » sur l'échelle de Landis-Koch. Ce qui absorbe
son signal n'est pas l'absence de discrimination, c'est un **biais de position
massif** : il répond « A » dans deux tiers des cas quelle que soit la paire.

Le TIE n'est pas absent : le juge s'abstient 10 fois sur 146. Sur les 33
comparaisons non stables, **23 sont de vraies bascules de position et 10 sont
des abstentions partielles** — une orientation tranche, l'autre dit TIE.

Par producteur : `mistral` 19/35, `gemma3` 8/12, `granite3.3` 13/26.

**Ce que la correction ne change pas :** la porte C4 du jeu tenu exige 75 % de
stabilité **brute**, et la stabilité brute observée reste 54,8 %. La conclusion
sur ce qu'aurait donné le jeu tenu est inchangée.

**Ce qu'elle change :** le diagnostic. « Instrument sans résolution » devient
« instrument à signal réel mais faible, noyé par un biais de position ». Le
premier est une impasse ; le second est un défaut connu et adressable.

## Résultat 2 — erreur méthodologique : le seuil est posé sur le plancher du hasard

**À consigner comme défaut de la préinscription, pas des modèles.**

La prérég V10 annonçait une transposition « mécanique et exhaustive » du panel
bi-juge vers le juge unique, en conservant les seuils « inchangés ». Le seuil
de résolution de 50 % a bien été conservé — mais **le plancher du hasard, lui,
a bougé**.

Le plancher du hasard dépend de la **structure** de la règle de résolution, et
il a changé sans que le seuil bouge :

| design | condition de résolution | plancher du hasard | seuil | marge |
|---|---|---|---|---|
| V8 — panel de 2 juges | les deux stables **et** d'accord | ≈ **12,5 %** | 50 % | ×4 |
| V10/V11 — juge unique | stable après inversion | **≤ 50 %**, maximum atteint pour un juge symétrique sans TIE | 50 % | **≥ ×1** |

Le seuil de 50 % a été recopié de V8 sans être redérivé. Sous juge unique, `2ab + t²`
ne peut jamais dépasser 50 % : la barre a donc été placée **sur la borne
supérieure du bruit**. Un juge parfaitement symétrique aurait eu une marge
strictement nulle. Le juge réel, fortement biaisé (`a` = 65,8 %), a un plancher
plus bas — 36,5 % — donc une marge non nulle, mais **par accident de son
biais**, pas par construction du seuil.

C'est ce qui rend le défaut structurel : la marge de la porte dépendait d'une
propriété du juge que personne n'avait mesurée ni bornée avant de geler.

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
- le design juge-unique en comparaison par paires **tel qu'instancié** — non
  parce qu'il serait sans signal, mais parce que son biais de position absorbe
  ce signal : 54,8 % de stabilité brute contre 75 % exigés par C4, et aucun
  réglage de budget producteur ne corrige cela.

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

## Correction du 2026-08-31

Quatre erreurs de la première rédaction, relevées par Simon Bouhier à la
relecture. Consignées ici plutôt que corrigées en silence.

1. **« Zéro TIE » était faux.** Le comptage ne retenait que les comparaisons
   TIE des *deux* côtés (0 cas) et présentait ce 0 comme l'absence totale de
   TIE. Le juge s'abstient en réalité 10 fois sur 146 appels, et 10
   comparaisons portent un TIE sur une seule orientation.
2. **Les 33 non-résolutions n'étaient pas toutes des bascules de position.**
   23 le sont ; 10 sont des abstentions partielles, de nature différente.
3. **Le plancher du hasard était supposé, pas dérivé.** 50 % ne vaut que si le
   juge est symétrique et n'abstient jamais. Avec ses marginales réelles, le
   plancher est à 36,5 %, et la conclusion s'inverse : p passe de 0,48 à
   0,0011. **C'est exactement le défaut D1 documenté plus haut, reproduit dans
   l'analyse de D1 elle-même.**
4. **Les logprobs ne sont pas disponibles pour le juge.** La vérification
   initiale avait été faite sur `gemma3:latest`, qui renvoie la séquence
   complète. Sur `qwen3.8:27b`, `/api/generate` ne renvoie **qu'une seule
   entrée** de logprobs quelles que soient les options — avec ou sans
   `format=json`, avec ou sans `think:false`, pour des générations de 7, 13 ou
   64 tokens. Hypothèse non vérifiée : les deux modèles n'empruntent pas le
   même moteur d'inférence dans Ollama, l'architecture `qwen35` n'étant pas
   chargeable par llama.cpp upstream. La voie de diagnostic « rejouer les packs
   existants avec logprobs » n'existe donc pas sur ce juge.

Résidus de nommage relevés au même moment, dans le code et non dans ce
document : 12 littéraux `H10_…` dans les verdicts du scoreur et 2 littéraux
`V10_ABORTED_…` dans les statuts. Une campagne V11 étiquetait donc ses propres
verdicts avec le numéro de la précédente.
