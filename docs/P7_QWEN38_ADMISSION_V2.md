# P7 — admission diagnostique de Qwen 3.8 V2

**Nature :** banc d'ingénierie synthétique, non confirmatoire  
**Langue :** anglais uniquement  
**Gel initial :** `08c0de9cee2806f58c9922359a74616d0dc5cad5`

## Incorporation du protocole initial

La V2 incorpore sans changement l'objectif, l'artefact modèle, les huit
orientations anglaises, les trois répétitions, l'ordre déterministe, les 24
appels, le transport `JSON_ONLY_PROMPTED`, le prompt, le contrat Pydantic, les
paramètres, les artefacts et la règle de décision de
`docs/P7_QWEN38_ADMISSION.md`, gelé au commit
`876d13f5cf8eac6bb863ee1205a5f172c824919d`.

La première exécution a été interrompue après un appel terminé parce que le
serveur Ollama, lancé avant la fin de son auto-mise à jour, n'avait détecté que
le CPU. Elle ne qualifie pas Qwen 3.8 et reste décrite dans
`docs/P7_QWEN38_ADMISSION_STATUS.md`.

## Unique modification : précondition GPU avant verrou

Avant d'acquérir le verrou V2 et avant tout appel de fixture, le runner lit
`/api/ps`. Le modèle gelé doit être déjà chargé au contexte 32K et présenter :

- le digest exact
  `22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643` ;
- `size > 0` ;
- `size_vram == size`.

Si cette précondition échoue, le runner s'arrête sans créer de verrou, de run
ou de requête de fixture. La même égalité est revérifiée après le vingt-quatrième
appel. Cette garde ne modifie ni les données ni le verdict ; elle empêche
seulement une exécution accidentelle intégralement CPU.

Le chargement préalable peut être réalisé par un smoke séparé, sans aucune
fixture du banc. Son résultat ne participe pas à la qualification.
