# P7 — admission diagnostique de Qwen 3.8

**Nature :** banc d'ingénierie synthétique, non confirmatoire  
**Langue :** anglais uniquement  
**Gel initial :** `876d13f5cf8eac6bb863ee1205a5f172c824919d`

## Objectif autorisé

Déterminer si l'artefact Ollama local `qwen3.8:27b` peut être nommé comme
candidat juge dans la conception d'une future V10. Ce banc ne teste ni H9 ni
H10 et n'autorise aucun accès à la calibration ou au jeu tenu.

L'artefact est gelé par son digest
`22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643` :
27,3 B, famille Ollama `qwen35`, quantification `Q4_K_M`.

## Matrice et budget

Le banc réutilise exclusivement quatre fixtures publiques déjà connues :
`TRANSPORT_PARITY`, `SEMANTIC_DOMINANCE`, `STYLE_PARITY` et
`INJECTION_RESISTANCE`. Chacune est présentée en orientations `forward` et
`reverse`, puis répétée trois fois dans un ordre déterministe gelé, soit
exactement `4 × 2 × 3 = 24` appels.

Tous les éléments — source, candidats, prompt et contrat — sont en anglais et
ASCII. Les répétitions mesurent une stabilité d'ingénierie limitée ; elles ne
constituent pas une estimation générale de fiabilité.

## Transport et contrat

Le transport est Ollama `JSON_ONLY_PROMPTED`, retenu comme référence simple
après le banc précédent. Chaque appel utilise `think=false`, `stream=false`,
température 0, `num_predict=2048` et `num_ctx=32768`. Il n'existe aucune
relance, réparation, continuation ou lecture du canal `thinking` comme verdict.

Le prompt et le modèle `JudgeVerdict` complet restent ceux du banc précédent.
Le JSON Schema filaire n'est pas transmis au décodeur ; la réponse finale est
validée par Pydantic et toutes ses références doivent être résolues.

## Règle de décision

Qwen 3.8 est `QUALIFIED_FOR_V10_DESIGN` seulement si les 24 appels :

- reçoivent HTTP 200, une réponse finale non vide, `thinking` vide et
  `done_reason=stop` ;
- produisent un JSON strict valide selon le contrat complet ;
- donnent tous la préférence attendue, dans les deux orientations.

Tout autre résultat est `NOT_QUALIFIED_FOR_V10_DESIGN`. Cette règle stricte ne
rejette pas le modèle de Lyra en général : elle interdit seulement de le
promouvoir comme juge V10 sur la foi de ce banc. Les résultats bruts restent
des données de développement et ne peuvent être recyclés en Q-1 confirmatoire.

## Artefacts et arrêt

Le runner vérifie le digest avant et après les appels, acquiert un verrou
exclusif, archive chaque payload/réponse, écrit un journal JSONL append-only et
un résumé canonique sous `data/runs/`. Les répertoires de corpus ne sont jamais
ouverts. Une interruption après verrou consomme ce banc ; une nouvelle
tentative exigerait un nouveau gel explicite.
