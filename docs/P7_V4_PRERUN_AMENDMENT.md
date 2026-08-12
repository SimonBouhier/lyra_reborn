# P7 V4 — amendement d'implémentation avant run

**Date :** 2026-08-12
**Moment :** après gel V4, avant calibration et avant sélection/scellement tenu

## Observation

Le smoke synthétique Mistral V4 a validé COMMON T1 et les cinq appels ABBA,
mais les deux sorties finales ont échoué le contrat : une citation paraphrasée
et une réponse non-JSON stricte. Aucun cas tenu n'a été ouvert et aucune
observable H4 n'a été produite.

## Correction compatible avec le gel

Le schéma, le prompt, les seuils, les modèles, les knobs, le préfixe, l'ordre et
le verdict scientifique restent inchangés. Le même
`EditorialDecision.model_json_schema()` déjà inclus dans le prompt est transmis
au champ racine Ollama `format` au tour 3, pour les deux branches. Le schéma des
actions `ToolAction` est transmis de la même manière aux deux ordres de chaque
juge.

La documentation officielle Ollama indique que `/api/generate` accepte un objet
JSON Schema dans `format` et recommande de revalider la réponse avec Pydantic :

- https://docs.ollama.com/api/generate
- https://docs.ollama.com/capabilities/structured-outputs

Il n'y a toujours ni appel de réparation, ni extraction de clôture Markdown, ni
assouplissement des citations exactes. Pydantic et le contrôle de sous-chaîne
restent l'autorité du contrat. Cette correction est symétrique et réduit un
défaut de transport syntaxique ; elle ne fournit aucun score à Lyra.

## Résultat de compatibilité

Le format natif a supprimé les sorties non-JSON, mais la matrice des trois
producteurs a montré cinq échecs de citation exacte sur six branches. V4 est
donc arrêtée avant calibration ; voir `docs/P7_V4_STATUS.md`. Aucun seuil ou
contrat V4 n'est modifié rétroactivement.
