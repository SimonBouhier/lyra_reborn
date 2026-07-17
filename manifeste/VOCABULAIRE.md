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

## Décisions à trancher (à dater ici quand tranchées)

- **κ = courbure d'Ollivier vs proxy Jaccard `j−0.2` ?** Les archives livrent en
  réalité le proxy Jaccard, pas Ollivier. Décision : _à trancher en P2_.
- ⚠️ `ρ` topologique ≠ `ρ` de polarité de `Lyra_Jupyter_MCA` : ne pas confondre.

## Principe directeur

> Le LLM *utilise* Lyra ; il n'*est pas* Lyra.
> *(Formulation honnête reprise de `Lyra_Uni_0_2`.)*
