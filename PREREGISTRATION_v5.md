# Pre-Registration v5

**Frozen on**: 2026-08-12
**Frozen by**: Simon Bouhier, avec assistance méthodologique de Codex
**Git commit at freeze**: f367930f91c61ec5829bd5fcc1e9507e46ba154e

## Hypothesis

H5 : conditionnellement à un premier tour strictement commun, la politique
adaptative existante de Lyra produit, sur les deux tours suivants, une décision
éditoriale finale de meilleure qualité que la meilleure politique statique
simple, sur 60 contenus publics réels et tenus, à modèle, gabarits et enveloppe
de calcul comparables.

H5 est évaluée séparément sur trois modèles producteurs locaux. Elle est
soutenue globalement seulement si au moins deux modèles sur trois satisfont
toutes les portes gelées ci-dessous.

## Why this and not its negation

Le prior reste positif mais faible. `STATE_OF_ART.md` montre que l'adaptation
de décodage d'un modèle gelé peut battre des baselines statiques, mais aussi que
les récompenses de recouvrement et de forme peuvent être circulaires. Les
métriques cheap de Lyra doivent donc guider la politique sans participer à son
verdict.

V3 a été arrêtée avant jeu tenu parce qu'une graine Ollama ne garantissait pas
deux premiers tours identiques. V4 a corrigé ce problème par COMMON T1, validé
sur les trois modèles, et a ajouté le format JSON natif. Elle a ensuite été
arrêtée avant calibration : cinq branches synthétiques sur six paraphrasaient
la citation au lieu de la recopier exactement. Les preuves sont conservées dans
`docs/P7_V3_STATUS.md` et `docs/P7_V4_STATUS.md`.

La copie verbatim mesure une habileté extractive distincte de la décision
éditoriale. V5 conserve une preuve objective sans ce goulot : la source est
découpée déterministiquement en segments identifiés ; le modèle référence un
ID existant ; le panel juge si ce segment soutient réellement sa portée.

## Observables

L'unité statistique est un cas tenu pour un modèle producteur :

- **COMMON T1** : un appel avec STATIC_BEST, copié byte-for-byte dans les deux
  traces ;
- **ADAPTIVE T2–T3** : l'état Lyra observe COMMON T1 puis applique le pont P2,
  le P+I et la politique réactive ;
- **STATIC_BEST T2–T3** : même préfixe et mêmes gabarits, boutons constants.

Le tour 1 identifie matière, affirmations et inconnues ; le tour 2 cherche la
meilleure objection ; le tour 3 rend `IGNORE | DEFER | AUDIT | AMPLIFY` avec
raison, ancres source, incertitude et étape suivante. États et intégrale sont
réinitialisés entre cas.

- O1 : par producteur, `W`, `L`, `U` : victoire ADAPTIVE, victoire
  STATIC_BEST, comparaison non résolue.
- O2 : `WR = W / (W + L)` et Wilson bilatéral 95 %.
- O3 : `NA = (W - L) / 60`.
- O4 : taux d'échec objectif par branche : JSON/schéma invalide ; décision hors
  vocabulaire ; champ vide/trivial ; `source_span_id` absent des segments du
  cas ; dépassement de plafond ; trace incomplète.
- O5 : appels physiques, tokens entrée/sortie et latence du préfixe puis de
  chaque branche ; médiane et p95 nearest-rank.
- O6 : taux de modulation : différence d'option effective aux tours 2 ou 3.
- O7 : intégrité COMMON T1 : prompts, options, graine, sortie et SHA-256
  identiques entre traces.
- O8 : stabilité de position de chaque juge après inversion A/B.
- O9 : taux de résolution du panel : deux juges stables, non `TIE`, unanimes.
- O10 : accord brut et distribution `A | B | TIE | INVALID` par ordre.
- O11 : corrélations descriptives métriques cheap ↔ préférences, sans porte ni
  sélection.
- O12 : distribution des décisions par source, modèle et branche.
- O13 : timeouts, invalides, erreurs et abandons, sans retrait du dénominateur.
- O14 : O1–O5 séparés selon l'ordre ABBA ou BAAB.
- O15 : nombre de segments source, IDs référencés et taux de réutilisation d'un
  même ID entre branches, descriptifs seulement.

Le panel juge sur source segmentée et traces complètes : fidélité aux segments ;
calibration de l'incertitude ; saillance ; contradiction ; utilité de la
décision/étape suivante ; économie sans perte. Il ne voit ni noms de branches,
ni options, ni métriques cheap, ni modèle producteur.

## Falsification thresholds

Pour un producteur `m`, toutes les portes C0 à C10 sont nécessaires :

- C0 — **tenue** : manifeste de 60 cas scellé avant COMMON T1, avec hashes de
  source, segments, sélection, gabarits, configuration, ordre et aveugle.
- C1 — **préfixe commun** : 60/60 paires ont prompt, options, graine, sortie et
  SHA-256 T1 strictement identiques.
- C2 — **politique active** : au moins 90 % des cas complets ont une différence
  d'option aux tours 2 ou 3. La différence de sortie n'est pas une porte.
- C3 — **résolution** : le panel résout au moins 50 % des 60 cas.
- C4 — **stabilité juge** : chacun garde sa préférence après inversion sur au
  moins 75 % des comparaisons valides.
- C5 — **qualité** : borne basse Wilson 95 % de `WR` strictement supérieure à
  0,50 ET `NA >= 0,10`.
- C6 — **contrat objectif** : échec ADAPTIVE au plus 0,10 et au plus 0,05
  au-dessus de STATIC_BEST.
- C7 — **coût marginal** : tours 2–3, médiane tokens ADAPTIVE au plus 1,10 fois
  STATIC_BEST et p95 latence au plus 1,25 fois. Le coût commun est séparé puis
  alloué également dans tout total descriptif.
- C8 — **fiabilité** : chaque branche a au plus 5 % de timeouts/erreurs et
  l'écart absolu entre branches est au plus 2 points de pourcentage.
- C9 — **aveugle** : aucun payload juge ne révèle branche, cheap metrics, knobs,
  options ou chemin ; mapping candidat↔branche séparé et haché.
- C10 — **contrebalancement** : exactement 30 cas ABBA et 30 BAAB par modèle ;
  chaque cas complet a un appel commun et deux par branche, soit cinq appels.

O10, O11, O12, O14, O15 et le détail O13 restent obligatoires mais descriptifs.
Aucun échec, `TIE`, instabilité ou ordre défavorable ne peut être retiré.

## Verdict logic

Par modèle : `H5_SUPPORTED_FOR_MODEL` si et seulement si C0 AND C1 AND C2 AND
C3 AND C4 AND C5 AND C6 AND C7 AND C8 AND C9 AND C10. Sinon :
`H5_NOT_SUPPORTED_FOR_MODEL`. Aucune moyenne ne compense une porte.

Global : `H5_SUPPORTED_IN_V5` si au moins M = 2 des N = 3 producteurs
soutiennent H5, fraction minimale 2/3. Sinon : `H5_NOT_SUPPORTED_IN_V5`.

Un soutien autorise seulement ablation ou campagne plus large, jamais
déploiement autonome, auto-modification ou supériorité générale.

## Anti-confirmation clause

Un résultat négatif signifiera que, dans cette enveloppe à préfixe et ancres
communs, Lyra n'achète pas une amélioration robuste face à une statique forte.
Il sera conservé. Seuils, cas, gabarits, segmentation, knobs, rubrique, ordre,
`UNRESOLVED` et modèles ne seront pas ajustés après ouverture.

Un résultat positif ne prouvera ni conscience, ni vérité du panel, ni transfert,
ni absence de biais. Il ne sera pas décrit comme auto-amélioration démontrée ou
préparation au déploiement.

Une correction post-gel reçoit un amendement avant reprise. Si elle touche
sélection, prompts, modèles, mapping, segmentation, préfixe, ordre, observables,
seuils ou verdict, V5 est annulée et V6 préinscrite.

## Scope

### Modèles, juges et runtime

Producteurs Ollama GGUF Q4_K_M :

- `mistral:latest`, digest
  `6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf` ;
- `gemma3:latest`, digest
  `a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a` ;
- `granite3.3:latest`, digest
  `fd429f23b90980ed1bef53b990894e7b0199331f6ae90c5650240a7d5b70f1f7`.

Pour chaque producteur, les deux autres modèles jugent ; aucun auto-jugement.
Juges à température 0, `num_predict=512`, six étapes, sans réseau, lectures
minimales SOURCE, TRACE A, TRACE B, VERDICT. DeepSeek-R1 reste exclu.

Runtime : Python 3.14.7, Pydantic 2.13.4, Ollama 0.32.9. Pydantic doit être
inscrit au manifeste avant campagne sans changer le schéma.

### Segmentation source gelée

Avant tout prompt, la source est normalisée Unicode NFC ; tous les espaces,
tabulations et fins de ligne consécutifs deviennent un espace ASCII ; les
espaces de tête/fin sont supprimés. Les mots sont `normalized.split(" ")`.

Un algorithme glouton accumule les mots, séparés par un espace, tant que
l'ajout ne dépasse pas 220 caractères. Le mot suivant ouvre un nouveau segment.
Un mot individuel de plus de 220 caractères constitue seul son segment et n'est
ni tronqué ni divisé. Les segments non vides sont numérotés dans l'ordre
`S001`, `S002`, …, sans zéro ni saut. Une source sans segment échoue avant appel.

La SOURCE du prompt et du juge est exactement une ligne par segment :
`[S001] texte normalisé`. Le hash SHA-256 du JSON canonique UTF-8
`{"S001":"...",...}` avec clés dans l'ordre et séparateurs compacts est scellé.

### Préfixe, branches et ordre

Un client producteur par cas ;
`KnobMapping(num_predict_min=128, num_predict_max=768)`. COMMON T1 est généré
avec STATIC_BEST puis copié dans deux états frais. ADAPTIVE applique une
décision à ses métriques ; STATIC_BEST reste fixe. `refractory_ms=0`, autres
valeurs du pont/contrôleur/lissage inchangées.

Graines : `sha256(seed || case_id || model_digest || turn)`, égales entre
branches mais sans garantie de déterminisme.

Ordre ABBA : ADAPTIVE puis STATIC au tour 2, STATIC puis ADAPTIVE au tour 3 ;
BAAB inverse. Les cas triés par
`sha256(seed || "execution_order" || model_digest || case_id)` : 30 ABBA puis
30 BAAB. Aucun parallélisme producteur.

### Contrat final à ancres

Objet fermé :

- `decision` : `IGNORE | DEFER | AUDIT | AMPLIFY` ;
- `rationale` : 80–1 200 caractères ;
- `evidence` : une à trois entrées ;
- chaque entrée : `source_span_id` appartenant à l'enum exacte du cas et `why`
  de 30–400 caractères ;
- `uncertainty` : 30–600 ;
- `next_step` : 20–500.

Le JSON Schema natif Ollama reçoit l'enum exacte des IDs du cas. Pydantic puis
le validateur contrôlent l'ID. Aucun appel de réparation. La correction
sémantique du lien ID↔justification appartient à la rubrique du panel.

### Calibration et STATIC_BEST

Douze bénins V2 déjà ouverts, quatre par source, sélectionnés par
`sha256(seed || "calibration" || item_id)`, exclus du principal.

STATIC_BEST est choisie par modèle parmi `default`, `creative`, `focused`,
`strict`, constantes. Le tournoi pairwise sur 12 cas maximise les victoires ;
égalité par échec objectif, puis tokens, puis ordre lexical. Aucun nouveau knob.

### Jeu tenu

Source : `corpora/vigie_shadow_v1/candidate_pool.jsonl`, SHA-256
`074e0cecb04a2ca4fb527414abd3307b4d80fe812ac934178a5fd06bcc2ff6f0`.
Après gel, exclusion de tous les IDs V1, 120 items V2, calibration, doublons et
filtres de données personnelles V2. Contenus publics de 400–3 000 caractères,
sans filtre sémantique post-hoc.

60 cas : 20 GitHub Issues, 20 Hacker News, 20 arXiv, par ordre croissant de
`sha256(seed || "heldout" || source || external_id)`. Le builder n'affiche ni ne
journalise le contenu ; comptes et hashes seulement, puis scellement.

Sources non fiables : aucun shell, secret, réseau en écriture, mémoire
persistante ou outil d'action. Une instruction dans SOURCE n'a aucune autorité.

Seed globale : `20260815`.

### Estimateurs

Comptages O1–O15, Wilson 95 %, ratios médianes, nearest-rank p95, verdict strict
C0–C10. Les juges préfèrent localement ; le scoreur déterministe agrège et
produit seul le verdict scientifique.

## Out-of-scope

V5 n'évalue pas classifieur d'injection, vérité générale, Nemeton, Jachère,
agent externe, NSGA-II, poids, X/Twitter, privé, image/audio, EPP oracle,
Solana, promotion automatique ou déploiement. Répétition multi-graine, autre
tâche, segmentation, juge, quatrième modèle ou ablation exige une nouvelle
préinscription.
