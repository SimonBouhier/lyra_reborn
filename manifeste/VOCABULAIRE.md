# Vocabulaire canonique de Lyra

Source unique de vérité, pour arrêter la dérive de sens constatée d'un dossier à
l'autre dans les archives. Toute brique se réfère à ces définitions.

| Terme | Définition retenue | Implémentation | Origine (audit) |
|---|---|---|---|
| **ρ (rho)** | structure / diversité contrôlée → `top_p` | `core/knobs.py` | né comme coeff. de couplage d'EDO (`lyra_project`) |
| **δr (delta_r)** | dilatation du contexte / longueur → `num_predict` | `core/knobs.py` | famille Uni |
| **τc (tau_c)** | tension → `temperature` ; mesurable comme divergence d'embeddings | `core/knobs.py` | `LyrAgent`, `conscious` |
| **κ (kappa)** | courbure/style, anti-répétition → `repeat_penalty` | `core/knobs.py` | `Topologie`/`Lyra_Core` |
| **Φ(t)** | Φ(t) := M[Σ(S(t))] — agrégat d'état, critère d'émergence stabilisée | *à implémenter (P2)* | `lyra_project`, .txt formel |
| **phase λ** | régime cognitif détecté + garde à hystérésis (cooldown) | `core/control/phase.py` | spec dans `Archi/phase_lambda.md` |
| **nemeton** | graphe sémantique de concepts/états | *à implémenter (P3)* | famille Uni, `Lyra_Core` |
| **ispace** | espace navigable d'états + réglages associés (CBR) | *à implémenter (P3)* | `IspaceNav.zip` |
| **modules A/M/P/G/X/R** | ontologie de modules cognitifs typés | *à implémenter* | manifeste, `Archi/kit_lyra` |
| **SilenceØ** | le refus/silence comme réponse de première classe | *à implémenter (P5)* | `LyrAgent` |

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
  réalité le proxy Jaccard, pas Ollivier. Décision : _à trancher en P2_.
- **prajñā / papañca** (introduits par Simon, 2026-07-19 : « demandent de la valence ») — mapping exact sur l'architecture À DÉFINIR PAR SIMON (discernement ↔ ? ; prolifération conceptuelle ↔ ?). Ne pas inventer à sa place.
- ⚠️ `ρ` topologique ≠ `ρ` de polarité de `Lyra_Jupyter_MCA` : ne pas confondre.

## Principe directeur

> Le LLM *utilise* Lyra ; il n'*est pas* Lyra.
> *(Formulation honnête reprise de `Lyra_Uni_0_2`.)*
