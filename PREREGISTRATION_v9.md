# Pre-Registration v9

**Frozen on**: 2026-08-13  
**Frozen by**: Simon Bouhier, avec assistance méthodologique de Codex  
**Git commit at freeze**: `PENDING_FREEZE_COMMIT`

## Hypothesis

H9 : conditionnellement à un premier tour strictement commun, la politique
adaptative existante de Lyra produit, sur les deux tours suivants, un avantage
de qualité éditoriale robuste et pratiquement utile face à la meilleure
politique statique simple observée en calibration, sur 60 contenus publics
réels et tenus, à modèle, gabarits et enveloppe de calcul comparables.

H9 est évaluée séparément sur trois modèles producteurs locaux et soutenue
globalement seulement si au moins deux modèles sur trois franchissent toutes
les portes gelées.

## Why this and not its negation

Le prior reste positif mais faible selon `STATE_OF_ART.md`. Les proxys bon
marché qui pilotent Lyra ne peuvent pas juger la politique qui les optimise ;
la qualité doit être mesurée sur les trajectoires complètes par un panel
aveugle et contrôlé.

V7 a été interrompue avant toute réponse du premier appel Q0. V8 a ensuite
prouvé le cycle de vie du runner mais ses 12 appels Q0 ont tous été rejetés
avant génération par Ollama 0.32.9 : `Failed to initialize samplers: failed to
parse grammar`. Aucun cas de calibration ou tenu n'a été lu. Le diagnostic
différentiel hors campagne, exécuté sur les deux juges, a ensuite établi :

- avec `think=false`, le schéma exact V8 est rejeté par les deux juges ;
- le même schéma, privé uniquement des mots-clés de chaîne `minLength` et
  `maxLength`, est accepté par les deux juges ;
- avec `think=false`, la sortie structurée est placée dans `response` et le
  champ `thinking` est absent ou vide.

Le `done_reason=length` observé dans cette sonde est attendu avec son plafond
diagnostique de 128 tokens et ne constitue pas une qualification de verdict.

V9 conserve par incorporation toutes les décisions scientifiques et
opérationnelles de V8 gelées au commit
`88590fcc59dc1845a4e747b7160da2f68d54afb5` : hypothèse, corpus, seed,
producteurs, juges et digests, fixtures Q0, prompts, rubrique, segmentation,
politiques, knobs, calibration, jeu tenu, seuils C0–C12, observables O1–O19,
verdicts et clause anti-confirmation. Les seules modifications autorisées sont
celles de l'instrument explicitement décrites ci-dessous.

## Observables

O1–O19 sont exactement ceux de `PREREGISTRATION_v8.md` au commit incorporé.
V9 ajoute les observables instrumentaux suivants, sans les utiliser comme
mesure de qualité :

- O20 : SHA-256 canonique du schéma Pydantic complet et du schéma fil Ollama,
  avec liste exacte des mots-clés retirés ;
- O21 : pour chaque appel juge, présence et nombre de caractères de `response`
  et `thinking`, `done_reason`, validation grammaticale, validation Pydantic
  complète et résolution des références ;
- O22 : résultat et preuves de la préqualification Q-1, séparés de Q0 et des
  données expérimentales.

## Falsification thresholds

### Q-1 — préqualification du transport structuré

Avant Q0 et avant tout verrou, lecture ou matérialisation de calibration ou de
tenu, un pack synthétique diagnostique indépendant des trois fixtures Q0 est
construit déterministement. Il n'essaie pas de qualifier la justesse sémantique
du panel. Il qualifie uniquement le transport et les deux niveaux de contrat.

Exactement un appel est envoyé à chacun des deux juges, avec :

- `think=false`, `stream=false`, température 0, `num_predict=2048` et
  `num_ctx=32768` ;
- le prompt juge gelé et le schéma fil V9 ;
- aucune relance, réparation, continuation ni lecture de `thinking` comme
  verdict.

Q-1 passe seulement si, pour les deux appels : HTTP 200 ; `response` non vide ;
`thinking` absent ou vide ; JSON strict ; validation par le modèle Pydantic
complet ; six critères dans l'ordre ; et toutes les références résolues. Un
échec produit `V9_ABORTED_BEFORE_Q0`, laisse H9 `UNTESTED` et interdit Q0,
calibration et tenu. Le pack Q-1 et son verrou sont distincts de Q0 ; aucune
donnée de campagne n'est importée par cette phase.

### Q0, Q1 et C0–C12

Si Q-1 passe, Q0 reste exactement la qualification V8 : trois paires
synthétiques (`SEMANTIC_DOMINANCE`, `STYLE_PARITY`,
`INJECTION_RESISTANCE`), deux orientations, deux juges, soit exactement 12
appels sans relance. Chaque juge doit produire le gagnant logique attendu ou
`TIE` dans les deux orientations et satisfaire le contrat intégral. Un échec
produit `V9_ABORTED_BEFORE_CALIBRATION` et laisse H9 `UNTESTED`.

Q1 et C0–C12 sont repris mot pour mot et avec les mêmes dénominateurs que V8 :

- Q1 : panel résolu sur au moins 50 % des comparaisons complètes de
  calibration ; gagnant non dépendant du dernier départage lexical ; même
  preset gagnant dans au moins deux des trois retraits de source ;
- C0 : manifeste scellé de 60 cas ;
- C1 : 60/60 préfixes COMMON T1 byte-identiques ;
- C2 : changement d'option T2 ou T3 sur au moins 90 % des cas complets ;
- C3 : panel résolu sur au moins 50 % des 60 cas ;
- C4 : stabilité de chaque juge d'au moins 75 % après inversion ;
- C5 : Wilson bas 95 % de `WR` strictement supérieur à 0,50 et
  `NA >= 0,10` ;
- C6 : échec ADAPTIVE `<= 0,10` et au plus 0,05 au-dessus de STATIC_BEST ;
- C7 : tokens médians T2–T3 ADAPTIVE `<= 1,10` fois STATIC_BEST et latence
  p95 `<= 1,25` fois ;
- C8 : timeouts/erreurs `<= 5 %` par branche et écart absolu `<= 2` points ;
- C9 : aveugle sans branche, proxys, knobs, options, producteur, chemin ou
  mapping ;
- C10 : exactement 30 ABBA et 30 BAAB par producteur, cinq appels producteur
  par cas complet ;
- C11 : 100 % des packs fermés, hachés avant appel, byte-déterministes,
  références résolues et inversion limitée aux labels/ordre ;
- C12 : au moins 95 % de réponses valides en un appel, par juge et producteur ;
  `INVALID` n'est ni réparé, ni relancé, ni retiré.

Les tables de caractéristiques opératoires de V8, notamment les nombres
minimaux W/L et la probabilité de franchir C3+C5, sont incorporées sans
changement et ne sont pas recalculées après observation.

## Verdict logic

Q-1, Q0 et Q1 sont des portes globales préalables. Leur échec laisse
`H9_UNTESTED_IN_V9`. Pour chaque producteur, l'ordre et la logique de V8 restent
inchangés :

- échec structurel C0/C1/C9/C10/C11/C12 : `H9_INCONCLUSIVE_FOR_MODEL` ;
- structure passée mais échec opérationnel C2/C6/C7/C8 :
  `H9_NOT_SUPPORTED_FOR_MODEL` ;
- structure et opération passées mais échec panel C3/C4 :
  `H9_INCONCLUSIVE_FOR_MODEL` ;
- toutes les portes, C5 comprise, passent : `H9_SUPPORTED_FOR_MODEL` ;
- toutes sauf C5 passent : `H9_NOT_SUPPORTED_FOR_MODEL`.

Globalement, au moins deux producteurs `SUPPORTED` donnent
`H9_SUPPORTED_IN_V9`, au moins deux `NOT_SUPPORTED` donnent
`H9_NOT_SUPPORTED_IN_V9`, et les autres combinaisons donnent
`H9_INCONCLUSIVE_IN_V9`.

## Scope

### Runtime et modèles

Le runtime reste Python 3.14.7, Pydantic 2.13.4 et Ollama 0.32.9. Les trois
producteurs et leurs digests restent ceux de V8. Le panel fixe reste :

- `qwen3.6:27b`, digest
  `a50eda8ed977ab48a12431878896b27ffd5cef552c17af3317d9623b939a7f1e` ;
- `glm-4.7-flash:latest`, digest
  `4475827791a269b02c8ec49b1c3bc1abb5846bacf3fae015b75d33986322d8f6`.

### Schéma de validation et schéma fil

Le modèle Pydantic `JudgeVerdict`, ses validateurs et son schéma complet
restent inchangés. Ce schéma complet demeure l'unique autorité pour accepter
un verdict.

Le schéma fil envoyé dans `format` est produit déterministement à partir du
schéma complet après injection de l'enum des segments du pack. La
transformation récursive retire **uniquement** les clés `minLength` et
`maxLength`, où qu'elles apparaissent. Elle ne retire ni `required`, ni
`additionalProperties`, ni enum, ni type, ni `minItems`/`maxItems`, ni aucun
autre mot-clé. Les tests doivent prouver que le diff exact entre les deux
schémas est cette seule suppression.

Une chaîne trop courte ou trop longue peut donc franchir la grammaire mais doit
échouer ensuite dans Pydantic et rester `INVALID`. Cette compatibilité ne
relaxe pas le contrat accepté.

### Canal de réponse

Tous les appels juges incluent `think=false`. Seul le champ API `response` est
passé à `validate_judgment`. Le champ `thinking` n'est jamais concaténé,
interprété ou réparé ; s'il est non vide, l'appel est `INVALID`. Ces règles
valent pour Q-1, Q0, calibration et tenu.

### Données et budget

Corpus, hash, seed, sélection, segmentation, calibration de 12 cas, tenu de 60
cas, trajectoires et ordre sont ceux de V8. Q-1 ajoute exactement deux appels
diagnostiques. Le plafond complet passe donc de 2 928 à 2 930 appels ; aucun
autre budget n'est modifié. Q-1 et Q0 ne lisent aucun contenu du corpus.

### Exécution

V9 est lancée au premier plan depuis la console de l'opérateur. Une commande
unique exécute Q-1 puis, seulement en cas de succès, Q0. Chaque phase possède
un verrou exclusif créé avant son premier appel. Fermer ou interrompre la
commande après la création d'un verrou invalide la phase ; aucune reprise ou
seconde tentative n'est autorisée sous ce gel.

## Anti-confirmation clause

Aucun échec, `TIE`, désaccord, instabilité, erreur, ordre défavorable ou
réponse grammaticale mais invalide selon Pydantic ne peut être retiré du
dénominateur applicable. Aucun prompt, fixture, seuil, schéma complet, enum,
ordre, modèle ou paramètre n'est ajusté après l'ouverture de Q-1.

Une correction après gel qui dépasse la suppression préinscrite de
`minLength`/`maxLength`, change le canal `response`, autorise une relance ou
touche Q-1/Q0/Q1/C0–C12 annule V9 et exige V10. Un résultat positif autorise
une ablation ou réplication, jamais un déploiement ni une revendication de
supériorité générale.

La continuation d'ingénierie de V8 reste valide : l'evidence pack et le
harnais peuvent être livrés comme briques si leurs tests d'intégrité,
d'isolation, de non-trivialité et de provenance passent, indépendamment du
verdict scientifique.
