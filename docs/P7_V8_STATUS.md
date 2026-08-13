# P7 V8 — arrêt avant calibration sur incompatibilité de grammaire

**Date :** 2026-08-13
**Statut :** `V8_ABORTED_BEFORE_CALIBRATION`
**Hypothèse H8 :** non testée ; aucun verdict scientifique.

## Gel et exécution

V8 a conservé les données, modèles, seed, fixtures, rubrique, seuils et
verdicts substantifs V7. Elle a été gelée au commit
`88590fcc59dc1845a4e747b7160da2f68d54afb5`, estampillée par `95742ee`, puis
son runner détachable a été versionné jusqu'au commit `4fbc791`. La branche
`codex/p7-policy-eval-v8` a été poussée avant Q0.

Le smoke de cycle de vie exigé par V8 a réussi hors campagne : le contrôleur a
rendu la main, un contrôle séparé a observé l'enfant encore vivant avec le
marqueur de départ présent et le marqueur final absent, puis le même PID a
terminé naturellement avec `status=PASS`. Stdout et stderr étaient séparés et
vides. Aucun verrou expérimental n'existait pendant ce smoke.

Empreintes de cette preuve locale :

- départ :
  `cd9c696b82c1fb234cd6f2c8e9e0880ba6d599e8268eebb258e490722a2fe27e` ;
- fin :
  `59c83d1d2cfba1f0412197474eaffe9d0206526a30acf56a251ad67170e6af7b`.

## Résultat Q0

Le run `p7_v8_q0_20260813T120320.726471Z` a acquis son verrou, construit les
six packs déterministes et tenté exactement les douze appels prévus, dans les
deux blocs Qwen puis GLM. Chaque appel possède un événement `call_started` et
un événement `call_finished`. Aucune relance ni réparation n'a eu lieu.

Les douze appels ont été refusés par Ollama avant génération avec HTTP 400 :

```text
Failed to initialize samplers: failed to parse grammar
```

Les deux modèles et toutes les orientations sont touchés de la même manière.
Le problème est donc situé avant le jugement sémantique, dans la compilation de
la grammaire dérivée du JSON Schema natif. Les douze réponses valent `INVALID`,
Q0 échoue avec 0 réponse valide sur 12, et H8 reste non testée.

Le résumé brut utilise encore par erreur la clé historique `h7` avec la valeur
`UNTESTED`. Ce défaut de libellé est consigné et ne change ni le statut V8, ni
les appels, ni le verdict Q0.

Empreintes locales de preuve :

- manifeste :
  `3d38a76b2e978b7282df87811b30dfe5665a366bbcff9b4aba83bdd571217220` ;
- journal append-only :
  `75e11d42b8232df1eabfc83bdfa355f50b13668e8382931acdcdc06464f9cd2d` ;
- résumé :
  `d36c5b6c83ca97978228b650a87016905d46b7f9deef9d9ec7d4ef8e5fb898e8` ;
- première réponse d'erreur :
  `4ea5297fd48a95992c3047e5fe1116f2a7260c0f56852ea1cfafc289dafc035e` ;
- verrou :
  `b92e54100b787ee75e267da0db1a1908913693dedd55503f4d8fa7861958bdbe`.

## Frontière des conclusions

- aucun token de jugement n'a été généré ;
- aucun cas de calibration n'a été sélectionné, lu ou généré ;
- aucun cas tenu n'a été sélectionné, lu, scellé ou généré ;
- aucune observable H8 n'a été calculée ;
- l'evidence pack et les tests déterministes restent acquis ;
- `PREREGISTRATION_v8.md` reste immuable.

## Condition de reprise

La prochaine tentative exige V9. Avant son verrou expérimental, elle devra
faire accepter par Ollama, sur une donnée synthétique distincte des fixtures
Q0, le schéma exact qui sera envoyé aux juges. Ce contrôle doit prouver la
compilation de grammaire et la validation Pydantic en un seul appel par modèle.
Un schéma compatible peut être simplifié dans V9, mais la rubrique qualitative,
les six critères, leurs références, l'inversion et l'absence de réparation ne
doivent pas être relâchés.
