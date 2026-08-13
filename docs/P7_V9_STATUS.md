# P7 V9 — arrêt à la préqualification du transport

**Date :** 2026-08-13

**Statut :** `V9_ABORTED_BEFORE_Q0`

**Hypothèse H9 :** non testée ; aucun verdict scientifique.

## Gel et lancement

V9 a été gelée au commit
`882f10cc04c7d470191d18a10df8063cd0b07c71`, estampillée par `c4bf68d`,
puis son runner a été versionné au commit `57ea03d`. La branche
`codex/p7-policy-eval-v9` avait été poussée avant l'exécution.

Une première invocation avec
`python scripts\p7_v9.py run --timeout 600` a échoué pendant les imports avec
`ModuleNotFoundError: No module named 'scripts'`. Cet échec a précédé toute
exécution du runner : aucun appel Ollama, répertoire V9 ou verrou n'a été
créé. L'invocation correcte, vérifiée par `--help`, est :

```text
python -m scripts.p7_v9 run --timeout 600
```

Les 19 tests ciblés P7 ont réussi avant l'ouverture de Q-1.

## Résultat Q-1

Le run `p7_v9_qminus1_20260813T131148.616025Z` a acquis le verrou Q-1 et
envoyé exactement les deux appels préinscrits, un par juge, sans relance ni
réparation. Le runtime et les digests correspondaient au gel.

La correction de transport a fonctionné pour les deux juges :

- HTTP 200 ;
- JSON non vide dans `response` ;
- champ `thinking` absent ;
- `done_reason=stop` ;
- aucune troncature (`eval_count` 476 pour Qwen et 244 pour GLM).

Les deux réponses ont toutefois échoué devant le contrat Pydantic complet :

- les quatre premières `claim` de chaque juge contenaient moins de 30
  caractères ;
- le critère `contradiction` de chaque juge ne citait ni segment source ni tour ;
- GLM ne contenait aucun `turn_refs`, et ne pouvait donc satisfaire la
  couverture obligatoire des candidats A et B.

Ces erreurs ont été diagnostiquées hors campagne par validation des réponses
brutes. Des substitutions temporaires en mémoire ont seulement servi à
révéler les validateurs suivants ; elles n'ont modifié aucun artefact, aucun
verdict et ne constituent pas une réparation admise.

Q-1 s'est donc terminée avec 0 réponse valide sur 2 et le statut
`V9_ABORTED_BEFORE_Q0`. Conformément au gel, le runner n'a créé ni répertoire
ni verrou Q0 et n'a envoyé aucun des douze appels Q0.

## Empreintes locales de preuve

- pack Q-1 :
  `7f486109f52923b03fafadfa5ac57eee0389992d1f9c8fa148458d31d0a2e541` ;
- schéma Pydantic complet :
  `fe30a5fe1699fa1ba33739bb30d77d7cbc96d55ac87a9408f0a1b7709a59ecfa` ;
- schéma fil :
  `08476fb85cd75612321cfc0a6e7ef710575e684cf82007c99065b622e9d6240d` ;
- manifeste :
  `e0736a884f60784387019ace58a278f1d7a22a9f610b51674bbc01443628904d` ;
- journal append-only :
  `743f798a891274d3be062811caa3912e0024425c21358520547adfee860950eb` ;
- résumé :
  `0c3bff41a61918e9a844211e60c08c9503d3b95c705f1918f2138b1d60d5c078` ;
- requête/réponse Qwen :
  `12ecefc14667b5ca126567c5130ad0ca82c3c244a61a6324f33a700e2e491304` /
  `4e046c29a9b8d05a9d9c4118f47bdb908acdea5e2565782088af766bb1b0c3c1` ;
- requête/réponse GLM :
  `940bf0354b740a5c3928abf15aba345b11d108e9ee7b57cd47fd615103c74154` /
  `7f873c4def508dc5ea6c214093e3ba0525d64aa9cbffc9af98bb35233fa716b1` ;
- verrou Q-1 :
  `09c0df7374ece52287387da61ab958aa108f3143f876f2e903e38b4da2db1e9c`.

## Frontière des conclusions

- la compilation de la grammaire V9 est fonctionnelle sur les deux juges ;
- `think=false` route bien leurs sorties vers `response` ;
- la validation Pydantic post-génération a empêché un faux PASS ;
- la justesse sémantique du panel n'est pas qualifiée ;
- aucun cas Q0, de calibration ou tenu n'a été ouvert ;
- aucune observable H9 n'a été calculée ;
- `PREREGISTRATION_v9.md` reste immuable.

## Condition de reprise

Le verrou V9 est consommé et interdit toute relance sous ce gel. Une reprise
exige V10. Elle devra qualifier hors campagne une représentation compatible
avec le compilateur Ollama qui rende obligatoires les références et guide des
`claim` substantives sans relâcher leur validation finale. Toute modification
du prompt, du schéma fil ou du modèle Pydantic devra être explicite et gelée
avant une nouvelle Q-1.
