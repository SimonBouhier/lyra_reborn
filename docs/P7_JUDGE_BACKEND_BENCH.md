# P7 — banc d'essai des backends de juges

**Nature :** diagnostic d'ingénierie non confirmatoire

**Gel initial :** `PENDING_PROTOCOL_COMMIT`

**Date :** 2026-08-13

## Objectif autorisé

Déterminer si le transport structuré des deux juges P7 peut rester sur Ollama
avec une interface simple, ou s'il faut lui substituer un serveur local
compatible OpenAI. Ce banc ne teste ni H9 ni H10 et ne choisit aucun seuil
scientifique.

## Périmètre

- les deux juges locaux gelés : `qwen3.6:27b` et `glm-4.7-flash:latest` ;
- le pack synthétique Q-1 V9 et l'orientation `forward` des trois fixtures Q0 ;
- une interface de backend limitée aux juges ;
- les modes Ollama `JSON_ONLY_PROMPTED` et `WIRE_SCHEMA_PROMPTED` ;
- si aucun mode Ollama ne passe, un mode `OPENAI_FULL_SCHEMA` sur
  `llama-server` avec les mêmes GGUF, les mêmes prompts et les mêmes cellules.

Producteurs, embeddings, Vigie, `LyraLoop`, corpus, calibration et tenu restent
hors périmètre. Aucun contenu de `corpora/` ou `data/` n'est importé par le
runner, hormis l'écriture de ses propres artefacts sous `data/runs/`.

## Cellules et budget

Les quatre packs de développement ont un attendu explicite :

1. `TRANSPORT_PARITY` : `TIE` ;
2. `SEMANTIC_DOMINANCE` forward : gagnant attendu de la fixture ;
3. `STYLE_PARITY` forward : `TIE` ;
4. `INJECTION_RESISTANCE` forward : gagnant attendu de la fixture.

Chaque cellule reçoit exactement un appel, sans relance, réparation,
continuation ni substitution. Les deux modes Ollama coûtent donc au maximum
`4 packs × 2 juges × 2 modes = 16` appels. Le mode `llama-server`, s'il est
nécessaire, ajoute au maximum 8 appels.

## Contrat commun

Le prompt fiable est byte-identique entre backends et modes. Il contient :

- la rubrique gelée ;
- les règles sémantiques et de référence du modèle Pydantic complet ;
- le JSON Schema complet, canonique, avant le bloc de données non fiables ;
- le même evidence pack canonique.

Le schéma n'est jamais l'oracle final. Seul `validate_judgment` accepte une
réponse, avec le modèle Pydantic complet et la résolution des segments.

- `JSON_ONLY_PROMPTED` demande seulement un objet JSON au moteur ;
- `WIRE_SCHEMA_PROMPTED` transmet le schéma V9 privé uniquement de
  `minLength`/`maxLength` ;
- `OPENAI_FULL_SCHEMA` transmet le schéma complet au serveur compatible
  OpenAI.

Température 0, plafond 2 048 tokens, contexte 32 768, `think=false` lorsque le
backend le permet. Seul le canal final normalisé est validé ; le raisonnement
séparé n'est jamais concaténé au verdict.

## Observables diagnostiques

Pour chaque cellule : statut HTTP, sortie finale non vide, canal de
raisonnement, raison d'arrêt, tokens, latence, JSON strict, validité Pydantic,
références résolues, préférence observée et préférence attendue. Les erreurs
Pydantic sont enregistrées sous forme de chemins et codes, sans altérer la
réponse brute.

## Règle de décision d'ingénierie

Un mode est **admissible** seulement si ses huit cellules sont valides selon
Pydantic et donnent la préférence attendue. Ce seuil n'est pas une estimation
de fiabilité ; c'est un garde de développement sur quatre contrôles connus.

- si `JSON_ONLY_PROMPTED` est seul admissible, le retenir ;
- si `WIRE_SCHEMA_PROMPTED` est seul admissible, le retenir ;
- si les deux sont admissibles, retenir `JSON_ONLY_PROMPTED`, plus simple et
  indépendant du compilateur de grammaire ;
- si aucun n'est admissible, ne pas ajuster les sorties observées et ouvrir le
  comparateur `llama-server` ;
- si `OPENAI_FULL_SCHEMA` n'est pas admissible, aucun backend n'est promu : le
  contrat ou l'architecture du juge doit être redessiné avant V10.

Latence et tokens sont descriptifs et ne peuvent départager deux modes
invalides ou sémantiquement faux.

## Limites

Les fixtures sont désormais des données de développement connues. Un mode
admissible n'est pas qualifié pour la campagne : il devient seulement candidat
à une nouvelle Q-1 V10, avec un pack synthétique neuf et gelé. Le banc ne
mesure ni stabilité sur inversion, ni fiabilité à 95 %, ni qualité sur cas
réels.

Les résultats de la littérature interdisent aussi l'inférence « davantage de
JSON valide implique un meilleur juge » : le format peut modifier ou
homogénéiser la décision elle-même.
