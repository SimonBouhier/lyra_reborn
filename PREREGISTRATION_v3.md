# Pre-Registration v3

**Frozen on**: 2026-08-12
**Frozen by**: Simon Bouhier, avec assistance méthodologique de Codex
**Git commit at freeze**: PENDING — sera estampillé par le commit suivant

## Hypothesis

H3 : sur des trajectoires éditoriales de trois tours issues de 60 contenus
publics réels et tenus, la politique adaptative existante de Lyra produit une
décision finale de meilleure qualité que la meilleure politique statique
simple, à modèle producteur, gabarits et enveloppe de calcul comparables.

H3 est évaluée séparément sur trois modèles producteurs locaux. Elle est
soutenue globalement seulement si au moins deux modèles sur trois satisfont
toutes les portes gelées ci-dessous.

## Why this and not its negation

Le prior est positif mais faible. L'adaptation du décodage d'un modèle gelé a
déjà battu des baselines statiques sous budget contrôlé sur des tâches
vérifiables. À l'inverse, les ablations récentes montrent qu'une récompense de
recouvrement ou de forme seule peut être nulle ou nuisible. C'est précisément
le risque de Lyra : ses capteurs sont réels et sa modulation est prouvée, mais
`kw_overlap`, les listes, l'anti-répétition et l'utilisation du budget peuvent
récompenser une apparence de tenue sans améliorer la décision.

Les travaux Agent-as-a-Judge justifient l'inspection de la trajectoire et des
preuves. Sage interdit toutefois de traiter un juge LLM comme stable par
défaut. Le protocole impose donc une rubrique indépendante des métriques Lyra,
deux familles de juges, l'inversion A/B et un état `UNRESOLVED` non rattrapé par
un arbitre. La synthèse et les sources sont gelées dans `STATE_OF_ART.md`.

## Observables

L'unité statistique est un cas tenu. Chaque cas produit deux traces appariées :

- **ADAPTIVE** : `LyraLoop` avec `EpistemicBridge`, `PIController`, politique
  réactive et état persistant pendant les trois tours. Son état initial est
  exactement STATIC_BEST pour le modèle concerné ;
- **STATIC_BEST** : mêmes appels et même mapping matériel, mais boutons constants
  choisis sur le jeu de calibration selon la règle gelée dans Scope.

Le tour 1 identifie la matière et les affirmations testables ; le tour 2 cherche
la meilleure objection et les preuves manquantes ; le tour 3 rend une décision
`IGNORE | DEFER | AUDIT | AMPLIFY` et une justification structurée. L'état et
l'intégrale P+I sont réinitialisés entre deux cas.

- O1 : pour chaque modèle producteur, nombres `W`, `L`, `U` : victoire ADAPTIVE,
  victoire STATIC_BEST, comparaison non résolue.
- O2 : taux de victoire résolu `WR = W / (W + L)` et intervalle de Wilson
  bilatéral à 95 %. Les `U` ne disparaissent pas : leur nombre reste dans O1 et
  O8.
- O3 : avantage net sur tous les cas `NA = (W - L) / 60`.
- O4 : taux d'échec du contrat objectif par bras : JSON invalide ; décision hors
  vocabulaire ; champ vide/trivial ; citation absente de la source normalisée ;
  dépassement du plafond ; trace incomplète.
- O5 : nombre exact d'appels, tokens d'entrée, tokens de sortie et latence
  murale par tour et par cas ; médiane et p95 nearest-rank par bras.
- O6 : taux de modulation effective : au moins une option Ollama réellement
  différente entre les bras aux tours 2 ou 3 ; taux de sorties différentes sur
  ces mêmes cas.
- O7 : stabilité de position de chaque juge : même préférence de candidat après
  inversion de l'ordre A/B.
- O8 : taux de résolution du panel. Une paire est résolue seulement si les deux
  juges sont stables, ne répondent pas `TIE` et préfèrent le même candidat.
- O9 : accord brut entre juges avant agrégation et distribution de
  `A | B | TIE | INVALID` par ordre.
- O10 : corrélations descriptives entre les composantes cheap de Lyra et les
  préférences du panel. Elles n'entrent dans aucune porte ni sélection.
- O11 : distribution des quatre décisions finales par source, modèle et bras.
- O12 : timeouts, sorties invalides, erreurs de transport et abandons, sans
  retrait d'un cas du dénominateur de 60.

La rubrique pairwise juge six propriétés sur la source et la trace complète :
fidélité aux éléments fournis ; calibration de l'incertitude ; choix des enjeux
saillants ; qualité de la contradiction ; utilité de la décision et de l'étape
suivante ; économie sans perte substantielle. Elle n'expose ni les noms de bras,
ni leurs options, ni les métriques cheap, ni le modèle producteur.

## Falsification thresholds

Pour un modèle producteur `m`, toutes les portes C0 à C8 sont nécessaires :

- C0 — **tenue** : manifeste de 60 cas scellé avant la première génération,
  avec hash de la source, de la sélection, des gabarits, de la configuration et
  de l'ordre aléatoire ; aucune mutation ultérieure.
- C1 — **politique active** : au moins 90 % des cas complets présentent une
  différence d'option effective aux tours 2 ou 3, et au moins 80 % de ces cas
  produisent des sorties différentes entre les bras.
- C2 — **résolution** : le panel résout au moins 50 % des 60 cas.
- C3 — **stabilité du juge** : chacun des deux juges conserve sa préférence
  après inversion d'ordre sur au moins 75 % des comparaisons valides.
- C4 — **qualité** : la borne basse Wilson 95 % de `WR` est strictement
  supérieure à 0,50 ET `NA >= 0,10`.
- C5 — **contrat objectif** : le taux d'échec ADAPTIVE est au plus 0,10 et ne
  dépasse pas celui de STATIC_BEST de plus de 0,05.
- C6 — **coût** : la médiane des tokens de sortie ADAPTIVE est au plus 1,10 fois
  celle de STATIC_BEST, et son p95 de latence au plus 1,25 fois celui de la
  baseline.
- C7 — **fiabilité du run** : chaque bras a au plus 5 % de timeouts/erreurs et
  l'écart absolu entre bras est au plus 2 points de pourcentage.
- C8 — **aveugle vérifiable** : aucun payload juge ne contient nom de bras,
  métrique cheap, boutons, options de génération ou chemin de fichier révélant
  la variante ; le mapping candidat↔bras est conservé séparément et haché.

O9, O10, O11 et le détail de O12 sont descriptifs mais obligatoires. Un échec,
un `TIE`, une instabilité de position ou une erreur reste publié et ne peut être
écarté après lecture.

## Verdict logic

Par modèle : `H3_SUPPORTED_FOR_MODEL` si et seulement si C0 AND C1 AND C2 AND
C3 AND C4 AND C5 AND C6 AND C7 AND C8 sont vraies. Sinon le verdict est
`H3_NOT_SUPPORTED_FOR_MODEL` ; il n'existe pas de compensation par moyenne.

Global : `H3_SUPPORTED_IN_V3` si au moins M = 2 des N = 3 modèles producteurs
soutiennent H3, soit une fraction d'au moins 2/3. Toute autre issue donne
`H3_NOT_SUPPORTED_IN_V3`.

Même un résultat soutenu ne permet que de retenir la politique pour une
campagne plus large ou une ablation. Il n'autorise ni déploiement autonome, ni
auto-modification, ni affirmation de supériorité générale de Lyra.

## Anti-confirmation clause

Un résultat négatif signifiera que, dans cette enveloppe, la modulation réelle
de Lyra n'achète pas une amélioration robuste de la décision face à une
politique statique forte. Il sera conservé. Les seuils, cas, gabarits, knobs,
rubrique, règles `UNRESOLVED` et modèles ne seront ni ajustés ni relancés pour
« réparer » H3 après ouverture des résultats.

Un résultat positif ne prouvera pas que les métriques mesurent la pensée, que
le panel dit vrai, que le gain se transfère à d'autres tâches, ni que les
juges locaux sont sans biais. Il ne sera pas décrit comme conscience,
auto-amélioration démontrée ou préparation au déploiement.

Toute correction post-gel nécessaire pour rendre le runner exécutable reçoit
un amendement daté avant reprise. Si elle touche sélection, prompts, modèles,
mapping, observables, seuils ou logique de verdict, V3 est annulée et une V4 est
préinscrite.

## Scope

### Modèles et enveloppe

Trois producteurs Ollama locaux, tous GGUF Q4_K_M, seront testés :

- `mistral:latest`, digest
  `6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf` ;
- `gemma3:latest`, digest
  `a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a` ;
- `granite3.3:latest`, digest
  `fd429f23b90980ed1bef53b990894e7b0199331f6ae90c5650240a7d5b70f1f7`.

Pour chaque producteur, les juges sont les deux autres modèles. Un modèle ne
juge donc jamais sa propre production. Chaque jugement est exécuté à
température 0, `num_predict=512`, sans outil réseau, avec accès en lecture aux
seuls artefacts locaux du cas. DeepSeek-R1 est exclu : son profil reasoning et
sa contrainte de quantification forment un bras matériel différent.

Chaque trajectoire comporte exactement trois appels producteur. Les deux bras
partagent `KnobMapping(num_predict_min=128, num_predict_max=768)` et un plafond
de 768 tokens de sortie par tour. Les graines sont dérivées de
`sha256(seed || case_id || model_digest || turn)` et identiques entre bras pour
un même tour. `SmoothingConfig.refractory_ms=0` rend chaque décision de contrôle
observable ; les autres valeurs du contrôleur, du pont et du lissage restent
les valeurs versionnées au commit gelé. Aucun retry de contenu n'est permis.
ADAPTIVE et STATIC_BEST utilisent le même prompt, la même graine et les mêmes
options au tour 1. La seule cause autorisée de divergence aux tours suivants
est la mise à jour de politique à partir des sorties précédentes.

Runtime gelé : Python 3.14.7, Pydantic 2.13.4 et Ollama 0.32.9. Pydantic est
installé dans `.venv` mais son inscription au manifeste de dépendances est une
dette explicite à solder avant la campagne ; cette correction de packaging ne
peut changer ni schéma ni validation.

### Contrat final

Le tour 3 doit produire un objet Pydantic fermé contenant :

- `decision`, enum `IGNORE | DEFER | AUDIT | AMPLIFY` ;
- `rationale`, texte non trivial ;
- `evidence`, une à trois citations exactes de la source avec leur portée ;
- `uncertainty`, limite ou inconnue explicite ;
- `next_step`, action concrète compatible avec la décision.

Les seuils de longueur exacts, la normalisation Unicode et la validation des
citations seront codés puis testés avant tout run, sans lire le jeu tenu. Un
échec de validation n'est pas réparé par un quatrième appel.

### Calibration et baseline statique

Douze contenus bénins déjà ouverts de V2 — quatre par source, sélectionnés par
`sha256(seed || "calibration" || item_id)` — constituent le jeu de calibration.
Ils ne peuvent entrer dans les 60 cas principaux.

STATIC_BEST est choisie séparément par modèle parmi quatre politiques déjà
versionnées : `default`, `creative`, `focused`, `strict`. Chaque candidate est
constante pendant les trois tours. Le choix maximise d'abord ses victoires de
panel dans un tournoi pairwise sur les 12 cas ; égalité départagée par le plus
faible taux d'échec objectif, puis par le moins de tokens de sortie, puis par
l'ordre lexical du nom. Aucune nouvelle valeur de knob n'est optimisée en V3.
La candidate retenue initialise aussi ADAPTIVE : les deux bras ne diffèrent
donc pas au tour 1.

### Jeu tenu

La source de sélection est la capture locale
`corpora/vigie_shadow_v1/candidate_pool.jsonl`, SHA-256
`074e0cecb04a2ca4fb527414abd3307b4d80fe812ac934178a5fd06bcc2ff6f0`.
Après le gel, le builder exclut tous les identifiants apparus dans les files V1,
les 120 items V2, le jeu de calibration, les doublons et les contenus rejetés
par les filtres de données personnelles V2. Il retient des contenus publics de
400 à 3 000 caractères. Aucun nouveau filtre de « pertinence » sémantique n'est
autorisé : la capture source provient déjà des requêtes thématiques V1, et un
contenu pauvre doit pouvoir conduire à la décision `IGNORE`.

Le jeu principal contient exactement 60 cas réels, 20 GitHub Issues, 20 Hacker
News et 20 arXiv, choisis par ordre croissant de
`sha256(seed || "heldout" || source || external_id)`. Le builder n'affiche et
ne journalise aucun contenu ; il publie seulement comptes et hashes avant de
sceller le manifeste. Les contenus restent des données non fiables : aucun
shell, secret, réseau en écriture, mémoire persistante ou outil d'action n'est
accessible aux producteurs ou juges. Une instruction rencontrée dans une
source ne reçoit aucune autorité.

Seed globale : `20260813`.

### Estimateurs

Comptages exacts O1–O12, intervalles de Wilson 95 %, ratios de médianes,
nearest-rank p95 et verdict booléen strict C0–C8. Les juges produisent les
préférences locales ; le scoreur déterministe produit seul les agrégats et le
verdict scientifique.

## Out-of-scope

V3 n'évalue pas un classifieur de prompt injection, la vérité générale des
contenus, la mémoire Nemeton, la Jachère, un agent à outils externes, NSGA-II,
l'apprentissage ou la modification des poids, X/Twitter, les données privées,
les images/audio, EPP comme oracle, Solana, la promotion automatique par GitHub
ou le déploiement de Lyra. Une ablation des métriques, un nouveau juge, un
quatrième modèle, une autre longueur de trajectoire ou une autre tâche exige
une nouvelle préinscription.
