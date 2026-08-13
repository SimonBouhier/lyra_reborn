# P7 — statut du banc des backends de juges

**Date :** 2026-08-13

**Protocole gelé :** `69e34deab012895caf4f0b377d8622f942febb86`

**Verdict :** aucun backend n'est promu ; V10 reste fermé.

## Exécution Ollama

- run : `data/runs/p7_backend_bench_20260813T165319.545409Z` ;
- journal SHA-256 :
  `f554143df3847153ec936395a4d89ba0475db906124c95367a671cea99a86a8b` ;
- 16 appels planifiés et 16 enregistrés ;
- aucun retry, aucune réparation, aucun accès au corpus, à la calibration ou au
  tenu ;
- Python `3.14.7`, Pydantic `2.13.4`, Ollama `0.32.9` ;
- juges gelés : `qwen3.6:27b`
  (`a50eda8ed977ab48a12431878896b27ffd5cef552c17af3317d9623b939a7f1e`)
  et `glm-4.7-flash:latest`
  (`4475827791a269b02c8ec49b1c3bc1abb5846bacf3fae015b75d33986322d8f6`).

| Transport | Qwen valide/juste | GLM valide/juste | Total valide/juste | Admissible |
|---|---:|---:|---:|---:|
| `JSON_ONLY_PROMPTED` | 4/4 | 3/3 sur 4 | 7/7 sur 8 | non |
| `WIRE_SCHEMA_PROMPTED` | 4/3 | 0/0 sur 4 | 4/3 sur 8 | non |

Le mode JSON simple manque l'admissibilité sur une sortie GLM pourtant
sémantiquement correcte : elle ne cite jamais le candidat A. Le schéma filaire
est nettement plus mauvais. Qwen y invente une préférence B sur la cellule
strictement équivalente `TRANSPORT_PARITY`; GLM duplique ou omet des critères
et produit des références unilatérales. Toutes les réponses se terminent par
`stop`; aucune n'est tronquée et aucun canal de raisonnement séparé n'est
présent. Les échecs observés ne sont donc pas des erreurs HTTP ni une simple
limite de tokens.

## Préflight llama-server

- build officiel : llama.cpp `10405`, commit `e79e4bf66` ;
- archive Windows CUDA 12.4 vérifiée avant extraction :
  `7da18847181aa668a77b02fa8bd47bb9588b82ca077cf184bccc3bf016b46e79` ;
- exécutable :
  `731fe93a56a8cfbc460a18179be822f6b31bda0b1de3d10749004c9e46137582` ;
- préflight complet :
  `data/runs/p7_backend_llama_preflight_20260813T171550.544741Z` ;
- appels modèle effectués : zéro.

Les deux blobs GGUF d'Ollama sont incompatibles avec llama.cpp upstream :

- Qwen : `qwen35.rope.dimension_sections` contient 3 valeurs, alors que le
  chargeur upstream en attend 4 ;
- GLM : l'architecture GGUF `glm4moelite` est inconnue du chargeur upstream.

Le mode conditionnel `OPENAI_FULL_SCHEMA` ne peut donc pas être évalué avec
les mêmes artefacts, comme l'exige le protocole. Télécharger ou convertir
d'autres GGUF changerait les artefacts modèles et constituerait une nouvelle
comparaison, à geler séparément.

## Interprétation

Le résultat ne justifie pas une migration générale hors d'Ollama. Il montre
deux choses distinctes :

1. la contrainte de grammaire la plus forte dégrade ici la validité sémantique
   ou contractuelle ;
2. les blobs Ollama récents ne forment pas une couche de stockage portable
   vers llama.cpp upstream.

La frontière de backend ajoutée reste utile : producteurs et embeddings
restent inchangés, tandis qu'un futur juge peut changer de transport sans
refonte de `LyraLoop`. Mais aucun transport n'achète à lui seul une meilleure
capacité de jugement. Le prochain choix doit porter d'abord sur le contrat et
le panel de juges.

## Porte de sortie proposée

Option recommandée avant toute nouvelle campagne : conserver Ollama comme
hôte local, garder `JSON_ONLY_PROMPTED` comme référence d'ingénierie, puis
préinscrire un V10 avec un contrat de décision plus petit et un second juge
réévalué. Ce V10 doit conserver le jugement holistique dans le prompt, mais ne
demander au JSON final que les éléments réellement utilisés par le verdict.

Deux alternatives restent ouvertes mais exigent un nouveau gel :

- télécharger deux GGUF upstream compatibles avec llama.cpp, ce qui change les
  artefacts modèles et duplique plusieurs dizaines de Go ;
- employer un juge distant compatible JSON Schema, ce qui change le coût, la
  confidentialité et l'indépendance du panel.

Dans tous les cas, les quatre cellules présentes sont désormais des données de
développement connues et ne peuvent pas servir de Q-1 confirmatoire à V10.

## Vérification de livraison

- tests ciblés du banc et du préflight : `11 passed` ;
- compilation Python et `git diff --check` : succès ;
- commandes exactes `--help`, banc Ollama et préflight exécutées depuis la
  racine avec `python -m` ;
- suite globale : `150 passed, 1 skipped, 1 failed`.

L'unique échec global est extérieur à ce diff : le test Vigie exige encore que
`EPP_Verdict/epp_quarantine_sidecar.py` soit identique au commit gelé
`3a274cd`, alors que le checkout EPP ouvert ne contient plus ce fichier. Ce
chantier ne modifie ni EPP ni ce test historique.
