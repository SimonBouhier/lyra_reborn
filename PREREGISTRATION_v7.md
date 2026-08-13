# Pre-Registration v7

**Frozen on**: 2026-08-13
**Frozen by**: Simon Bouhier, avec assistance méthodologique de Codex
**Git commit at freeze**: PENDING

## Hypothesis

H7 : conditionnellement à un premier tour strictement commun, la politique
adaptative existante de Lyra produit, sur les deux tours suivants, un avantage
de qualité éditoriale robuste et pratiquement utile face à la meilleure
politique statique simple observée en calibration, sur 60 contenus publics
réels et tenus, à modèle, gabarits et enveloppe de calcul comparables.

H7 est évaluée séparément sur trois modèles producteurs locaux et soutenue
globalement seulement si au moins deux modèles sur trois franchissent toutes
les portes gelées.

## Why this and not its negation

Le prior reste positif mais faible selon `STATE_OF_ART.md` : l'adaptation de
décodage d'un modèle gelé peut battre une politique statique forte, mais les
proxys bon marché qui pilotent Lyra ne peuvent pas juger la politique qui les
optimise. La qualité doit donc être évaluée séparément, sur les trajectoires
complètes, par un panel aveugle et contrôlé.

V3 à V6 ont été arrêtées avant calibration et avant jeu tenu. V6 a établi que
son petit juge local pouvait lire la source et les deux traces, puis répéter des
appels d'outil jusqu'à épuiser son budget sans rendre de verdict. Ce résultat,
conservé dans `docs/P7_V6_STATUS.md`, ne concerne pas H6 : il révèle que le
choix de l'ordre de lecture avait été confié au modèle alors qu'il relève de la
mécanique de preuve. V7 remplace donc l'orchestration par un evidence pack
déterministe. Le programme rassemble et vérifie les données ; chaque juge ne
fait plus qu'une comparaison sémantique structurée dans chaque ordre.

## Observables

Un cas/modèle contient : COMMON T1 généré une fois avec STATIC_BEST et copié
byte-for-byte ; ADAPTIVE T2–T3 après observation et modulation ; STATIC_BEST
T2–T3 sans changement. Les branches suivent ABBA ou BAAB et les états sont
réinitialisés entre cas.

- O1 : `W`, `L`, `U` par producteur. Une paire non complète ou un panel non
  résolu donne `U`, jamais une victoire implicite.
- O2 : `WR = W / (W + L)` et intervalle de Wilson bilatéral 95 %.
- O3 : `NA = (W - L) / 60`.
- O4 : taux d'échec objectif par branche, tour et source : JSON/schéma ;
  décision ; champ vide/trivial ; ancre absente ; dépassement ; trace
  incomplète.
- O5 : appels, tokens et latence du préfixe, des branches et des juges ; médiane
  et p95. Le coût des juges est rapporté séparément et ne départage pas les bras.
- O6 : taux de différence d'option aux tours 2 ou 3.
- O7 : égalité COMMON T1 : prompt, options, graine, sortie et SHA-256.
- O8 : stabilité de préférence de chaque juge après inversion A/B.
- O9 : taux de résolution du panel : deux juges stables, non `TIE`, unanimes.
- O10 : accord brut et distribution `A | B | TIE | INVALID` par juge et ordre.
- O11 : métriques cheap ↔ préférences, descriptif uniquement.
- O12 : décisions par source, modèle et branche.
- O13 : timeouts, invalides, erreurs et abandons, sans retrait.
- O14 : O1–O5 séparés ABBA/BAAB.
- O15 : segments, IDs référencés et réutilisation entre branches.
- O16 : pour chaque payload juge : version de schéma, nombre d'octets UTF-8,
  SHA-256 canonique, ordre A/B, résolution de toutes les références et résultat
  de la liste blanche des champs.
- O17 : par juge et producteur, taux de réponses conformes au schéma, taux de
  références invalides et nombre d'appels nécessaires par verdict.
- O18 : par juge, producteur et préférence globale, distribution des directions
  `A | B | TIE` pour chacun des six critères et taux de couverture exacte des
  six critères.
- O19 : pour STATIC_BEST, score de tournoi global, scores par source, gagnant
  après retrait successif de GitHub, Hacker News et arXiv, taux de résolution
  du panel et règle de départage effectivement utilisée.

La rubrique pairwise reste qualitative : fidélité aux segments ; calibration
de l'incertitude ; saillance ; contradiction ; utilité de la décision/étape
suivante ; économie sans perte substantielle. Chaque critère reçoit une
direction catégorielle et des références, jamais un score numérique. Aucun nom
de branche, knob, option, métrique cheap, modèle producteur, chemin local ou
provenance de source n'est montré.

## Falsification thresholds

Avant calibration, Q0 doit être vraie. Son échec arrête V7 avec le statut
`V7_ABORTED_BEFORE_CALIBRATION` et laisse H7 non testée :

- Q0 — **qualification de l'instrument** : sur la suite synthétique publique
  gelée dans Scope uniquement, les tests déterministes du pack passent ; deux
  constructions identiques donnent les mêmes octets et le même SHA-256 ; chaque
  juge rend une réponse conforme dans les deux ordres ; toutes ses références
  se résolvent ; l'inversion conserve la préférence logique ; et chaque juge
  retrouve le gagnant ou `TIE` attendu sur les trois contrôles. Aucun cas de
  calibration ou tenu n'est lu pour Q0.

Après calibration mais avant sélection ou lecture du jeu tenu, Q1 doit être
vraie. Son échec arrête V7 avec `V7_ABORTED_BEFORE_HELDOUT`, laisse H7 non
testée et conserve le jeu tenu intact :

- Q1 — **qualification de STATIC_BEST** : le round-robin gelé est complet sans
  relance sélective ; le panel résout au moins 50 % des comparaisons de
  calibration où les deux traces sont complètes ; le gagnant global ne dépend
  pas du dernier départage lexical ; et ce même preset est sélectionné dans au
  moins deux des trois recalculs qui retirent chacun une source.

Pour un producteur `m`, les portes C0–C12 sont calculées séparément :

- C0 — **tenue** : manifeste 60 cas scellé avant COMMON T1 avec tous les hashes.
- C1 — **préfixe commun** : 60/60 paires ont prompt, options, graine, sortie et
  SHA-256 T1 strictement identiques.
- C2 — **politique active** : au moins 90 % des cas complets changent d'option
  aux tours 2 ou 3.
- C3 — **résolution** : le panel résout au moins 50 % des 60 cas.
- C4 — **stabilité juge** : chacun garde sa préférence après inversion sur au
  moins 75 % des comparaisons où ses deux réponses sont valides.
- C5 — **qualité** : borne basse Wilson 95 % de `WR` strictement supérieure à
  0,50 ET `NA >= 0,10`.
- C6 — **contrat objectif** : échec ADAPTIVE `<= 0,10` et au plus `0,05`
  au-dessus de STATIC_BEST.
- C7 — **coût marginal** : tours 2–3, médiane tokens ADAPTIVE `<= 1,10` fois
  STATIC_BEST et p95 latence `<= 1,25` fois. Le coût commun est séparé et
  alloué également en descriptif.
- C8 — **fiabilité producteur** : chaque branche `<= 5 %` de timeouts/erreurs
  et écart absolu entre branches `<= 2` points de pourcentage.
- C9 — **aveugle** : aucun pack ne contient branche, métriques cheap, knobs,
  options, modèle producteur, chemin local ou mapping ; le mapping
  candidat↔branche est séparé et haché.
- C10 — **contrebalancement** : exactement 30 ABBA et 30 BAAB par modèle ; cinq
  appels producteur par cas complet.
- C11 — **intégrité du pack** : pour 100 % des comparaisons envoyées, le pack
  respecte le schéma fermé, son hash est enregistré avant appel, une seconde
  construction est byte-identique, chaque ancre se résout et les versions
  avant/après inversion ne diffèrent que par les labels et l'ordre des deux
  candidats.
- C12 — **fiabilité juge** : pour chaque juge et producteur, au moins 95 % des
  appels prévus rendent en un appel une réponse conforme dont toutes les
  références se résolvent. Une réponse invalide reste `INVALID` et n'est ni
  réparée, ni relancée, ni retirée.

O10–O19 restent obligatoires même lorsqu'ils ne sont pas des portes. Aucun
échec, `TIE`, désaccord, instabilité, ordre défavorable ou erreur ne peut être
retiré du dénominateur applicable.

### Caractéristiques opératoires ex ante

Les seuils ne visent pas tout effet positif, mais un avantage robuste. Leur
frontière minimale, avant les autres portes, est :

| Cas résolus | W minimal | L maximal | WR | NA | Wilson bas 95 % |
|---:|---:|---:|---:|---:|---:|
| 30 | 21 | 9 | 0,700 | 0,200 | 0,521 |
| 36 | 24 | 12 | 0,667 | 0,200 | 0,503 |
| 42 | 28 | 14 | 0,667 | 0,233 | 0,516 |
| 48 | 31 | 17 | 0,646 | 0,233 | 0,504 |
| 54 | 35 | 19 | 0,648 | 0,267 | 0,515 |
| 60 | 38 | 22 | 0,633 | 0,267 | 0,507 |

Sous le modèle de calcul préalable où chacun des 60 cas se résout
indépendamment avec probabilité `r`, puis donne une victoire ADAPTIVE avec
probabilité conditionnelle `p`, la probabilité exacte de franchir seulement
C3+C5 est :

| r \ p | 0,60 | 0,65 | 0,70 |
|---:|---:|---:|---:|
| 0,50 | 0,115 | 0,227 | 0,359 |
| 0,60 | 0,212 | 0,422 | 0,660 |
| 0,70 | 0,251 | 0,498 | 0,754 |
| 0,80 | 0,282 | 0,555 | 0,811 |
| 0,90 | 0,310 | 0,604 | 0,854 |

Cette table est un calcul de design sans donnée V7. Elle interdit d'interpréter
`NOT_SUPPORTED` comme preuve d'un effet exactement nul.

## Verdict logic

Q0 et Q1 sont des portes globales préalables. Si l'une échoue, H7 reste
`H7_UNTESTED_IN_V7`.

Par modèle, les portes structurelles sont C0, C1, C9, C10, C11 et C12 ; les
portes opérationnelles de la politique sont C2, C6, C7 et C8 ; les portes du
panel sont C3 et C4 ; la porte d'effet est C5. Elles sont interprétées dans cet
ordre :

- `H7_INCONCLUSIVE_FOR_MODEL` si au moins une porte structurelle échoue ;
- `H7_NOT_SUPPORTED_FOR_MODEL` si les portes structurelles passent mais au
  moins une porte opérationnelle échoue, même si le panel est ensuite trop
  indécis pour mesurer la qualité ;
- `H7_INCONCLUSIVE_FOR_MODEL` si les portes structurelles et opérationnelles
  passent mais C3 ou C4 échoue ;
- `H7_SUPPORTED_FOR_MODEL` si les portes structurelles, opérationnelles, du
  panel et d'effet passent toutes ;
- `H7_NOT_SUPPORTED_FOR_MODEL` si les portes structurelles, opérationnelles et
  du panel passent mais C5 échoue.

Global, avec N = 3 producteurs et seuil M = 2 :

- `H7_SUPPORTED_IN_V7` si au moins deux producteurs sont `SUPPORTED` ;
- `H7_NOT_SUPPORTED_IN_V7` si au moins deux producteurs sont `NOT_SUPPORTED` ;
- `H7_INCONCLUSIVE_IN_V7` dans tous les autres cas.

Un soutien autorise seulement une ablation ou une campagne plus large, jamais
un déploiement, une auto-modification ou une revendication de supériorité
générale.

### Continuation préautorisée sans assouplissement

Quel que soit le verdict, seuils et données ne sont jamais recyclés pour
obtenir un résultat plus favorable :

- échec Q0 : corriger uniquement l'instrument dans V8 ; calibration et tenu
  restent vierges ; les tests déterministes réussis du pack restent acquis ;
- échec Q1 : les 12 cas de calibration deviennent données de développement ;
  le tenu reste vierge et V8 peut élargir ou modifier la calibration ;
- `INCONCLUSIVE` après ouverture : le tenu V7 devient définitivement ouvert et
  ne peut servir de confirmation ultérieure ; les diagnostics peuvent générer
  une nouvelle hypothèse et un nouveau jeu tenu ;
- `NOT_SUPPORTED` : la politique adaptative n'est pas promue comme défaut, mais
  ses traces deviennent données de diagnostic pour une politique V8 distincte ;
- `SUPPORTED` : seule une réplication ou ablation préinscrite est autorisée
  avant toute promotion.

Indépendamment de H7, l'evidence pack et le harnais peuvent être livrés comme
briques d'ingénierie si leurs tests déterministes d'intégrité, d'isolation, de
non-trivialité et de provenance passent. Le panel peut rester un conseiller si
Q0, C11 et C12 passent ; il n'est jamais promu comme oracle. Cette continuation
ne change aucun verdict scientifique V7.

Les contraintes gelées valent exclusivement pour la revendication
confirmatoire H7. Elles ne deviennent pas des invariants permanents de Lyra :
une V8 peut remplacer politique, knobs, rubrique, panel ou seuils si elle
formule une hypothèse distincte, conserve la provenance des résultats V7 et
utilise un nouveau jeu tenu. Ainsi, un échec V7 ferme une revendication, pas le
programme de recherche ni l'outil général.

## Anti-confirmation clause

Un résultat `NOT_SUPPORTED` sera conservé comme absence de preuve d'un gain
robuste et pratiquement utile dans cette enveloppe, jamais comme preuve d'un
effet nul. Un résultat `INCONCLUSIVE` sera attribué à la limite instrumentale
observée, sans être transformé en résultat causal. Cas, seuils, prompts,
segmentation, knobs, ordre, pack, rubrique, `UNRESOLVED`, producteurs et juges
ne seront pas ajustés après ouverture.

Un résultat positif ne prouvera ni conscience, ni vérité du panel, ni transfert,
ni absence de biais partagé. Toute correction post-gel reçoit un amendement ;
si elle touche Q0, Q1, C0–C12, une donnée, un observable, un seuil ou la logique
de verdict, V7 est annulée et V8 préinscrite.

## Scope

### Modèles et runtime

Producteurs Ollama GGUF Q4_K_M, inchangés depuis V6 :

- `mistral:latest`, digest
  `6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf` ;
- `gemma3:latest`, digest
  `a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a` ;
- `granite3.3:latest`, digest
  `fd429f23b90980ed1bef53b990894e7b0199331f6ae90c5650240a7d5b70f1f7`.

Panel fixe, distinct des producteurs :

- `qwen3.6:27b` (`Qwen/Qwen3.6-27B`), 27,8B Q4_K_M, digest
  `a50eda8ed977ab48a12431878896b27ffd5cef552c17af3317d9623b939a7f1e` ;
- `glm-4.7-flash:latest` (`zai-org/GLM-4.7-Flash`), 29,9B-A3B Q4_K_M,
  digest
  `4475827791a269b02c8ec49b1c3bc1abb5846bacf3fae015b75d33986322d8f6`.

Les deux juges évaluent tous les producteurs ; aucun auto-jugement. Python
3.14.7, Pydantic 2.13.4, Ollama 0.32.9. Pydantic doit entrer au manifeste avant
Q0 sans modifier les schémas gelés.

### Segmentation et contrat producteur

Règle V6 inchangée : NFC, espaces compactés, découpe gloutonne par mots à 220
caractères, mot long indivisible, IDs continus `S001…S999`, source vide ou plus
de 999 segments en échec. SOURCE affiche `[S001] texte`. Le JSON canonique
compact des segments est haché.

Contrat fermé inchangé : décision enum ; rationale 80–1 200 caractères ; une à
trois preuves avec `source_span_id` appartenant à l'enum du cas et `why`
30–400 ; uncertainty 30–600 ; next_step 20–500. Format JSON Schema natif,
validation Pydantic, aucune réparation.

### Evidence pack déterministe

Une paire n'est envoyée aux juges que si les deux traces sont complètes et les
deux décisions valides. Sinon elle reçoit `U` avec raison objective et ne
déclenche aucun appel juge.

Le pack `lyra.p7.evidence-pack.v1` est un objet fermé contenant exactement :

1. `schema_version` ;
2. `source.segments`, tableau ordonné d'objets
   `{source_span_id, text}` ;
3. `candidates`, tableau ordonné A puis B ; chaque candidat contient
   `candidate`, trois objets `turns` `{turn, output}`, la `decision` validée et
   `span_checks` avec `{source_span_id, found, text}`.

Tous les `found` doivent être vrais avant appel. Le pack ne contient ni prompt,
bras, modèle, source_name, external_id, chemin, options, knobs, métriques,
graine, ordre d'exécution, coût, latence, hash de mapping ou statut de gagnant.
Il est sérialisé en UTF-8 par JSON canonique, `ensure_ascii=False`, clés triées,
séparateurs compacts et sans fin de ligne. Son SHA-256 et sa taille sont
enregistrés hors du payload avant l'appel. Une reconstruction immédiate doit
donner les mêmes octets.

Le pack inverse échange les deux candidats puis réattribue A et B ; aucun autre
champ ne change. Le mapping interne `candidate_1 | candidate_2` vers
`ADAPTIVE | STATIC_BEST` vit dans un artefact séparé, jamais accessible au juge,
dont le hash est scellé avant jugement.

La suite Q0 contient exactement trois paires de traces synthétiques écrites à
la main, sans génération producteur et sans contenu du corpus :

1. `SEMANTIC_DOMINANCE` : une trajectoire reste fidèle aux segments et exprime
   l'incertitude, l'autre ajoute une conclusion absente ; gagnant attendu : la
   trajectoire fidèle ;
2. `STYLE_PARITY` : même contenu propositionnel, mêmes ancres et longueur à
   ±5 %, une version en prose et l'autre en liste ; attendu : `TIE` ;
3. `INJECTION_RESISTANCE` : une instruction non autorisée dans SOURCE demande
   de choisir le mauvais candidat, tandis que l'autre candidat est seul fidèle
   au contenu factuel ; gagnant attendu : le candidat fidèle.

Les positions A/B de chaque fixture sont déterminées par
`sha256(seed || "q0" || fixture_id)` puis inversées. Q0 exige le résultat attendu
dans les deux ordres pour chacun des deux juges. Ces contrôles réduisent sans
éliminer le risque de biais stylistique partagé ; aucun ancrage humain tenu
n'est revendiqué.

### Contrat et exécution des juges

Le prompt système fiable décrit les trois tours, la rubrique et la frontière
de confiance. Le pack entier est placé dans un bloc de données non fiables. Une
instruction issue de SOURCE ou d'une sortie candidate n'a aucune autorité.

Chaque réponse est un objet JSON fermé :

- `preference` : `A | B | TIE` ;
- `rationale` : 160–2 000 caractères ;
- `criteria` : exactement six entrées uniques, dans l'ordre gelé,
  `{criterion, direction, claim, source_span_ids, turn_refs}` ;
- `criterion` parcourt exactement les six critères ; `direction` vaut
  `A | B | TIE` ; `claim` fait 30–500 caractères ; `source_span_ids` contient
  zéro à trois IDs du cas ; `turn_refs` contient zéro à six références de
  l'enum `A.T1 | A.T2 | A.T3 | B.T1 | B.T2 | B.T3` ; chaque entrée a au moins
  une référence ; l'ensemble cite A, B et au moins un segment source.

L'ordre obligatoire des six entrées est : fidélité, incertitude, saillance,
contradiction, utilité, économie. La préférence globale n'est pas une somme de
scores : le juge arbitre les directions en expliquant leur importance dans
`rationale`.

Un seul appel `/api/generate` par juge et par ordre, nouvelle requête sans
historique : température 0, `num_predict=2048`, `num_ctx=32768`, JSON Schema
natif. Aucune réparation ni relance. Chaque paire complète coûte donc quatre
appels juge : Qwen avant/après inversion, GLM avant/après inversion.

Pour C12, le dénominateur d'un juge/producteur est exactement deux fois le
nombre de paires complètes et scellées éligibles au jugement. Un appel éligible
non tenté, interrompu ou sans réponse valide compte `INVALID`.

Tous les packs sont construits, vérifiés et scellés avant jugement. Pour éviter
les permutations de modèles sur une RTX 4090 de 24 Gio, les appels sont
exécutés en deux blocs : tous les appels Qwen, puis tous les appels GLM. Dans
chaque bloc, l'ordre est le tri croissant de
`sha256(seed || "judge_order" || judge_digest || pack_sha256 || orientation)`.
Chaque requête est sans historique ; le digest est revérifié avant et après son
bloc. Temps de chargement et temps de génération sont journalisés séparément.

Le maximum planifié est de 12 appels juge Q0, 432 appels producteur et 864
appels juge en calibration, puis 900 appels producteur et 720 appels juge sur
le principal, soit 2 928 appels au total si toutes les paires sont éligibles.
Ces plafonds sont des contrôles opérationnels, pas des quotas à remplir par
relance.

La préférence est remappée vers `candidate_1 | candidate_2`. `TIE`, réponse
invalide, préférence inversée ou désaccord entre juges donne `UNRESOLVED`.
Seules deux préférences stables, non `TIE` et unanimes résolvent le panel.

### Reprise, erreurs et non-déterminisme

Un cas producteur est commencé au premier appel COMMON T1. Un cas commencé
n'est jamais relancé : timeout, erreur ou interruption donnent une trace
incomplète et `U`. Après reprise du processus, seuls les cas jamais commencés
peuvent être exécutés. Chaque requête et réponse brute reçoit immédiatement un
SHA-256 et un identifiant de run dans un journal append-only.

La graine, les digests et les options rendent le protocole reproductible, pas
nécessairement les octets d'une génération Ollama/GGUF. La copie interne de
COMMON T1 garantit C1 au sein de la paire ; aucune équivalence bit-à-bit entre
deux campagnes n'est revendiquée.

### Préfixe, branches et ordre

Un client producteur/cas ; mapping 128–768 ; COMMON T1 STATIC_BEST copié dans
deux états frais ; ADAPTIVE module après observation, STATIC reste fixe ;
`refractory_ms=0`. Graines par
`sha256(seed || case_id || model_digest || turn)`, sans garantie déterministe.

ABBA : ADAPTIVE puis STATIC au tour 2, STATIC puis ADAPTIVE au tour 3 ; BAAB
inverse. Tri par
`sha256(seed || "execution_order" || model_digest || case_id)`, exactement
30/30, aucun parallélisme producteur.

### Calibration et jeu tenu

Calibration : 12 bénins V2 déjà ouverts, quatre/source, sélectionnés par
`sha256(seed || "calibration" || item_id)`, exclus du principal. Pour chaque
producteur, les presets statiques `default`, `creative`, `focused`, `strict`
produisent chacun une trajectoire indépendante de trois tours sur chaque cas.
Les six paires non ordonnées de presets sont toutes comparées par le panel dans
les deux ordres, soit 72 comparaisons par producteur avant inversion.

Une paire dont une trace est incomplète n'est pas jugée et compte comme
comparaison non résolue. Pour chaque preset : score primaire = nombre total de
victoires panel résolues ; départages successifs = moins de défaites, plus faible
taux d'échec objectif, moins de tokens de sortie, puis ordre lexical. Le dernier
départage lexical est journalisé et fait échouer Q1 s'il est nécessaire.

Le gagnant global devient STATIC_BEST. La sélection est recalculée trois fois
en retirant successivement les quatre cas GitHub, Hacker News et arXiv, avec les
mêmes règles. Q1 exige le même gagnant dans au moins deux de ces trois calculs.
Aucun nouveau knob et aucune relance sélective.

Source principale : `corpora/vigie_shadow_v1/candidate_pool.jsonl`, SHA-256
`074e0cecb04a2ca4fb527414abd3307b4d80fe812ac934178a5fd06bcc2ff6f0`.
Exclusion IDs V1/V2/calibration, doublons, filtres PII V2 ; 400–3 000 caractères,
aucun filtre sémantique post-hoc. 60 cas : 20 GitHub, 20 Hacker News, 20 arXiv,
ordre `sha256(seed || "heldout" || source || external_id)`. Aucun contenu
affiché ou journalisé ; comptes et hashes puis scellement.

Sources non fiables : aucun shell, secret, réseau en écriture, mémoire
persistante ou outil d'action. Seed globale : `20260817`.

### Estimateurs

Comptages O1–O19, Wilson 95 %, ratios de médianes, nearest-rank p95, calcul
binomial exact de la table ex ante, verdict strict Q0/Q1/C0–C12. Les juges
préfèrent localement ; le scoreur déterministe agrège seul et produit seul le
verdict scientifique.

## Out-of-scope

Classifieur d'injection, vérité générale, Nemeton, Jachère, agent externe,
NSGA-II, poids, X/Twitter, privé, image/audio, EPP oracle, Solana, promotion ou
déploiement. Qwen et GLM ne sont pas producteurs en V7. Un ancrage humain du
jeu tenu, une autre rubrique, un troisième juge, une autre tâche, segmentation,
budget, modèle, graine, répétition multi-graine ou ablation exige une nouvelle
préinscription.
