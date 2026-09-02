# Sources ouvrables — dossier de travail P7 post-V11

**Date :** 2026-09-02
**Rôle :** centraliser les *sources primaires* citées dans `REVUE_BIBLIO_P7_POST_V11.md`, avec un lien officiel ouvrable.
**Ce que ce dossier n’est pas :** une bibliographie gelée pour V12, une validation des chiffres extraits dans la revue, un substitut à la lecture des PDF.

## Comment lire ce fichier

- **A — à ouvrir avant tout usage normatif.** Ce sont les articles dont un chiffre ou un protocole a été invoqué dans la revue.
- **B — contexte et extensions.** Utile pour l’atelier, pas requis pour vérifier une affirmation déjà faite.
- **C — méthode / gouvernance.** Holdout adaptatif, préinscription, consentement.
- **D — notes industrielles et blogs.** Non peer-reviewed ; ne pas geler dessus.
- **Paywall.** Lien officiel quand même ; alternative ouverte indiquée si elle existe.

Colonne **PDF local** : fichier téléchargé dans `pdfs/` quand le document est ouvert (arXiv, ACL, eLife, MIT Press OA, PMC).
Les blogs et les articles Science/PNAS payants n’ont pas de PDF local.

## Attribution et redistribution

Les tableaux ci-dessous conservent, pour chaque source, les auteurs disponibles,
le titre et le lien officiel. Les métadonnées de la page officielle prévalent si
une citation formelle est nécessaire.

Les PDF placés dans `docs/pdfs/` constituent un **cache local de lecture**. Ils
sont ignorés par Git et ne sont pas redistribués avec le projet. Un document
librement téléchargeable n'est pas nécessairement placé sous une licence qui
autorise un tiers à en republier une copie ; l'attribution ne remplace pas cette
autorisation. Les liens officiels restent donc la voie de diffusion canonique.

Statut de lecture dans *cette* session : **non lu en intégral**. La revue s’appuie sur résumés, HTML arXiv et extraits. Toute affirmation chiffrée doit être recollée au PDF avant de devenir normative.

Les sources internes Lyra (`docs/P7_V11_STATUS.md`, `PREREGISTRATION_v11.md`,
etc.) vivent dans ce dépôt. Elles documentent l'état local du programme, mais
ne remplacent pas les publications externes citées ici.

---

## A — Corpus prioritaire (vérifier avant tout usage normatif)

| # | Source | Année | Lien abs / page | PDF officiel | PDF local | Pourquoi elle est ici |
|---|---|---:|---|---|---|---|
| A1 | Zheng, Chiang, Sheng et al. *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* | 2023 | https://arxiv.org/abs/2306.05685 | https://arxiv.org/pdf/2306.05685 | `pdfs/A1_Zheng_MTBench_2306.05685.pdf` | Protocole fondateur : pairwise, swap d’ordre, position, verbosité, self-enhancement |
| A2 | Shi, Ma, Liang, Diao, Ma, Vosoughi. *Judging the Judges: A Systematic Investigation of Position Bias…* | 2024 | https://arxiv.org/abs/2406.07791 | https://arxiv.org/pdf/2406.07791 | `pdfs/A2_Shi_PositionBias_2406.07791.pdf` | Stabilité de répétition, consistance de position, équité ; biais plus fort quand les candidats sont proches |
| A3 | Jeong, Park, Hong, Lee, Choo. *The Comparative Trap: Pairwise Comparisons Amplifies Biased Preferences…* | 2024–25 | https://arxiv.org/abs/2406.12319 | https://arxiv.org/pdf/2406.12319 | `pdfs/A3_Jeong_ComparativeTrap_2406.12319.pdf` | Pairwise vs pointwise ; PRePair ; vulnérabilité adversariale (LLMBar) |
| A3b | Version venue ACL/BlackboxNLP | 2025 | https://aclanthology.org/2025.blackboxnlp-1.5/ | https://aclanthology.org/2025.blackboxnlp-1.5.pdf | — | Même article, pagination venue. Préférer celle-ci pour citer. |
| A4 | Wadhwa, Tripathi, Durrett, Niekum. *Pairwise or Pointwise? Evaluating Feedback Protocols for Bias…* | 2025 | https://arxiv.org/abs/2504.14716 | https://arxiv.org/pdf/2504.14716 | `pdfs/A4_Wadhwa_PairwiseOrPointwise_2504.14716.pdf` | Distracteurs : ~35 % de bascules pairwise vs ~9 % pointwise — **à revérifier dans le PDF** |
| A5 | Dubois, Galambosi, Liang, Hashimoto. *Length-Controlled AlpacaEval…* | 2024 | https://arxiv.org/abs/2404.04475 | https://arxiv.org/pdf/2404.04475 | `pdfs/A5_Dubois_LengthControlledAlpacaEval_2404.04475.pdf` | GLM longueur ; gameability 22,9–64,3 % vs 41,9–51,6 % ; Spearman 0,94→0,98 — **à revérifier** |
| A6 | Saito, Wachi, Wataoka, Akimoto. *Verbosity Bias in Preference Labeling by Large Language Models* | 2023 | https://arxiv.org/abs/2310.10076 | https://arxiv.org/pdf/2310.10076 | `pdfs/A6_Saito_VerbosityBias_2310.10076.pdf` | Définition opérationnelle de la verbosité LLM vs humain |
| A7 | Ye, Wang, Huang et al. *Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge* | 2024 | https://arxiv.org/abs/2410.02736 | https://arxiv.org/pdf/2410.02736 | `pdfs/A7_Ye_JusticeOrPrejudice_2410.02736.pdf` | 12 biais, cadre CALM. Site : https://llm-judge-bias.github.io/ |
| A8 | Wataoka, Takahashi, Ri. *Self-Preference Bias in LLM-as-a-Judge* | 2024 | https://arxiv.org/abs/2410.21819 | https://arxiv.org/pdf/2410.21819 | `pdfs/A8_Wataoka_SelfPreference_2410.21819.pdf` | Auto-préférence liée à la perplexité / familiarité |
| A9 | Chen et al. *Do LLM Evaluators Prefer Themselves for a Reason?* | 2025 | https://arxiv.org/abs/2504.03846 | https://arxiv.org/pdf/2504.03846 | `pdfs/A9_Chen_PreferThemselves_2504.03846.pdf` | Part légitime vs part nuisible de l’auto-préférence |
| A10 | Abercrombie, Dinkar, Cercas Curry, Rieser, Hovy. *Consistency is Key… Intra-Annotator Agreement* | 2023–25 | https://arxiv.org/abs/2301.10684 | https://arxiv.org/pdf/2301.10684 | `pdfs/A10_Abercrombie_IntraAnnotator_2301.10684.pdf` | Intra-rater rarement rapporté ; ~25 % d’inconsistance — **à revérifier** |
| A10b | Version venue NLPerspectives | 2025 | https://aclanthology.org/2025.nlperspectives-1.6/ | https://aclanthology.org/2025.nlperspectives-1.6.pdf | — | Pagination venue |
| A11 | Angelopoulos, Bates, Fannjiang, Jordan, Zrnic. *Prediction-Powered Inference* | 2023 | https://arxiv.org/abs/2301.09633 | https://arxiv.org/pdf/2301.09633 | `pdfs/A11_Angelopoulos_PPI_2301.09633.pdf` | Cadre statistique labels chers + surrogate abondant. Version Science : doi:10.1126/science.adi6000 |
| A12 | Angelopoulos, Duchi, Zrnic. *PPI++: Efficient Prediction-Powered Inference* | 2023 | https://arxiv.org/abs/2311.01453 | https://arxiv.org/pdf/2311.01453 | `pdfs/A12_Angelopoulos_PPIpp_2311.01453.pdf` | Version efficace / calibrée de PPI |
| A13 | *Efficient Inference for Noisy LLM-as-a-Judge Evaluation* | 2026 | https://arxiv.org/abs/2601.05420 | https://arxiv.org/pdf/2601.05420 | `pdfs/A13_NoisyJudge_2601.05420.pdf` | Estimateur naïf de win-rate biaisé ; PPI++ vs EIF |
| A14 | Li, Yitao. *Who Drifted: the System or the Judge?* | 2026 | https://arxiv.org/abs/2606.15474 | https://arxiv.org/pdf/2606.15474 | `pdfs/A14_Li_WhoDrifted_2606.15474.pdf` | Ancrage humain, e-process, verdict {none, system, judge} |
| A15 | Dwork, Feldman, Hardt, Pitassi, Reingold, Roth. *Preserving Statistical Validity in Adaptive Data Analysis* | 2014–16 | https://arxiv.org/abs/1411.2664 | https://arxiv.org/pdf/1411.2664 | `pdfs/A15_Dwork_AdaptiveDataAnalysis_1411.2664.pdf` | Version ouverte du *reusable holdout*. Article Science 2015 : doi:10.1126/science.aaa9375 (payant) |
| A16 | Thompson, Wrightson, Sainsbury, Poldrack. *Dataset decay and the problem of sequential analyses on open datasets* | 2020 | https://elifesciences.org/articles/53498 | HTML OA ; PDF eLife/PMC bloqué ici (406/403) | — ouvrir dans le navigateur | Faux positifs par réusage séquentiel même sans relire les labels |
| A17 | Nosek, Ebersole, DeHaven, Mellor. *The preregistration revolution* | 2018 | https://www.pnas.org/doi/10.1073/pnas.1708274114 | Préprint OSF : https://osf.io/2dxu5 | `pdfs/A17_Nosek_PreregistrationRevolution_OSF.pdf` | Prédiction vs postdiction ; holdout scellé. Version venue PNAS/PMC si besoin de pagination |
| A18 | Liusie, Manakul, Gales. *LLM Comparative Assessment…* | 2023 | https://arxiv.org/abs/2307.07889 | https://arxiv.org/pdf/2307.07889 | `pdfs/A18_Liusie_ComparativeAssessment_2307.07889.pdf` | Comparatif vs score absolu ; biais de position déjà mesuré |

---

## B — Extensions utiles à l’atelier (non requises pour geler)

| # | Source | Lien abs | PDF | PDF local | Note |
|---|---|---|---|---|---|
| B1 | Whitehouse et al. *J1: Incentivizing Thinking in LLM-as-a-Judge via RL* (2025) | https://arxiv.org/abs/2505.10320 | https://arxiv.org/pdf/2505.10320 | `pdfs/B1_J1_2505.10320.pdf` | Pairwise-J1 vs Pointwise-J1 ; récompense de consistance |
| B2 | Saha et al. *EvalPlanner* (2025) | https://arxiv.org/abs/2501.18099 | https://arxiv.org/pdf/2501.18099 | `pdfs/B2_EvalPlanner_2501.18099.pdf` | Plan + exécution dans les deux ordres |
| B3 | Li et al. *From Generation to Judgment* — survey (2024) | https://arxiv.org/abs/2411.16594 | https://arxiv.org/pdf/2411.16594 | `pdfs/B3_Survey_FromGenerationToJudgment_2411.16594.pdf` | Taxonomie pairwise / pointwise / listwise ; mitigations |
| B4 | Thakur et al. *Judging the Judges: Evaluating Alignment and Vulnerabilities…* | https://arxiv.org/abs/2406.12624 | https://arxiv.org/pdf/2406.12624 | `pdfs/B4_Thakur_Alignment_2406.12624.pdf` | Alignement humain ≠ pouvoir discriminant |
| B5 | Yang et al. *Quantifying and Mitigating Self-Preference Bias of LLM Judges* (2026) | https://arxiv.org/abs/2604.22891 | https://arxiv.org/pdf/2604.22891 | `pdfs/B5_Yang_SPB_2604.22891.pdf` | Paires de qualité égalisée |
| B6 | Ghiglia et al. *Play Favorites: A Statistical Method to Measure Self-Bias…* (2025) | https://arxiv.org/abs/2508.06709 | https://arxiv.org/pdf/2508.06709 | `pdfs/B6_PlayFavorites_2508.06709.pdf` | Self-bias et family-bias après juge tiers |
| B7 | *Judging the Judges: A Systematic Evaluation of Bias Mitigation Strategies…* (2026) | https://arxiv.org/abs/2604.23178 | https://arxiv.org/pdf/2604.23178 | `pdfs/B7_BiasMitigation_2604.23178.pdf` | Style vs position vs verbosité hétérogène selon le juge |
| B8 | Zhang / Park et al. *From Lists to Emojis: How Format Bias Affects Model Alignment* | https://arxiv.org/abs/2409.11704 | https://arxiv.org/pdf/2409.11704 | `pdfs/B8_FormatBias_2409.11704.pdf` | Format au-delà de la longueur |
| B9 | Zhou et al. *Better than Random: Constrained Active Sampling (CASF)* | https://arxiv.org/abs/2406.07967 | https://arxiv.org/pdf/2406.07967 | `pdfs/B9_CASF_2406.07967.pdf` | Échantillonnage humain pour classer des systèmes NLG |
| B10 | *Cost-aware active combination of weak and strong raters* (2025) | https://arxiv.org/abs/2506.07949 | https://arxiv.org/pdf/2506.07949 | `pdfs/B10_CostAwareRaters_2506.07949.pdf` | Allocation budget humain / autorater (PPI actif) |
| B11 | Hofman et al. *Pre-registration for Predictive Modeling* | https://arxiv.org/abs/2311.18807 | https://arxiv.org/pdf/2311.18807 | `pdfs/B11_Hofman_PreregPredictive_2311.18807.pdf` | Gel après tuning, avant holdout |
| B12 | Liusie et al. *Efficient LLM Comparative Assessment: Product of Experts* | https://arxiv.org/abs/2405.05894 | https://arxiv.org/pdf/2405.05894 | `pdfs/B12_Liusie_PoE_2405.05894.pdf` | Sous-échantillonnage de paires |
| B13 | *Dependence-Aware Label Aggregation for LLM-as-a-Judge via Ising Models* | https://arxiv.org/abs/2601.22336 | https://arxiv.org/pdf/2601.22336 | `pdfs/B13_IsingAggregation_2601.22336.pdf` | Juges LLM non indépendants |
| B14 | Artstein & Poesio. *Inter-Coder Agreement for Computational Linguistics* | https://doi.org/10.1162/coli.07-034-R2 | https://direct.mit.edu/coli/article/34/4/555/1999/Inter-Coder-Agreement-for-Computational | — 403 ici ; OA MIT Press dans le navigateur | κ, π, α — hypothèses |
| B15 | *Hidden Measurement Error in LLM Pipelines…* (2026) | https://arxiv.org/abs/2604.11581 | https://arxiv.org/pdf/2604.11581 | `pdfs/B15_HiddenMeasurementError_2604.11581.pdf` | Variance de pipeline vs vérité humaine |
| B16 | PRECISE — PPI pour métriques de ranking (2026) | https://arxiv.org/abs/2601.18777 | https://arxiv.org/pdf/2601.18777 | `pdfs/B16_PRECISE_2601.18777.pdf` | PPI étendu au ranking |

---

## C — Gouvernance, holdout, consentement

| # | Source | Lien | PDF ouvert | PDF local | Note |
|---|---|---|---|---|---|
| C1 | Thompson et al. 2020 — déjà A16 | https://elifesciences.org/articles/53498 | oui | voir A16 | Réusage séquentiel |
| C2 | Dwork et al. — déjà A15 | https://arxiv.org/abs/1411.2664 | oui | voir A15 | Holdout réutilisable sous accès contraint |
| C3 | Nosek et al. 2018 — déjà A17 | https://pmc.ncbi.nlm.nih.gov/articles/PMC5856500/ | oui | voir A17 | Préinscription |
| C4 | Wagenmakers, Wetzels, Borsboom, van der Maas, Kievit. *Why psychologists must change the way they analyze their data…* (2011/12) | https://doi.org/10.1177/1745691611406923 | souvent payant | — | Définition stricte du confirmatoire. Cité par Thompson |
| C5 | Reece et al. *The CANDOR corpus* | https://www.science.org/doi/10.1126/sciadv.adf3197 | PDF OA : https://www.science.org/doi/pdf/10.1126/sciadv.adf3197 | — 403 ici ; ouvrir dans le navigateur | Consentement conversationnel enregistré |
| C6 | *CompanionHarm* (2026) | https://arxiv.org/abs/2608.25377 | https://arxiv.org/pdf/2608.25377 | `pdfs/C6_CompanionHarm_2608.25377.pdf` | Désaccord annotateur sur conversations réelles |
| C7 | *DialogPII* (2026) | https://arxiv.org/abs/2606.30312 | https://arxiv.org/pdf/2606.30312 | `pdfs/C7_DialogPII_2606.30312.pdf` | Pourquoi les corpus conversationnels réels sont rares |
| C8 | Longpre et al. *Consent in Crisis* — Data Provenance Initiative | https://arxiv.org/abs/2407.14933 | https://arxiv.org/pdf/2407.14933 | `pdfs/C8_ConsentInCrisis_2407.14933.pdf` | Consentement des sources web (contexte, pas un mode d’emploi P6) |

---

## D — Notes industrielles et blogs (non gelables)

À conserver pour le régime C (surveillance), pas pour une préinscription.

| # | Source | Lien | Nature |
|---|---|---|---|
| D1 | LMSYS / LMArena. *Style Control* | https://arena.ai/blog/style-control | Blog + méthode BT. Données/colab mentionnés dans le billet |
| D2 | LMSYS / LMArena. *Sentiment Control* | https://arena.ai/blog/sentiment-control | Extension style (emoji, sentiment) |
| D3 | AlpacaEval dépôt | https://github.com/tatsu-lab/alpaca_eval | Code de A5 |
| D4 | Arize. *How to build LLM-as-a-Judge evaluators that hold up in production* (2026) | https://arize.com/blog/how-to-build-llm-as-a-judge-evaluators-that-hold-up-in-production/ | Golden set, drift |
| D5 | Galileo. *How to Calibrate Your LLM Judge With Human Annotations* (2026) | https://galileo.ai/blog/calibrate-llm-judge-human-annotations | κ dans le temps |
| D6 | Metacto. *LLM-as-Judge: When It Works, When It Breaks* (2026) | https://www.metacto.com/blogs/llm-as-judge-production-evaluation | Pinning de snapshot |
| D7 | Shadow traffic / A-B LLM (exemple vendor) | https://www.codeant.ai/blogs/shadow-traffic-llm-testing | Shadow ≠ préférence révélée |

---

## Ordre de lecture minimal pour vérifier la revue

Si le temps est compté, ouvrir dans cet ordre et annoter « chiffre confirmé / chiffre inexact / hors portée Lyra » :

1. A1 Zheng — le protocole d’inversion
2. A2 Shi — ce que mesure vraiment une stabilité à 54,8 %
3. A5 Dubois — comment on retire la longueur sans changer l’estimand
4. A3 + A4 Jeong / Wadhwa — pairwise vs pointwise
5. A6 Saito + B7 — verbosité n’est pas un scalaire unique
6. A8 + A9 — auto-préférence
7. A10 Abercrombie — intra-annotateur
8. A11 + A13 — PPI plutôt que κ seul comme estimand
9. A15 + A16 + A17 — jeu tenu après analyses voisines
10. A14 Li — régime C, ancrage vs dérive du juge

---

## Fichiers de travail

```
docs/
  00_SOURCES_OUVRABLES.md       ← ce fichier, versionné
  REVUE_BIBLIO_P7_POST_V11.md   ← revue narrative, versionnée
  pdfs/                         ← cache local de lecture, ignoré par Git
```

---

*Aucune de ces sources n’autorise V12. Un chiffre de la revue qui ne se retrouve pas dans le PDF correspondant doit être retiré avant tout usage normatif.*
