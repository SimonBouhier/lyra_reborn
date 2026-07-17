# Références externes

Sources déposées dans `docs/`. Ce que chacune ancre dans le projet.

| Fichier | Titre / auteurs | Ce que ça ancre |
|---|---|---|
| `2607.13104v1.pdf` | *Self-Improvements in Modern Agentic Systems: A Survey* — Ren, Chen, Guo, … **J. Schmidhuber** (KAUST, Jilin U.), juil. 2026 | **Bannière La Jachère / Organe 1** (Pouponnière évolutive). Taxonomie *foundation-model vs scaffold self-improvement* ; case **Population-Based scaffolding self-improvement** = notre pouponnière évolutive. Méthodes citables : Promptbreeder, ADAS, Darwin Gödel Machine, AlphaEvolve/ShinkaEvolve, GPTSwarm, POWERPLAY ; plafond = Gödel Machine. Couvre « evaluation harnesses », « skill libraries », « autonomous tool creation ». **Ne couvre pas** le sommeil/rêve. |
| `2607.06906v1.pdf` | *The Harness Effect: How Orchestration Design Sets the Token Economics of Enterprise Agentic AI* — Writer, Inc., juil. 2026 | **Organe 1** (justification empirique). Le **harness** est LE levier coût **et** qualité (swap d'orchestration seule : −33 à −61 % coût, +82 % qualité/\$, −38 % tokens à parité) ; gain **spécifique au modèle** → un harness doit être cultivé **par-modèle / par-tâche**. Concept clé : *token maxing*. |
| `Language_Models_Need_Sleep_Learning_to_Self-Modify.pdf` | *Language Models Need Sleep: Learning to Self-Modify and Consolidate Memories* — Behrouz, Hashemi, **Mirrokni** (Google) | **Organe 2 — Le Songe** (le mécanisme). Paradigme **« Sleep »** en 2 stades : (1) **Consolidation mémoire** = *Knowledge Seeding* (distillation ascendante par *replay*, ≈ NREM) ; (2) **Dreaming** = auto-amélioration par curriculum synthétique auto-généré via RL (≈ REM), apparenté aux *self-edits* de **SEAL**. Le Dreaming *est* le pont vers l'Organe 1 (curriculum auto-généré → candidats). ⚠️ mécanisme en espace **paramétrique** → sur Ollama gelé, cf. les 2 paliers de `BANNIERE_LA_JACHERE.md`. |

**Statut :** l'**Organe 2** est désormais **fondé** (mécanisme du papier ci-dessus).
Reste à décider, pour le **Palier 2** (consolidation paramétrique / *Knowledge
Seeding* réel), l'ajout éventuel d'une brique de **fine-tuning local** (LoRA) —
non requise pour le Palier 1 (rêve au niveau scaffold/mémoire).

> Rappel charte §4 : un chiffre issu de ces papiers est cité *comme résultat de
> ces papiers*, pas comme un résultat de Lyra. Les résultats de Lyra doivent être
> régénérables par un script du dépôt.
