# Revue bibliographique P7 après V11

**Date :** 2026-09-02
**Statut :** document de travail — revue de littérature ciblée, non normatif
**Mandat :** recherches indiquées au §10 du cadrage externe P6–P7 post-V11
**Hors mandat :** nouveaux seuils, gel d’instrument, ouverture du jeu tenu, autorisation de V12
**Méthode :** recherche web 2024–2026 + corpus fondateur 2015–2023 ; synthèse par axe, avec portée et limites
**Langue de travail :** français ; titres d’articles laissés en langue originale

Ce texte ne clôt rien. Il relie des résultats publiés aux défauts déjà observés en V11 (stabilité 54,8 %, κ = 0,288, plancher marginal 36,5 %, 53/144 arrêts producteur par limite de longueur, classement des victoires aligné sur les budgets). Il ne dérive aucun seuil.

---

## 0. Ce que la littérature permet de dire d’emblée

Trois constats sont suffisamment répliqués pour servir de cadre, pas de verdict local.

1. **Le juge LLM n’est pas un instrument neutre.** Position, verbosité, style/format, identité du modèle et auto-préférence sont documentés de façon indépendante (Zheng et al. 2023 ; Saito et al. 2023 ; Shi et al. 2024 ; Ye et al. 2024 ; Dubois et al. 2024).
2. **Le protocole de jugement change le biais mesuré.** Le pairwise est souvent plus discriminant mais plus vulnérable aux indices superficiels ; le pointwise est plus stable en position mais plus exposé au plafond et à la dérive d’échelle (Jeong et al. 2024/2025 ; Liusie et al. 2024 ; Wadhwa et al. 2025, arXiv:2504.14716).
3. **Corriger un biais isolément ne valide pas l’instrument.** Les protocoles qui *estiment* le biais (inversion + agrégation, régression longueur/style, PPI contre un ancrage humain) sont plus défendables que ceux qui le *masquent* (un seul ordre, un seul score, un seul juge).

Ces trois points recoupent D1–D3 du cadrage. Ils ne disent pas si l’instrument Lyra actuel est réparable.

---

## 1. Pairwise vs pointwise pour sorties longues et proches

### Résultats stables

- Les humains et les LLM sont en général **meilleurs en jugement relatif qu’en notation absolue** (Liusie et al. 2024 ; Zheng et al. 2023, MT-Bench / LLM-as-a-Judge). C’est l’argument principal pour le pairwise sur la question finale « adaptatif vs statique ».
- Le pairwise **amplifie les préférences superficielles** (verbosité, ton autoritaire, format) quand les deux sorties sont proches. Jeong, Park, Hong, Lee & Choo, *The Comparative Trap* (arXiv:2406.12319, BlackboxNLP 2025) : le pairwise est plus vulnérable que le pointwise sur des paires adversariales (LLMBar) ; le pointwise résiste mieux aux distracteurs.
- Wadhwa, Tripathi, Durrett & Niekum, *Pairwise or Pointwise?* (arXiv:2504.14716) : en présence de traits distracteurs, les préférences pairwise basculent dans ~35 % des cas contre ~9 % en notation absolue.
- Le pairwise introduit un **biais de position** que le pointwise évite par construction. Les juges pairwise entraînés restent inconsistants après mitigation (J1, Whitehouse et al. 2025, arXiv:2505.10320 : jusqu’à ~20 % d’incohérences d’ordre ; le pointwise formé sur supervision pairwise réduit les égalités artificielles).
- Coût : le pairwise double au moins le budget d’inférence s’il faut les deux ordres ; le listwise multiplie les permutations (Shi et al. 2024 ; Zhu et al. 2024, PORTIA).

### Hybrides pertinents pour Lyra

- **PRePair** (Jeong et al.) : raisonnement *pointwise* dans un cadre *pairwise*. Meilleur que le pairwise naïf sur LLMBar, meilleur que le pointwise pur sur MT-Bench.
- **J1 Pointwise** formé à partir de paires : cohérence de position par design, au prix d’une résolution plus floue entre candidats proches.
- **EvalPlanner** (Saha et al. 2025, arXiv:2501.18099) : plan d’évaluation puis exécution dans les deux ordres ; la consistance d’ordre est un critère d’inclusion des traces d’entraînement.

### Portée pour P7

Le comparatif reste l’estimand naturel de l’hypothèse adaptatif/statique. Le ponctuel sert le diagnostic (contraintes, correction, concision, couverture). Un hybride est **justifié comme atelier**, pas encore comme règle gelée : la littérature montre un gain de robustesse, pas une absence de flexibilité analytique. La flexibilité excessive apparaît si l’on choisit pairwise ou pointwise *après* avoir vu lequel favorise une politique.

---

## 2. Biais de position, verbosité, style, identité et auto-préférence

### Position

Shi, Ma, Liang, Diao, Ma & Vosoughi, *Judging the Judges* (arXiv:2406.07791) : cadre à trois métriques — stabilité de répétition, consistance de position, équité de préférence — sur 12–15 juges, MT-Bench et DevBench, >100k instances. Le biais de position n’est pas du bruit. Il varie selon le juge, la tâche et **l’écart de qualité entre candidats** : plus les sorties sont proches, plus la position pèse. La longueur du prompt n’est qu’un facteur faible.

Mitigations courantes :

- double appel avec inversion, victoire seulement si les deux ordres concordent (Zheng et al. 2023) ;
- batches position-agnostiques et récompense de consistance (J1) ;
- PORTIA : alignement qui imite la comparaison humaine pour recalibrer la position.

Limite : traiter les désaccords d’ordre comme TIE **conserve le sens** mais **abaisse la résolution**. V11 a déjà cette tension (40/73 résolues). Forcer une agrégation qui « fabrique » de la stabilité (vote majoritaire sans modèle de dépendance, ou moyenne de scores non comparables) est exactement ce que Shi et al. et les travaux d’agrégation dépendante (Ising, arXiv:2601.22336) déconseillent.

### Verbosité et longueur

- Saito, Wachi, Wataoka & Akimoto, *Verbosity Bias in Preference Labeling* (arXiv:2310.10076) : préférence pour le plus long même à qualité comparable, plus nette en écriture créative ; écart LLM/humain.
- Dubois et al., *Length-Controlled AlpacaEval* (arXiv:2404.04475) : un GLM qui conditionne la préférence sur la différence de longueur. La win-rate brute d’un même modèle passe de 22,9 % à 64,3 % selon la consigne de verbosité ; après contrôle, 41,9–51,6 %. Corrélation Spearman avec Chatbot Arena : 0,94 → 0,98.
- LMSYS / Arena *Style Control* (2024) puis *Sentiment Control* : même idée en Bradley–Terry, covariables = longueur, titres markdown, gras, listes, puis sentiment/emojis. Le coefficient de longueur domine (~0,25) ; le markdown est secondaire (0,02–0,06). Les classements changent.
- Ye et al. 2024, *Justice or Prejudice?* (arXiv:2410.02736, ICLR 2025) : 12 biais via le cadre CALM ; verbosité et style parmi les plus actionnables.
- Un papier 2026 de mitigation systématique (arXiv:2604.23178) nuance le dogme « plus long = mieux » : le biais de **style (markdown vs prose)** peut dominer la position (0,10–0,76 vs ≤0,04) ; la verbosité est **hétérogène selon le juge** (Llama/Gemini allongent, Claude Sonnet 4 penche vers la concision, GPT-4o quasi-neutre). Sur des paires de *troncature* (le plus long est réellement plus complet), tous les juges testés préfèrent la version complète (0,88–1,00). Donc : on ne peut pas confondre « filler » et « achèvement de contrat ».

C’est le point le plus proche de D2/D3 Lyra. Les 53/144 arrêts producteur au tour 3 par limite de longueur ne sont pas un biais de juge : ce sont des sorties **incomplètes**. Les préférer ou les pénaliser n’est pas le même estimand que « politique meilleure à contrat identique ».

### Auto-préférence et identité

- Wataoka, Takahashi & Ri, *Self-Preference Bias in LLM-as-a-Judge* (arXiv:2410.21819) : GPT-4 favorise les textes à faible perplexité, y compris non auto-générés. L’auto-préférence est en partie une **préférence de familiarité**.
- Chen et al., *Do LLM Evaluators Prefer Themselves for a Reason?* (arXiv:2504.03846) : une part de l’auto-préférence des modèles forts est légitime (ils sont objectivement meilleurs) ; la part *nuisible* (favoriser une réponse auto-générée objectivement fausse) reste sur les items où le générateur échoue.
- Yang et al. 2026, *Quantifying and Mitigating Self-Preference Bias* (arXiv:2604.22891) : paires de qualité égalisée pour séparer discriminabilité et biais ; capacités avancées ≠ faible SPB.
- Li et al., *Play Favorites* (arXiv:2508.06709) : self-bias et *family-bias* après contrôle par un juge tiers (humain).
- Conséquence opérationnelle répétée : ne pas faire juger un producteur par le même modèle ou la même famille sans le déclarer comme limite de portée.

Pour Lyra : si le juge et un producteur partagent famille ou contrat JSON, une partie du « signal » V11 (κ = 0,288, p = 0,0011 contre le hasard) peut être de la familiarité de format, pas de la qualité éditoriale.

---

## 3. Inversion, répétition, permutation, agrégation

Ce que la littérature distingue clairement :

| Protocole | Ce qu’il estime | Ce qu’il masque s’il est mal utilisé |
|---|---|---|
| Un seul ordre | un mélange position + contenu | tout |
| Deux ordres, TIE si désaccord | la préférence *stable à la position* | la puissance (plus de TIE) |
| Deux ordres + score continu / logprobs | un degré de préférence | une fausse précision si mal calibré |
| Répétition à T>0 | stabilité intra-juge | un accord artificiel à T=0 |
| Régression longueur/style (AlpacaEval-LC, Arena Style Control) | préférence à longueur/style fixés | l’effet réel de la longueur si la longueur *fait partie* de l’intervention |
| PPI / PPI++ / estimateurs à erreur de mesure | un paramètre humain avec surrogate LLM | rien si l’échantillon humain n’est pas ancré |
| Vote majoritaire de K juges LLM | un consensus de famille | la dépendance (données, prompts, modes de défaillance partagés) |

Dwork et al. 2015 (*Reusable holdout*, Science) et Angelopoulos et al. (PPI, Science 2023 ; PPI++ 2023) sont les outils statistiques adaptés quand on a un juge bruyant et peu d’ancrage humain. *Efficient Inference for Noisy LLM-as-a-Judge* (arXiv:2601.05420) montre que l’estimateur naïf de win-rate LLM est biaisé ; PPI++ calibré atteint la borne d’efficacité dans le cas binaire.

L’agrégation de juges LLM sans modèle de dépendance surestime la confiance (Ising / facteurs latents, arXiv:2601.22336). Un second juge automatique n’est pas un second humain.

**Règle de lecture pour V11 :** 54,8 % de stabilité après inversion n’est pas un échec du contenu seul. C’est la métrique que Shi et al. appellent *position consistency*. Le κ = 0,288 dit qu’il reste un signal après prise en compte des marginales. Ni l’un ni l’autre ne sépare encore longueur, position et politique.

---

## 4. Calibration d’un juge contre des humains

Points de consensus :

- L’accord brut est insuffisant. Cohen κ, Krippendorff α, Scott π restent le langage commun (Artstein & Poesio 2008 ; LREC 2026, *Counting on Consensus*).
- Un κ « bon » n’implique pas une bonne discrimination entre systèmes (Thakur et al., *Judging the Judges* arXiv:2406.12624) : des juges peu alignés mais à biais *stable* peuvent classer aussi bien que des juges « excellents » selon π.
- Les annotateurs humains ont une **erreur de mesure non nulle**. Abercrombie et al., *Consistency is Key* (arXiv:2301.10684, NLPerspectives 2025) : l’intra-annotateur est rarement rapporté ; sur quatre tâches NLP, ~25 % de réponses inconsistantes au re-test. L’inter-annotateur mélange désaccord légitime, ambiguïté de l’item et instabilité de l’opérateur.
- Un composite de plusieurs codeurs peut être fiable alors que chaque codeur est médiocre (exemple 2026 : 9 codeurs, α = 0,38 individuel, ICC(k=9) = 0,85). Cela plaide pour un panel même petit, pas pour un juge unique présenté comme « préférence humaine ».
- PPI et apparentés (PRECISE arXiv:2601.18777 ; multi-task PPI arXiv:2605.29249) : quelques centaines de labels humains + beaucoup de jugements LLM donnent des intervalles valides sur un estimand humain, à condition que le sous-échantillon humain ne soit pas choisi après coup sur les cas « intéressants ».

Pour Lyra : un seul chercheur-annotateur mesure la **répétabilité intra-opérateur**, pas une préférence humaine générale. C’est déjà ce que le cadrage affirme. La littérature le confirme et ajoute : sans second passage aveugle du même annotateur, on ne sait même pas si le plafond humain est au-dessus de 54,8 %.

---

## 5. Petit panel humain : plans réalistes

Ce qui existe à petite échelle, sans panel industriel :

1. **Double passage du même annotateur**, ordre re-randomisé, délai (Abercrombie et al.). Mesure intra-rater. Coût : 2× l’échantillon de développement.
2. **Échantillonnage actif contraint** pour le classement inter-systèmes, pas pour l’esthétique des items. *Better than Random: Constrained Active Sampling* (CASF, arXiv:2406.07967) : avec un budget limité, un échantillon naïf fausse le classement ; un contrôleur qui évite les grappes et la manipulation améliore la reconnaissance du meilleur système (~93 % dans leur méta-réévaluation NLG). Mise en garde 2026 : en détection d’hostilité, l’AL n’a **pas** battu le tirage aléatoire sous annotateur LLM ni humain (arXiv:2604.13899). L’AL n’est pas un réflexe.
3. **Allocation coût-optimale weak/strong rater** (arXiv:2506.07949) : PPI actif. Le juge LLM annote tout ; l’humain n’annote que là où le surrogate est incertain ou influent. Objectif : estimateur sans biais de la moyenne humaine sous budget.
4. **Adjudication sur désaccords seulement**, à condition que la règle de sélection soit fixée avant (sinon l’estimand se déplace vers les cas difficiles).
5. **Ancrage fixe** (30–50 items versionnés) rescoré à chaque changement de juge — pratique industrielle répétée (Arize 2026 ; Galileo 2026 ; Metacto 2026), pas une preuve scientifique de taille minimale universelle.

Aucune source ne donne « N humains = reproductibilité utile » comme constante. Les ordres de grandeur qui reviennent : dizaines d’items pour détecter un juge cassé ; centaines pour un κ avec intervalle utilisable ; milliers pour un classement de politiques. Un sous-ensemble commun à 2–3 annotateurs sur quelques dizaines d’items suffit à *estimer* un désaccord, pas à *certifier* une préférence.

---

## 6. Politiques adaptatives quand l’intervention change longueur ou coût

C’est le trou le plus important pour P7, et le plus proche de D3.

La littérature d’alignement (RLHF/RLAIF, AlpacaEval-LC, Arena Style Control, *From Lists to Emojis* arXiv:2409.11704) montre que :

- l’intervention (récompense, politique, budget de décodage) **déplace la longueur** ;
- le juge **récompense la longueur** ;
- le classement mesure alors un mélange « meilleure décision + plus de tokens ».

Les correctifs publiés sont des **contrôles statistiques a posteriori** (conditionner à Δlongueur = 0) ou des **contraintes a priori** (même budget de tokens, même contrat de sortie, pénalité de longueur dans la récompense). Aucun papier trouvé ne valide une politique adaptative *conversationnelle* à utilisateur unique en séparant proprement δr et qualité éditoriale.

Implication pour V12, sans seuil :

- si `δr` commande la longueur disponible, l’estimand « avantage robuste de l’adaptatif » n’est identifiable que si l’on fixe le contrat et le budget, **ou** si l’on estime un effet de longueur et qu’on le retire, **ou** si l’on redéfinit l’estimand comme « qualité sous budget libre » (autre hypothèse).
- Pénaliser les sorties tronquées sans égaliser le budget sélectionne la politique qui *finit le formulaire* — exactement D2.

---

## 7. Développement de l’évaluateur, test gelé, surveillance

La séparation demandée au cadrage (régimes A/B/C) a des analogues clairs, rarement tenus ensemble dans un même papier NLP.

- **Développement vs test :** Nosek et al., *The preregistration revolution* (PNAS 2018) ; Hofman et al., *Pre-registration for Predictive Modeling* (arXiv:2311.18807) : déclarer le gel *après* le tuning et *avant* le holdout. Le test set ne se visite pas pour choisir la règle.
- **Holdout réutilisable sous adaptativité :** Dwork, Feldman, Hardt, Pitassi, Reingold, Roth, *The reusable holdout* (Science 2015). On peut interroger plusieurs fois un holdout si l’accès est bruité / limité (inspiration differential privacy). Ce n’est pas « on relit les 60 cas ». C’est un protocole d’accès.
- **Surveillance post-déploiement :** *Who Drifted: the System or the Judge?* (arXiv:2606.15474) — ancrage humain fixe, e-process anytime-valid, verdict {none, system, judge}. Un z-test glissant faux-alarme ~75 % des flux sans dérive. C’est l’article le plus proche du régime C.
- Pratique industrielle convergente : épingler le snapshot du juge, rescorer un golden set à chaque bump de modèle, suivre κ dans le temps (Arize, Galileo, Metacto 2026).

L’erreur structurelle que le cadrage nomme — geler ensemble un instrument encore en développement et l’hypothèse — est exactement ce que ces sources appellent leakage / adaptive data analysis.

---

## 8. Validité d’un jeu tenu après plusieurs arrêts

Sources utiles, aucune n’est un blanc-seing.

- Thompson et al., *Dataset decay* (eLife 2020) : réutiliser le même jeu pour des tests successifs gonfle les faux positifs, même sans lire les labels, dès que les analyses sont guidées par des résultats voisins.
- Wagenmakers et al. 2012, repris par Thompson : une analyse n’est confirmatoire que si elle est préenregistrée **avant** toute information sur les données. Après publication ou usage voisin, le reste est exploratoire sauf nouvelle collecte ou holdout jamais touché *et* protocole d’accès contraint.
- Dwork et al. 2015 : le holdout reste informatif s’il n’est pas lu en clair et si le nombre d’adaptations est compté.
- Templates OSF de preregistration sur données secondaires : déclarer **toutes** les analyses antérieures sur matériau adjacent, variables déjà vues, arrêts antérieurs.

Application honnête au jeu tenu Lyra (60/60 intacts) :

- L’intégrité *physique* (jamais généré, jamais lu) est une condition nécessaire, pas suffisante.
- V3–V11 ont adapté l’instrument, les contrats, les portes et le juge sur du matériau **voisin**. C’est de l’analyse adaptative au sens de Dwork/Thompson.
- Un usage confirmatoire futur exige au minimum : (a) déclaration de dépendance aux choix antérieurs, (b) instrument figé *avant* ouverture, (c) une seule ouverture, (d) estimand qui n’a pas été tacitement ajusté pour « passer » sur la calibration. Même alors, la communauté méthodologique classerait plutôt cela comme **confirmation faible / quasi-holdout**, pas comme expérience indépendante.

La littérature ne dit pas « jeter les 60 cas ». Elle dit « ne pas les présenter comme une réplication indépendante ».

---

## 9. Shadow mode, interleaving, essais séquentiels à faible volume

Ce qui existe :

- **Shadow / dark launch** : la politique candidate reçoit le trafic réel, sa sortie n’est pas montrée, on journalise divergence, latence, coût, contrat. Standard MLOps (guides 2024–2026). Mesure ce que le modèle *ferait*, pas ce que l’utilisateur *préférerait*.
- **A/B / interleaving** : l’utilisateur voit une des politiques (ou des tours mélangés). Seul moyen de mesurer une préférence révélée. Exige un volume que Lyra n’a pas (un utilisateur principal).
- **Canary puis rampe** : après shadow, 5–25 % du trafic, rollback.
- **Auditions à vote nul** (llm-council, 2026) : la politique participe au jugement mais son poids de décision est 0 jusqu’à un quota de sessions.

Limites pour un utilisateur unique :

- pas de significativité fréquentiste classique à N faible ;
- l’utilisateur-constructeur **sait** quelle politique est en fantôme s’il lit les logs — le jugement humain quotidien n’est pas aveugle sauf protocole explicite (clé de politique cachée, comme le cadrage §7 le prévoit déjà) ;
- les essais séquentiels anytime-valid (e-process, arXiv:2606.15474) sont plus adaptés qu’un test t figé à N=60.

La promotion shadow → actif chez un utilisateur unique n’a pas de critère publié universel. Les sources industrielles parlent de « pas de régression sur contrat + ancrage humain stable + coût acceptable », ce qui est une politique de risque, pas une preuve d’hypothèse P7.

---

## 10. Gouvernance, consentement, confidentialité des corpus conversationnels

Consensus utile, même pour un usage d’abord local :

- Recueillir un corpus d’usage réel n’est pas anodin dès qu’un tiers (annotateur, auditeur, modèle externe) y accède. CANDOR (Science Advances) : consentement répété, risque d’identification, possibilité de retrait, revue humaine avant partage.
- DialogPII (2026) : la rareté des corpus conversationnels publics vient précisément du coût éthique (approbation, consentement, PII). Les jeux synthétiques aident l’outillage d’anonymisation, ils ne remplacent pas le consentement du locuteur réel.
- CompanionHarm (arXiv:2608.25377) : désaccord annotateur élevé sur les tours contextuels ; les labels individuels doivent être conservés, pas seulement le vote majoritaire.
- GDPR / AI Act : finalité déterminée, minimisation, base légale, droit de retrait, pas de réutilisation opportuniste comme benchmark si le consentement portait sur « améliorer mon assistant ».
- *Consent in Crisis* (Data Provenance Initiative) : même le web « public » n’est plus un commun par défaut.

Pour P6 local : journal forensique séparant entrée, config, sorties, tokens, retour humain — déjà prévu au cadrage — est aligné. Devenir un benchmark P7 exige une **règle explicite de transformation** (développement / surveillance / tenu) et, si un second humain entre, un consentement distinct. Sinon la collecte quotidienne est de l’optimisation sur les préférences du constructeur, précisément la question 9 de l’auditeur.

---

## 11. Lecture des questions d’auditeur (§11) à la lumière des sources

Réponses de littérature, pas de décision locale.

1. **Estimand qualité / longueur / coût / préférence personnelle.** Oui, il doit être factorisé. AlpacaEval-LC et Arena Style Control montrent que « mieux » sans covariable de longueur n’est pas identifiable. Le cadrage a déjà le bon découpage ; il manque l’écriture formelle de l’estimand (ex. préférence à contrat satisfait et à Δtokens dans une bande, vs préférence brute).
2. **Hybride ponctuel/comparatif.** Justifié comme *atelier de diagnostic + verdict comparatif aveugle*, à condition que le choix de la règle de verdict soit antérieur au jeu tenu. Sinon c’est de la flexibilité analytique (Jeong ; Wadhwa).
3. **Quantité minimale d’annotation humaine commune.** Pas de N magique. Plan minimal défendable dans la littérature : intra-rater sur échantillon stratifié de développement + éventuellement 2e annotateur sur un sous-ensemble. Dizaines d’items pour auditer le juge ; pas assez pour une « préférence humaine » générale.
4. **Sorties non conformes vs budget.** Les traiter comme échec de contrat *après* avoir égalisé le budget. Sinon on sélectionne la politique qui tient dans l’enveloppe. Les paires troncature vs expansion (arXiv:2604.23178) montrent que les juges savent récompenser la complétude réelle ; encore faut-il que chaque politique *puisse* être complète.
5. **Correction de position.** Inversion + TIE si désaccord estime la consistance ; c’est la pratique la plus défendable. Les agrégations qui reconstruisent un vainqueur à tout prix fabriquent de la stabilité (Shi et al.).
6. **Séparer δr et préférence pour la longueur.** Trois leviers publiés : égaliser le budget ; contrôler statistiquement Δlongueur ; redéfinir l’estimand. Les trois doivent être choisis avant le tenu. Aucun papier ne les applique à un `δr` conversationnel.
7. **Jeu tenu historique.** Utilisable comme confirmation faible si dépendance déclarée, instrument figé, une seule ouverture. Pas comme réplication indépendante (Thompson 2020 ; Dwork 2015).
8. **Promotion fantôme → actif, utilisateur unique.** Critère de risque opérationnel (contrat, ancrage, coût), distinct du test d’hypothèse P7. Shadow d’abord. Pas de N publié.
9. **Empêcher l’optimisation opportuniste P6.** Règles de régime A/B/C, clé de politique cachée au jugement, transformation explicite interaction → cas, pas de retuning du juge sur le flux quotidien sans versionnage. Analogues : golden set d’ancrage, preregistration for predictive modeling.

---

## 12. Ce que la littérature ne tranche pas

- Un seuil de stabilité (75 % ou autre) pour un juge unique local.
- La taille du panel humain « suffisante » pour Lyra.
- La légitimité scientifique d’ouvrir les 60 cas après V11.
- L’existence d’un avantage adaptatif une fois longueur et contrat égalisés — **non testé ici, non testé ailleurs dans un design comparable**.
- Le juge Qwen / contrat JSON comme instrument spécifique.

Toute transposition chiffrée de ces papiers vers V12 serait une nouvelle hypothèse, donc une préinscription distincte.

---

## 13. Corpus prioritaire (lecture directe)

Ordre suggéré, du plus actionnable au plus méthodologique.

1. Zheng et al. 2023 — MT-Bench / LLM-as-a-Judge (position, swap).
2. Shi et al. 2024 — *Judging the Judges*, arXiv:2406.07791.
3. Jeong et al. 2024/25 — *The Comparative Trap*, arXiv:2406.12319.
4. Dubois et al. 2024 — *Length-Controlled AlpacaEval*, arXiv:2404.04475.
5. LMSYS Arena Style Control (blog + régression BT).
6. Saito et al. 2023 — verbosity bias, arXiv:2310.10076.
7. Ye et al. 2024 — *Justice or Prejudice?*, arXiv:2410.02736.
8. Wataoka et al. 2024 — self-preference / perplexité, arXiv:2410.21819.
9. Abercrombie et al. 2025 — intra-annotateur, arXiv:2301.10684.
10. Angelopoulos et al. 2023 — Prediction-Powered Inference.
11. Dwork et al. 2015 — reusable holdout.
12. Thompson et al. 2020 — dataset decay, eLife.
13. Nosek et al. 2018 — preregistration revolution.
14. Li 2026 — *Who Drifted: the System or the Judge?*, arXiv:2606.15474.
15. Wadhwa et al. 2025 — pairwise vs pointwise distractors, arXiv:2504.14716.

---

## 14. Limites de cette revue

- Revue par axes, non exhaustive. Les surveys 2026 (Li et al. *From Generation to Judgment* arXiv:2411.16594 ; *Large language models as judges*, Artif. Intell. Review 2026) couvrent plus large.
- Plusieurs résultats 2026 n’ont pas encore de version venue ; traités comme prépublications.
- Aucun article lu en PDF intégral page à page dans cette session ; synthèse sur résumés, HTML arXiv et extraits. Un auditeur qui doit citer un chiffre précis (35 %, 0,98, 25 % d’intra-inconsistance) devrait vérifier dans le PDF.
- Les sources internes Lyra listées au cadrage (`P7_V11_STATUS.md`, etc.) sont
  présentes dans ce dépôt. Les chiffres V11 repris ici n'ont toutefois pas été
  recalculés pendant cette revue bibliographique.

---

*Fin de revue. Toute hypothèse ou tout seuil issu de cette discussion doit vivre dans une préinscription distincte, gelée avant la mesure correspondante.*
