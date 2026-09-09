# Vocabulaire canonique de Lyra

Source unique des **définitions et décisions de sens**, pour arrêter la dérive
constatée d'un dossier à l'autre dans les archives. Toute brique se réfère à ces
définitions. La disponibilité, l'intégration et les preuves de maturité relèvent
de [ETAT_ACTUEL](../docs/ETAT_ACTUEL.md) ; les intentions et leurs prochains
jalons restent traçables dans le [registre](../docs/REGISTRE_INTENTIONS.md).

**Correspondances relues le 9 septembre 2026**, sur le code issu de `15bcede4`.
La colonne de code identifie une réalisation ou un écart ; elle n'annonce pas
l'admission en usage de tout le concept.

| Terme | Définition retenue | Correspondance dans le code ou horizon | Origine (audit) |
|---|---|---|---|
| **ρ (rho)** | structure / diversité contrôlée → `top_p` | `core/knobs.py` | né comme coeff. de couplage d'EDO (`lyra_project`) |
| **δr (delta_r)** | dilatation du contexte / longueur → `num_predict` | `core/knobs.py` | famille Uni |
| **τc (tau_c)** | tension → `temperature` ; mesurable comme divergence d'embeddings | `core/knobs.py` | `LyrAgent`, `conscious` |
| **κ (kappa)** | courbure/style, anti-répétition → `repeat_penalty` | `core/knobs.py` | `Topologie`/`Lyra_Core` |
| **Φ(t)** | Φ(t) := M[Σ(S(t))] — agrégat d'état, critère d'émergence stabilisée | Horizon P2 ; `CognitiveState` n'est pas identifié comme une implémentation de cette formule | `lyra_project`, .txt formel |
| **phase λ** | régime cognitif détecté + garde à hystérésis (cooldown) | `PolicyLambda` dans `core/control/phase.py` : seuil de cohérence, boost de τc et cooldown ; appelée par l'autopilote synthétique de `core/loop.py`, pas par le dialogue P6 | spec dans `Archi/phase_lambda.md` |
| **nemeton** | graphe sémantique de concepts/états | `GraphStore` dans `memory/graph/store.py` et injecteur borné `memory/graph/injector.py` ; nœuds et arêtes typés, deltas, rollback et compaction ; portée précisée ci-dessous | famille Uni, `Lyra_Core` |
| **ispace** | espace navigable d'états + réglages associés (CBR) | `Memento`, `Navigator` et `Suggestion` dans `memory/cbr/memento.py` ; cas sur features d'état et quatre stratégies de cibles ; projection des réglages maintenue dans `core/knobs.py` | `IspaceNav.zip` |
| **modules A/M/P/G/X/R** | ontologie de modules cognitifs typés | Horizon de représentation des modules ; les types de nœuds `GraphStore` ne suffisent pas à réaliser cette ontologie | manifeste, `Archi/kit_lyra` |
| **SilenceØ** | le refus/silence comme réponse de première classe | Horizon P5 ; une erreur technique, une chaîne vide ou une absence de génération n'est pas cette décision d'abstention | `LyrAgent` |

## Frontières de sens et de réalisation — 9 septembre 2026

- **Boutons et concepts.** Le mapping de `core/knobs.py` réalise ρ → `top_p`,
  δr → `num_predict`, τc → `temperature`, κ → `repeat_penalty`. `num_predict`
  borne la sortie ; ce mapping n'est pas à lui seul une gestion du contexte
  d'entrée. L'intention de « dilatation du contexte » demeure plus large.
  Le κ de réglage n'est pas une mesure de courbure d'Ollivier.
- **État et proxies.** `EpistemicBridge` dérive cohérence, fit et tension depuis
  des heuristiques textuelles. Son `pressure` est
  `len(core.metrics.cheap.tokens(output)) / num_predict`, borné dans [0,1] :
  `tokens()` découpe lexicalement le texte par expression régulière. Ce n'est
  pas le compte de tokens du moteur. La divergence d'embeddings reste un sens
  historique de τc, pas le calcul actuel de `tension`. La décision de juillet
  ci-dessous est conservée avec cette précision de correspondance.
- **Nemeton.** `GraphStore` est un graphe non orienté à données de nœuds/arêtes.
  Son champ libre `Node.data` ne constitue pas un magasin vectoriel ni un index
  ANN. `is_novel_link` observe une absence d'arête et de voisin commun ; le nom
  ne prouve pas la nouveauté sémantique. La [note Jachère](../docs/NOTE_ARCHITECTURE_JACHERE_CLOISONNEMENT_2026-09-07.md)
  définit l'horizon de mémoire dérivée, avec filiation, corrections et retrait.
- **ispace.** `Memento.retrieve` compare par cosinus des features telles que
  coherence/fit/pressure/tension/δr/τc ; `Navigator.suggest` propose des cibles
  avec `stabilize`, `explore`, `case_guided` ou `balanced`. Ces primitives ne
  constituent pas une navigation sémantique complète ni une API `/ispace/suggest`
  exposée dans le dialogue actuel. Le parcours historique `LyraConversation`
  les instancie ; `DialogueConversation`, profil P6 de référence, ne les appelle pas.
- **Deux pouponnières.** `Strate.POUPONNIERE` dans `MemoryEcology` classe des
  items mémoriels. La **Pouponnière évolutive** désigne la génération/évaluation/
  sélection de modules de scaffold. L'existence de la première ne livre pas la
  seconde. Oubli différé et compost réveillable ne suppriment pas le journal source.
- **Songe et Jachère.** Le Songe conserve consolidation et recombinaison ; la
  Jachère réunit le travail hors tâche sur mémoire et modules. Selon la note du
  7 septembre, chaque fonction peut réussir, s'abstenir ou échouer séparément ;
  leurs ponts sont facultatifs. Les traces résiduelles sont une intention
  distincte, à stockage séparé et influence conditionnelle. Le palier
  paramétrique reste un horizon d'entraînement local ; un contexte recomposé
  n'est pas une modification des poids.

Les correspondances ont été lues dans le code et les tests existants
[`test_cbr.py`](../tests/test_cbr.py), [`test_graph_store.py`](../tests/test_graph_store.py)
et [`test_phase.py`](../tests/test_phase.py). Cette relecture documentaire n'est
pas un nouveau résultat d'exécution ; les preuves datées restent dans ETAT_ACTUEL.

## Décisions datées

- **2026-07-18 — Réalignement des overrides** : les task overrides sont des
  masques transitoires de projection ; la modulation porte sur l'état de base.
- **2026-07-18 — Pont P2 v1 (signaux épistémiques réels)** : `coherence` =
  structure + anti-emballement ; `fit` = recouvrement prompt↔sortie (pénalisé si
  troncature) ; `pressure` = utilisation du budget de génération (tokens
  produits / num_predict — le signal que δr pilote mécaniquement) ; `tension` =
  combinateur commun. Pondérations dans `BridgeConfig` (calibrables). **À
  calibrer sur campagne réelle** : `fit_gain` (observé ~0.14 sur gemma3, bas).
- **2026-07-18 — Partage des responsabilités de modulation** : le P+I pilote
  **δr/τc** (application directe — sa stabilité vient de ses bandes/fuite/
  anti-windup ; l'hystérésis externe bloquait ses petits pas, constaté en live) ;
  la politique réactive pilote **ρ/κ** (garde-fous + EWMA). Un pilote par bouton.

- **2026-07-18 — Consensus ESMM à deux niveaux + rapprochement sémantique** :
  l'accord lexical exact entre modèles hétérogènes est une impasse empirique
  (constaté : 38 puis 56 propositions, 0 accord — « figure géométrique » vs
  « forme géométrique »). Le consensus vote sur des **clusters de liens** :
  sujet identique (lexical strict via `match_key`) + objets équivalents
  (lexical strict, sinon **cosinus mxbai-embed-large ≥ τ_obj=0.78** — calibré
  sur 8 paires observées, choix conservateur précision-d'abord, à recalibrer
  sur campagne). Niveaux : `exact` (même prédicat ≥2 modèles) / `pair` (même
  lien, prédicats ≠, majoritaire retenu). Premier run productif : 48 proposés →
  6 acceptés (4 exact + 2 pair), 34 rejetés.
- **2026-07-18 — Topologie (κ/ρ/Betti) REPORTÉE** : un programme plus abouti
  existe hors dépôt (conclusion de Simon : « je me compliquais la vie pour
  rien ») — investigation à part entière quand il sera fourni.

- **2026-07-18 — Récolte EPP_Verdict (organe aîné, jamais audité)** : cascade
  de matching du consensus ESMM alignée sur l'ADR-011-v2 d'EPP — **exact
  (match_key, diacritiques pliées) → Jaro-Winkler > 0.9 (stdlib, vérifié sur
  vecteurs de référence) → embeddings mxbai ≥ 0.78** ; groupes de synonymes de
  relations (ADR-006 d'EPP adapté à nos 8 canoniques français, FR+EN) pliés
  AVANT le vote. Mesure ayant tranché : les variantes d'accents tombent à
  JW≈0.877 < 0.9 → pliage des diacritiques dans match_key (exact, gratuit),
  JW réservé aux coquilles. Effet live : « fractale partie_de théorie
  mathématique » validé par 3 modèles au niveau exact.

- **2026-07-19 — Surface affective (théâtre honnête)** : la valence (joy/
  tension) est DÉRIVÉE des signaux réels du pont P2 (joy = 0.6·fit +
  0.4·coherence — poids de l'esquisse de Simon, « resonance » ≡ fit), rendue
  visible en fin de sortie (`[affect] joy=… tension=…`). C'est un AFFICHAGE,
  pas un second pilote (« un pilote par bouton ») : la modulation voulue par
  l'esquisse est déjà faite en amont par le P+I sur les mêmes signaux.
  Désactivée par défaut, comme dans le canon. `core/affect.py`.

## Décisions à trancher (à dater ici quand tranchées)

- **κ = courbure d'Ollivier vs proxy Jaccard `j−0.2` ?** Les archives livrent en
  réalité le proxy Jaccard, pas Ollivier. Question conservée pour le prochain
  cadrage topologique ; le report explicite du 18 juillet reste applicable.
- **prajñā / papañca** (introduits par Simon, 2026-07-19 : « demandent de la valence ») — mapping exact sur l'architecture À DÉFINIR PAR SIMON (discernement ↔ ? ; prolifération conceptuelle ↔ ?). Ne pas inventer à sa place.
- ⚠️ `ρ` topologique ≠ `ρ` de polarité de `Lyra_Jupyter_MCA` : ne pas confondre.

## Principe directeur

> Le LLM *utilise* Lyra ; il n'*est pas* Lyra.
> *(Formulation honnête reprise de `Lyra_Uni_0_2`.)*
