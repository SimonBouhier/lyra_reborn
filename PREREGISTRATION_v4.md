# Pre-Registration v4

**Frozen on**: 2026-08-12
**Frozen by**: Simon Bouhier, avec assistance méthodologique de Codex
**Git commit at freeze**: 93fc5611f09c1622a469bc54427dd920c8455d76

## Hypothesis

H4 : conditionnellement à un premier tour strictement commun, la politique
adaptative existante de Lyra produit, sur les deux tours suivants, une décision
éditoriale finale de meilleure qualité que la meilleure politique statique
simple, sur 60 contenus publics réels et tenus, à modèle, gabarits et enveloppe
de calcul comparables.

H4 est évaluée séparément sur trois modèles producteurs locaux. Elle est
soutenue globalement seulement si au moins deux modèles sur trois satisfont
toutes les portes gelées ci-dessous.

## Why this and not its negation

Le prior reste positif mais faible pour les raisons consignées dans
`STATE_OF_ART.md` : l'adaptation de décodage est plausible et publiée, mais les
proxys de recouvrement et de forme peuvent être circulaires ou nuisibles.

V3 n'a ouvert aucun cas tenu et n'a produit aucun verdict sur H3. Son smoke-test
synthétique a toutefois invalidé son attribution causale : deux appels Ollama
avec prompt, options et graine identiques ont produit des sorties différentes.
Cette observation est conservée dans `docs/P7_V3_STATUS.md`. La graine ne peut
donc pas jouer le rôle d'un couplage exact des deux bras sur ce runtime.

V4 remplace les deux générations concurrentes du tour 1 par un unique préfixe
réel partagé byte-for-byte. Lyra observe ce préfixe et adapte son état ; la
baseline le reçoit sans changer ses boutons. Le bruit résiduel des appels de
branche est traité comme bruit expérimental et leur ordre est contrebalancé. Ce
dessin isole mieux la décision de politique sans prétendre rendre le LLM
déterministe.

## Observables

L'unité statistique est un cas tenu pour un modèle producteur. Chaque unité
contient un préfixe commun et deux branches :

- **COMMON T1** : un appel producteur avec STATIC_BEST ; sa sortie, son prompt,
  ses options et sa graine sont copiés à l'identique dans les deux traces ;
- **ADAPTIVE T2–T3** : l'état Lyra a observé COMMON T1 puis applique
  `EpistemicBridge`, `PIController` et la politique réactive ;
- **STATIC_BEST T2–T3** : mêmes gabarits et préfixe, boutons constants.

Le tour 1 identifie la matière et les affirmations testables ; le tour 2 cherche
la meilleure objection et les preuves manquantes ; le tour 3 rend une décision
`IGNORE | DEFER | AUDIT | AMPLIFY` et sa justification structurée. Tous les
états et l'intégrale P+I sont réinitialisés entre deux cas.

- O1 : pour chaque producteur, nombres `W`, `L`, `U` : victoire ADAPTIVE,
  victoire STATIC_BEST, comparaison non résolue.
- O2 : taux de victoire résolu `WR = W / (W + L)` et intervalle de Wilson
  bilatéral à 95 %.
- O3 : avantage net sur tous les cas `NA = (W - L) / 60`.
- O4 : taux d'échec du contrat objectif par branche : JSON invalide ; décision
  hors vocabulaire ; champ vide/trivial ; citation absente de la source
  normalisée ; dépassement de plafond ; trace incomplète.
- O5 : appels physiques, tokens d'entrée, tokens de sortie et latence murale du
  préfixe commun et de chaque appel de branche ; médiane et p95 nearest-rank.
- O6 : taux de modulation effective : au moins une option Ollama réellement
  différente entre ADAPTIVE et STATIC_BEST aux tours 2 ou 3.
- O7 : intégrité du préfixe : égalité byte-for-byte des prompts, options,
  sorties et hashes COMMON T1 présents dans les deux traces.
- O8 : stabilité de position de chaque juge : même préférence de candidat après
  inversion A/B.
- O9 : taux de résolution du panel. Une paire est résolue seulement si les deux
  juges sont stables, ne répondent pas `TIE` et préfèrent le même candidat.
- O10 : accord brut entre juges et distribution de
  `A | B | TIE | INVALID` par ordre.
- O11 : corrélations descriptives entre composantes cheap et préférences du
  panel. Elles n'entrent dans aucune porte ni sélection.
- O12 : distribution des quatre décisions par source, modèle et branche.
- O13 : timeouts, sorties invalides, erreurs de transport et abandons, sans
  retrait d'un cas du dénominateur de 60.
- O14 : résultats O1–O5 séparés selon l'ordre d'exécution ABBA ou BAAB, afin de
  rendre visible un effet de chauffe, de cache ou de dérive temporelle.

La rubrique pairwise juge six propriétés sur la source et les traces complètes :
fidélité ; calibration de l'incertitude ; saillance ; qualité de la
contradiction ; utilité de la décision/étape suivante ; économie sans perte
substantielle. Elle n'expose ni noms de branches, ni options, ni métriques cheap,
ni modèle producteur.

## Falsification thresholds

Pour un modèle producteur `m`, toutes les portes C0 à C10 sont nécessaires :

- C0 — **tenue** : manifeste de 60 cas scellé avant COMMON T1, avec hashes de
  source, sélection, gabarits, configuration, ordre et mapping aveugle ; aucune
  mutation ultérieure.
- C1 — **préfixe commun** : 60/60 paires ont des prompt, options, graine, sortie
  et SHA-256 de tour 1 strictement identiques entre les deux traces.
- C2 — **politique active** : au moins 90 % des cas complets présentent une
  différence d'option effective aux tours 2 ou 3. La différence de sortie live
  n'est pas une porte de modulation, car le runtime est stochastique.
- C3 — **résolution** : le panel résout au moins 50 % des 60 cas.
- C4 — **stabilité du juge** : chacun des deux juges conserve sa préférence
  après inversion sur au moins 75 % des comparaisons valides.
- C5 — **qualité** : la borne basse Wilson 95 % de `WR` est strictement
  supérieure à 0,50 ET `NA >= 0,10`.
- C6 — **contrat objectif** : le taux d'échec ADAPTIVE est au plus 0,10 et ne
  dépasse pas celui de STATIC_BEST de plus de 0,05.
- C7 — **coût marginal** : sur les seuls tours 2–3, la médiane des tokens de
  sortie ADAPTIVE est au plus 1,10 fois celle de STATIC_BEST, et son p95 de
  latence au plus 1,25 fois celui de la baseline. Le coût commun est rapporté
  séparément et alloué également aux deux traces dans tout total descriptif.
- C8 — **fiabilité** : chaque branche a au plus 5 % de timeouts/erreurs et
  l'écart absolu entre branches est au plus 2 points de pourcentage.
- C9 — **aveugle vérifiable** : aucun payload juge ne contient nom de branche,
  métrique cheap, boutons, options de génération ou chemin révélant la variante ;
  le mapping candidat↔branche est séparé et haché.
- C10 — **contrebalancement** : pour chaque producteur, le manifeste contient
  exactement 30 cas ABBA et 30 cas BAAB ; chaque cas complet contient un appel
  commun et deux appels par branche, soit cinq appels physiques.

O10, O11, O12, O14 et le détail de O13 sont descriptifs mais obligatoires. Un
échec, un `TIE`, une instabilité, un ordre défavorable ou une erreur reste
publié et ne peut être retiré après lecture.

## Verdict logic

Par modèle : `H4_SUPPORTED_FOR_MODEL` si et seulement si C0 AND C1 AND C2 AND
C3 AND C4 AND C5 AND C6 AND C7 AND C8 AND C9 AND C10 sont vraies. Sinon le
verdict est `H4_NOT_SUPPORTED_FOR_MODEL`. Aucune moyenne ne compense une porte.

Global : `H4_SUPPORTED_IN_V4` si au moins M = 2 des N = 3 modèles producteurs
soutiennent H4, soit une fraction d'au moins 2/3. Toute autre issue donne
`H4_NOT_SUPPORTED_IN_V4`.

Même un résultat soutenu autorise seulement une ablation ou une campagne plus
large. Il n'autorise ni déploiement autonome, ni auto-modification, ni
affirmation de supériorité générale de Lyra.

## Anti-confirmation clause

Un résultat négatif signifiera que, dans cette enveloppe à préfixe commun, la
modulation réelle de Lyra n'achète pas une amélioration robuste face à une
politique statique forte. Il sera conservé. Seuils, cas, gabarits, knobs,
rubrique, ordre, règles `UNRESOLVED` et modèles ne seront pas ajustés après
ouverture pour réparer H4.

Un résultat positif ne prouvera pas que les métriques mesurent la pensée, que
le panel dit vrai, que le gain se transfère, ni que les juges sont sans biais.
Il ne sera pas décrit comme conscience, auto-amélioration démontrée ou
préparation au déploiement.

Toute correction post-gel nécessaire à l'exécution reçoit un amendement daté
avant reprise. Si elle touche sélection, prompts, modèles, mapping, préfixe
commun, ordre, observables, seuils ou verdict, V4 est annulée et V5 préinscrite.

## Scope

### Modèles et runtime

Trois producteurs Ollama locaux, GGUF Q4_K_M :

- `mistral:latest`, digest
  `6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf` ;
- `gemma3:latest`, digest
  `a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a` ;
- `granite3.3:latest`, digest
  `fd429f23b90980ed1bef53b990894e7b0199331f6ae90c5650240a7d5b70f1f7`.

Pour chaque producteur, les juges sont les deux autres modèles ; aucun modèle ne
juge sa propre sortie. Chaque jugement utilise température 0,
`num_predict=512`, six étapes au maximum, aucun outil réseau et quatre lectures
minimales : SOURCE, TRACE A, TRACE B, VERDICT. DeepSeek-R1 reste exclu en raison
de son profil reasoning et de sa contrainte de quantification distincte.

Runtime : Python 3.14.7, Pydantic 2.13.4, Ollama 0.32.9. La dette d'inscription
de Pydantic au manifeste doit être soldée avant la campagne sans changer schéma
ni validation.

### Préfixe commun et branches

Chaque cas utilise un unique client du modèle producteur et
`KnobMapping(num_predict_min=128, num_predict_max=768)`. COMMON T1 est généré
avec STATIC_BEST. Ses prompt, options, graine, sortie et métriques sont
enregistrés une fois.

Deux états frais, initialisés avec STATIC_BEST, reçoivent ensuite exactement ce
même tour dans leur historique. L'état ADAPTIVE applique une seule décision de
contrôle aux métriques communes ; l'état STATIC_BEST n'est pas modifié. Les deux
branches utilisent leurs propres sorties pour construire les tours suivants.
`SmoothingConfig.refractory_ms=0` ; les autres valeurs versionnées du contrôleur,
du pont et du lissage restent inchangées.

Les graines sont dérivées de
`sha256(seed || case_id || model_digest || turn)` et restent égales entre
branches, mais ne sont pas interprétées comme une garantie de déterminisme.

L'ordre est ABBA ou BAAB : pour ABBA, ADAPTIVE s'exécute avant STATIC_BEST au
tour 2, puis STATIC_BEST avant ADAPTIVE au tour 3 ; BAAB inverse ces positions.
Pour chaque producteur, les 60 cas sont triés par
`sha256(seed || "execution_order" || model_digest || case_id)` ; les 30 premiers
sont ABBA et les 30 suivants BAAB. Aucun parallélisme producteur n'est permis.

### Contrat final

Le schéma et les seuils sont ceux de `eval/p7_contracts.py` au commit gelé :
enum `IGNORE | DEFER | AUDIT | AMPLIFY`, rationale 80–1 200 caractères, une à
trois preuves, citation 20–240, portée 30–400, incertitude 30–600, étape suivante
20–500. Chaque citation normalisée NFC doit être une sous-chaîne exacte de la
source normalisée. JSON strict, schéma fermé, aucun appel de réparation.

### Calibration et STATIC_BEST

Douze contenus bénins déjà ouverts de V2 — quatre par source, sélectionnés par
`sha256(seed || "calibration" || item_id)` — servent uniquement à la
calibration. Ils ne peuvent entrer dans les 60 cas principaux.

STATIC_BEST est choisie séparément par modèle parmi `default`, `creative`,
`focused`, `strict`, toutes constantes sur trois tours. Le tournoi pairwise sur
les 12 cas maximise les victoires de panel ; égalité départagée par taux
d'échec objectif, puis tokens de sortie, puis ordre lexical. Aucune nouvelle
valeur de knob n'est optimisée.

### Jeu tenu

Source : `corpora/vigie_shadow_v1/candidate_pool.jsonl`, SHA-256
`074e0cecb04a2ca4fb527414abd3307b4d80fe812ac934178a5fd06bcc2ff6f0`.
Après le gel, le builder exclut tous les identifiants V1, les 120 items V2, la
calibration, les doublons et les contenus rejetés par les filtres de données
personnelles V2. Il conserve les contenus publics de 400 à 3 000 caractères,
sans nouveau filtre sémantique post-hoc.

Le jeu principal contient 60 cas : 20 GitHub Issues, 20 Hacker News, 20 arXiv,
choisis par ordre croissant de
`sha256(seed || "heldout" || source || external_id)`. Le builder n'affiche ni ne
journalise leur contenu ; il publie comptes et hashes puis scelle le manifeste.

Les sources restent des données non fiables. Producteurs et juges n'ont accès à
aucun shell, secret, réseau en écriture, mémoire persistante ou outil d'action.
Une instruction dans la source ne reçoit aucune autorité.

Seed globale : `20260814`.

### Estimateurs

Comptages O1–O14, Wilson 95 %, ratios de médianes, nearest-rank p95 et verdict
booléen C0–C10. Les juges produisent les préférences locales ; le scoreur
déterministe produit seul agrégats et verdict scientifique.

## Out-of-scope

V4 n'évalue pas un classifieur d'injection, la vérité générale des contenus,
Nemeton, la Jachère, un agent à outils externes, NSGA-II, l'apprentissage des
poids, X/Twitter, les données privées, image/audio, EPP comme oracle, Solana,
promotion automatique ou déploiement. Une répétition multi-graine, une autre
tâche, un nouveau juge, un quatrième modèle ou une ablation exige une nouvelle
préinscription.
