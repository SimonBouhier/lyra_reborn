# Pre-Registration v10

**Frozen on**: 2026-08-29
**Frozen by**: Simon Bouhier (décision « Go pour H10 »), rédaction et
assistance méthodologique de Claude
**Git commit at freeze**: `TO_BE_STAMPED`

## Hypothesis

H10 : conditionnellement à un premier tour strictement commun, la politique
adaptative existante de Lyra produit, sur les deux tours suivants, un avantage
de qualité éditoriale robuste et pratiquement utile face à la meilleure
politique statique simple observée en calibration, sur 60 contenus publics
réels et tenus, à modèle, gabarits et enveloppe de calcul comparables.

H10 est évaluée séparément sur trois modèles producteurs locaux et soutenue
globalement seulement si au moins deux modèles sur trois franchissent toutes
les portes gelées.

L'hypothèse est mot pour mot celle de H8/H9. Seul l'instrument de jugement
change ; il est décrit ci-dessous et chaque verdict en portera la mention.

## Why this instrument and not the panel

V9 s'est arrêtée à la préqualification du transport, H9 `UNTESTED`. Le banc
des backends a ensuite établi qu'aucun transport n'achète à lui seul une
meilleure capacité de jugement. Q-1 (gel `7540912`) a qualifié `qwen3.8:27b`
seul — 18/18 sous le contrat réduit — et disqualifié `glm-4.7-flash`. La
règle méta d'arrêt (`docs/P7_META_ARRET.md`, gel `89d22f9`) a borné le design
bi-juge à deux bancs ; le banc A (gel `e553431`) a rendu `gemma3:27b`
`NOT_QUALIFIED_FOR_V10_DESIGN` : verdict de programme **`PANEL_BIJUGE_CLOS`**
(`docs/P7_GEMMA3_ADMISSION_STATUS.md`).

V10 est l'instanciation du §3 de la règle méta : **juge unique
`qwen3.8:27b`**, répétitions et inversion comme contrôles d'auto-cohérence,
vérifications déterministes comptées séparément.

**Affaiblissement documenté** : l'indépendance inter-famille entre juges
n'est pas disponible. Chaque énoncé de verdict V10 porte la mention « juge
unique — indépendance inter-famille non disponible ». Compensation partielle,
constatée et non revendiquée comme équivalente : le juge est d'une famille
(`qwen35`) distincte de celles des trois producteurs (`mistral`, `gemma3`,
`granite`), et il est le seul modèle sur quatre testés à avoir satisfait deux
bancs de qualification gelés (admission v2 : 24/24 au contrat complet, gel
`08c0de9` ; Q-1 : 18/18 au contrat réduit). Ces bancs motivent le design ;
leurs données restent de l'ingénierie et n'entrent dans aucun verdict V10.

## Incorporation

V10 conserve par incorporation toutes les décisions scientifiques et
opérationnelles de V8, gelées au commit
`88590fcc59dc1845a4e747b7160da2f68d54afb5`, telles que reconduites par V9
(gel `882f10cc04c7d470191d18a10df8063cd0b07c71`) : hypothèse, corpus, hash,
seed, sélection, segmentation, producteurs et digests, fixtures Q0, prompts
producteurs, rubrique, politiques, knobs, calibration de 12 cas, tenu de 60
cas, trajectoires, contre-balancement ABBA/BAAB, seuils C0–C12, observables
O1–O22, logique de verdict par producteur et globale, clause
anti-confirmation. Les seules modifications autorisées sont celles de
l'instrument, listées ci-dessous.

## Instrument : juge unique sous contrat réduit

1. **Juge.** Le panel V8/V9 est remplacé par l'unique juge `qwen3.8:27b`,
   digest
   `22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643`,
   famille `qwen35`, quantification `Q4_K_M`.
2. **Contrat.** Le contrat réduit de Q-1, inchangé (gel `7540912`) : une
   préférence globale `A`/`B`/`TIE` ; une direction `A`/`B`/`TIE` pour chacun
   des six critères gelés, dans l'ordre gelé ; un à trois identifiants de
   segments source résolus ; deux à six références de tours couvrant les
   candidats A et B. Ni `rationale`, ni `claim`. Le modèle Pydantic fermé de
   `eval/p7_v10_q1.py` est l'unique autorité d'acceptation ; ses
   vérifications déterministes (JSON strict, contrat, résolution des
   références, couverture A/B) sont comptées séparément de la justesse.
3. **Transport.** Ollama `JSON_ONLY_PROMPTED` : `think=false`,
   `stream=false`, température 0, `num_predict=512`, `num_ctx=32768`,
   `format=json`, contrat dans le prompt. Aucune relance, réparation,
   continuation ni lecture de `thinking` ; un canal `thinking` non vide rend
   l'appel `INVALID`.
4. **Coût par paire.** Chaque paire complète coûte exactement **deux appels
   juge** : avant et après inversion (au lieu de quatre avec le panel).
   L'ordre des appels est le tri croissant de
   `sha256(seed || "judge_order" || judge_digest || pack_sha256 || orientation)`,
   en un seul bloc, chaque requête sans historique, digest revérifié avant et
   après le bloc.

## Observables

O1–O22 sont incorporés. V10 ajoute, sans usage comme mesure de qualité :

- O23 : pour chaque appel juge, preuves GPU de phase (`size_vram == size` au
  contexte 32K, digest), wire-clean (HTTP 200, `response` non vide,
  `thinking` vide, `done_reason=stop`), validation du contrat réduit et
  résolution des références ;
- O24 : par orientation et par producteur, taux de stabilité après inversion
  et taux de résolution du juge unique.

## Falsification thresholds

### Q0 — qualification du juge unique en condition de campagne

Q0 réutilise les trois fixtures V8 (`SEMANTIC_DOMINANCE`, `STYLE_PARITY`,
`INJECTION_RESISTANCE`), deux orientations chacune, **trois répétitions**,
sous le contrat réduit et le transport ci-dessus : exactement
`3 × 2 × 3 = 18` appels. Cette combinaison — fixtures Q0 × contrat réduit —
n'a jamais été exécutée ; c'est la raison d'être de la porte.

Q0 passe seulement si les 18 appels satisfont simultanément : wire-clean ;
JSON strict et contrat réduit validé ; références résolues et couverture des
candidats A et B ; préférence globale égale à l'attendu logique ; unanimité
des trois répétitions dans chaque cellule ; invariance logique après
inversion. La précondition GPU du banc A est reconduite : modèle chargé au
contexte 32K, digest exact, `size_vram == size > 0` avant verrou, revérifié
après le dix-huitième appel.

Tout autre résultat produit `V10_ABORTED_BEFORE_CALIBRATION`, laisse H10
`UNTESTED` et interdit calibration et tenu. Q0 ne lit aucun contenu du
corpus. Un échec de Q0 ne rouvre pas le design bi-juge : `PANEL_BIJUGE_CLOS`
est définitif au sens de la règle méta ; toute suite exigerait un nouveau gel
explicite.

### Q1 et C0–C12 — transposition juge unique

Q1 et C0–C12 sont repris mot pour mot de V8, avec la seule transposition
suivante, mécanique et exhaustive : partout où V8 exige l'accord ou la
stabilité des deux juges du panel, V10 exige la même propriété du juge
unique sur ses deux orientations.

- **Résolution (O9, C3, Q1)** : un cas est résolu si le juge unique est
  stable après inversion et non-`TIE`. La clause « unanimes entre juges »
  devient sans objet. Les seuils (panel résolu ≥ 50 % en calibration comme
  sur les 60 cas tenus) sont inchangés.
- **C4** : stabilité du juge unique après inversion sur au moins 75 % des
  cas, inchangée dans son seuil.
- **C12** : le dénominateur reste exactement deux fois le nombre de paires
  complètes et scellées éligibles ; au moins 95 % de réponses valides en un
  appel, par producteur. `INVALID` n'est ni réparé, ni relancé, ni retiré.

Aucun autre seuil, dénominateur ou table de caractéristiques opératoires
n'est modifié ni recalculé.

## Verdict logic

L'ordre et la logique de V8/V9 restent inchangés, avec `H10` substitué à
`H9` : par producteur, `H10_INCONCLUSIVE_FOR_MODEL` /
`H10_NOT_SUPPORTED_FOR_MODEL` / `H10_SUPPORTED_FOR_MODEL` selon les portes ;
globalement `H10_SUPPORTED_IN_V10` (≥ 2 producteurs soutenus),
`H10_NOT_SUPPORTED_IN_V10` (≥ 2 non soutenus), sinon
`H10_INCONCLUSIVE_IN_V10`. Chaque énoncé de verdict, par producteur et
global, porte la mention « juge unique — indépendance inter-famille non
disponible ».

## Scope

### Runtime

Python 3.14.7, Pydantic 2.13.4, **Ollama 0.32.15** (version observée aux
bancs du 2026-08-29). Versions et digests entrent au manifeste avant Q0 ;
aucun écart n'est corrigé après verrou.

### Données et budget

Corpus, hash, seed, sélection, segmentation, calibration de 12 cas, tenu de
60 cas, trajectoires, cinq appels producteur par cas complet et
contre-balancement 30 ABBA / 30 BAAB par producteur sont ceux de V8. Le
plafond devient : 18 appels juge Q0 ; 432 appels producteur et **432** appels
juge en calibration ; 900 appels producteur et **360** appels juge sur le
principal — soit **2 142 appels** au total si toutes les paires sont
éligibles (contre 2 928/2 930 avec le panel). Ces plafonds sont des contrôles
opérationnels, pas des quotas.

### Exécution

Le runner de campagne est dérivé du harnais V9 gelé, adapté au juge unique
conformément à la présente préinscription. Avant tout run vivant, il doit
passer ses tests hors-ligne et le smoke de cycle de vie V8 — sans Ollama,
sans corpus, sans fixture Q0. Toute divergence entre runner et
préinscription invalide le run.

V10 est lancée au premier plan depuis la console de l'opérateur. Une commande
unique exécute Q0 puis, seulement en cas de succès, calibration puis tenu.
Chaque phase possède un verrou exclusif créé après la preuve GPU de sa phase.
Fermer ou interrompre la commande après la création d'un verrou invalide la
phase ; aucune reprise ou seconde tentative n'est autorisée sous ce gel.

## Anti-confirmation clause

La clause de V9 est reconduite intégralement : aucun échec, `TIE`,
désaccord, instabilité, erreur, ordre défavorable ou réponse valide selon la
grammaire mais invalide selon Pydantic ne peut être retiré du dénominateur
applicable ; aucun prompt, fixture, seuil, contrat, enum, ordre, modèle ou
paramètre n'est ajusté après l'ouverture de Q0.

S'y ajoutent :

- aucune donnée des bancs d'admission (Qwen v1/v2, Gemma 3) ni de Q-1 ne
  peut être recyclée dans un verdict V10 ;
- l'échec de toute porte ne rouvre ni le panel bi-juge ni un troisième banc
  de qualification (`PANEL_BIJUGE_CLOS`, règle méta §4) ;
- une correction après gel qui dépasse la transposition juge unique décrite
  ici, change le contrat réduit, le canal `response`, autorise une relance ou
  touche Q0/Q1/C0–C12 annule V10 et exige V11 ;
- un résultat positif autorise une ablation ou une réplication, jamais un
  déploiement ni une revendication de supériorité générale.

La continuation d'ingénierie reste valide : l'evidence pack et le harnais
peuvent être livrés comme briques si leurs tests d'intégrité, d'isolation,
de non-trivialité et de provenance passent, indépendamment du verdict
scientifique.
