# Pre-Registration v6

**Frozen on**: 2026-08-12
**Frozen by**: Simon Bouhier, avec assistance méthodologique de Codex
**Git commit at freeze**: PENDING — sera estampillé par le commit suivant

## Hypothesis

H6 : conditionnellement à un premier tour strictement commun, la politique
adaptative existante de Lyra produit, sur les deux tours suivants, une décision
éditoriale finale de meilleure qualité que la meilleure politique statique
simple, sur 60 contenus publics réels et tenus, à modèle, gabarits et enveloppe
de calcul comparables.

H6 est évaluée séparément sur trois modèles producteurs locaux et soutenue
globalement seulement si au moins deux modèles sur trois franchissent toutes
les portes gelées.

## Why this and not its negation

Le prior reste positif mais faible selon `STATE_OF_ART.md` : l'adaptation de
décodage est plausible, mais les proxys cheap ne doivent jamais juger la
politique qui les optimise.

V3 a été arrêtée avant jeu tenu faute de préfixe déterministe ; V4, avant
calibration, car la copie verbatim dominait le contrat ; V5 a qualifié COMMON
T1, les ancres source et les six branches producteur sur smoke synthétique,
puis son premier juge a épuisé six étapes sans verdict. Les statuts sont
conservés dans `docs/P7_V3_STATUS.md`, `docs/P7_V4_STATUS.md` et
`docs/P7_V5_STATUS.md`.

Le budget V5 comptait les lectures minimales, pas la vérification des ancres.
V6 garde six étapes mais remplace les checks unitaires par un check batch par
candidat. Le juge peut ainsi inspecter toutes les preuves sans coût variable :
SOURCE, TRACE A, TRACE B, SPANS A, SPANS B, VERDICT.

## Observables

Un cas/modèle contient : COMMON T1 généré une fois avec STATIC_BEST et copié
byte-for-byte ; ADAPTIVE T2–T3 après observation et modulation ; STATIC_BEST
T2–T3 sans changement. Les branches suivent ABBA ou BAAB et les états sont
réinitialisés entre cas.

- O1 : `W`, `L`, `U` par producteur.
- O2 : `WR = W / (W + L)` et Wilson bilatéral 95 %.
- O3 : `NA = (W - L) / 60`.
- O4 : taux d'échec objectif : JSON/schéma ; décision ; vide/trivial ; ancre
  absente ; dépassement ; trace incomplète.
- O5 : appels, tokens et latence du préfixe et des branches ; médiane et p95.
- O6 : taux de différence d'option aux tours 2 ou 3.
- O7 : égalité COMMON T1 : prompt, options, graine, sortie, SHA-256.
- O8 : stabilité de préférence de chaque juge après inversion.
- O9 : taux de résolution du panel : deux juges stables, non `TIE`, unanimes.
- O10 : accord brut et `A | B | TIE | INVALID` par ordre.
- O11 : cheap metrics ↔ préférences, descriptif uniquement.
- O12 : décisions par source, modèle et branche.
- O13 : timeouts, invalides, erreurs, abandons, sans retrait.
- O14 : O1–O5 séparés ABBA/BAAB.
- O15 : segments, IDs référencés et réutilisation entre branches.
- O16 : pour chaque jugement, séquence des six actions, étapes consommées et
  statut des deux batches d'ancres, sans exposer le contenu des traces.

La rubrique pairwise reste : fidélité aux segments ; incertitude ; saillance ;
contradiction ; utilité de la décision/étape suivante ; économie. Aucun nom de
branche, knob, option, métrique cheap ou modèle producteur n'est montré.

## Falsification thresholds

Pour un producteur `m`, C0–C11 doivent toutes être vraies :

- C0 : manifeste 60 cas scellé avant COMMON T1 avec tous les hashes.
- C1 : 60/60 préfixes strictement identiques entre traces.
- C2 : au moins 90 % des cas complets changent d'option aux tours 2 ou 3.
- C3 : panel résolu sur au moins 50 % des 60 cas.
- C4 : chaque juge garde sa préférence après inversion sur au moins 75 % des
  comparaisons valides.
- C5 : borne basse Wilson 95 % de `WR` > 0,50 ET `NA >= 0,10`.
- C6 : échec ADAPTIVE <= 0,10 et au plus 0,05 au-dessus de STATIC_BEST.
- C7 : tours 2–3, médiane tokens ADAPTIVE <= 1,10 fois STATIC_BEST et p95
  latence <= 1,25 fois. Coût commun séparé et alloué également en descriptif.
- C8 : chaque branche <= 5 % timeouts/erreurs et écart <= 2 points.
- C9 : aveugle vérifiable et mapping candidat↔branche séparé/haché.
- C10 : exactement 30 ABBA et 30 BAAB par modèle ; cinq appels producteur par
  cas complet.
- C11 : chaque jugement valide contient exactement, avant verdict, au moins une
  lecture SOURCE, une TRACE A, une TRACE B, un CHECK_SPANS A et un CHECK_SPANS
  B ; `steps <= 6`. Toute absence donne `INVALID`, jamais une préférence.

O10–O16 restent obligatoires même lorsqu'ils ne sont pas des portes. Aucun
échec, `TIE`, instabilité, batch défavorable ou erreur ne peut être retiré.

## Verdict logic

Par modèle : `H6_SUPPORTED_FOR_MODEL` si et seulement si C0 AND C1 AND C2 AND
C3 AND C4 AND C5 AND C6 AND C7 AND C8 AND C9 AND C10 AND C11. Sinon :
`H6_NOT_SUPPORTED_FOR_MODEL`.

Global : `H6_SUPPORTED_IN_V6` si au moins M = 2 des N = 3 producteurs
soutiennent H6, fraction minimale 2/3. Sinon : `H6_NOT_SUPPORTED_IN_V6`.

Un soutien autorise seulement une ablation ou campagne plus large, jamais
déploiement, auto-modification ou supériorité générale.

## Anti-confirmation clause

Un résultat négatif sera conservé comme absence de gain robuste dans cette
enveloppe. Cas, seuils, prompts, segmentation, knobs, ordre, six actions,
rubrique, `UNRESOLVED` et modèles ne seront pas ajustés après ouverture.

Un résultat positif ne prouvera ni conscience, ni vérité du panel, ni transfert,
ni absence de biais. Toute correction post-gel reçoit un amendement ; si elle
touche un élément précédent, observables ou verdict, V6 est annulée et V7
préinscrite.

## Scope

### Modèles et runtime

- `mistral:latest`, digest
  `6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf` ;
- `gemma3:latest`, digest
  `a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a` ;
- `granite3.3:latest`, digest
  `fd429f23b90980ed1bef53b990894e7b0199331f6ae90c5650240a7d5b70f1f7`.

Tous GGUF Q4_K_M. Les deux modèles autres que le producteur jugent ; aucun
auto-jugement. DeepSeek-R1 exclu. Python 3.14.7, Pydantic 2.13.4, Ollama 0.32.9.
Pydantic doit entrer au manifeste avant campagne sans modifier le schéma.

### Segmentation et contrat

Règle V5 inchangée : NFC, espaces compactés, découpe gloutonne par mots à 220
caractères, mot long indivisible, IDs continus `S001…S999`, source vide/plus de
999 segments en échec. SOURCE affiche `[S001] texte`. Le JSON canonique compact
des segments est haché.

Contrat fermé inchangé : décision enum ; rationale 80–1 200 ; une à trois
preuves avec `source_span_id` appartenant à l'enum du cas et `why` 30–400 ;
uncertainty 30–600 ; next_step 20–500. Format JSON Schema natif, validation
Pydantic, aucune réparation.

### Juge batché

Température 0, `num_predict=512`, six étapes maximum. Actions fermées :
`READ_SOURCE`, `READ_TRACE`, `CHECK_SPANS`, `VERDICT`. Les anciennes
`READ_TURN`, `CHECK_SPAN`, `CONTRACT_STATUS` sont retirées de l'enum V6.

`CHECK_SPANS(candidate)` lit uniquement la décision finale déjà validée du
candidat. Il retourne une liste bornée de une à trois entrées
`{source_span_id, found, text}`. `found` doit être vrai pour chacune par contrat ;
le texte est celui du segment local. Aucun ID fourni librement par le juge.

Un verdict est accepté seulement après SOURCE, TRACE A, TRACE B, CHECK_SPANS A
et B. Séquence recommandée explicitement dans le prompt, avec compteur
`step/6`. Le sixième appel doit être VERDICT. Sortie du budget : `INVALID`.

### Préfixe, branches et ordre

Un client producteur/cas ; mapping 128–768 ; COMMON T1 STATIC_BEST copié dans
deux états frais ; ADAPTIVE module après observation, STATIC reste fixe ;
`refractory_ms=0`. Graines par
`sha256(seed || case_id || model_digest || turn)`, sans garantie déterministe.

ABBA : A puis B au tour 2, B puis A au tour 3 ; BAAB inverse. Tri par
`sha256(seed || "execution_order" || model_digest || case_id)`, 30/30, aucun
parallélisme producteur.

### Calibration et jeu tenu

Calibration : 12 bénins V2 déjà ouverts, quatre/source, sélectionnés par
`sha256(seed || "calibration" || item_id)`, exclus du principal. STATIC_BEST
par modèle parmi `default`, `creative`, `focused`, `strict` : victoires panel,
puis échec objectif, tokens, ordre lexical. Aucun nouveau knob.

Source principale : `corpora/vigie_shadow_v1/candidate_pool.jsonl`, SHA-256
`074e0cecb04a2ca4fb527414abd3307b4d80fe812ac934178a5fd06bcc2ff6f0`.
Exclusion IDs V1/V2/calibration, doublons, filtres PII V2 ; 400–3 000 caractères,
aucun filtre sémantique post-hoc. 60 cas : 20 GitHub, 20 Hacker News, 20 arXiv,
ordre `sha256(seed || "heldout" || source || external_id)`. Aucun contenu
affiché/journalisé ; comptes et hashes puis scellement.

Sources non fiables : aucun shell, secret, réseau en écriture, mémoire
persistante ou outil d'action. Seed globale : `20260816`.

### Estimateurs

Comptages O1–O16, Wilson 95 %, ratios médianes, nearest-rank p95, verdict strict
C0–C11. Les juges préfèrent localement ; le scoreur déterministe agrège seul.

## Out-of-scope

Classifieur d'injection, vérité générale, Nemeton, Jachère, agent externe,
NSGA-II, poids, X/Twitter, privé, image/audio, EPP oracle, Solana, promotion ou
déploiement. Toute autre tâche, segmentation, budget, outil, juge, quatrième
modèle, répétition multi-graine ou ablation exige une nouvelle préinscription.
