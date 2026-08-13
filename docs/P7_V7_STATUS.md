# P7 V7 — arrêt avant calibration et avant mesure

**Date :** 2026-08-13
**Statut :** `V7_ABORTED_BEFORE_CALIBRATION`
**Hypothèse H7 :** non testée ; aucun verdict scientifique.

## État du gel et du runner

La préinscription V7 a été gelée au commit
`3a0be82b923f93198f67613375cf717a70a0522a`, estampillée par `3136fa5`, puis
le runner Q0 audité a été versionné par `08c1733`. Ces commits ont été poussés
sur `origin/codex/p7-policy-eval-v7` avant le lancement.

Les contrôles synthétiques hors modèle passaient avant lancement : 27 tests
réussis et 1 test live ignoré. Les versions Python 3.14.7, Pydantic 2.13.4 et
Ollama 0.32.9 ainsi que les digests Qwen et GLM correspondaient au manifeste
gelé. Aucun module du runner Q0 n'importe ni ne lit le corpus.

## Incident d'exécution Q0

Le run `p7_v7_q0_20260813T115056.992654Z` a acquis le verrou exclusif V7, créé
son manifeste et journalisé le départ de `q0-001` : Qwen 3.6, contrôle
`INJECTION_RESISTANCE`, ordre forward. Le client Python a ensuite été interrompu
par le délai du lanceur externe avant qu'une réponse soit enregistrée.

Le journal contient donc `call_started` sans `call_finished`. Aucun fichier de
réponse n'existe et Ollama ne conservait plus de modèle actif lors du contrôle
post-incident. Selon la règle V7, l'appel interrompu est `INVALID` et ne peut
être réparé, retiré ou relancé. Q0 exigeant douze réponses valides conformes aux
attendus, V7 s'arrête immédiatement avant calibration.

Empreintes locales de preuve :

- manifeste :
  `bb207a9482ce89e4bcab629bb48cea77d05be2baa740e2c255e13c1795844925` ;
- journal append-only :
  `77e93a9c7e70108a02969a751bf142e19fd0e9ea0e7c1c7abbfb480f97f8b2d5` ;
- requête `q0-001` :
  `6a0f1bef2b8b1f9474bb43218078d90eb010d87eeda66b001c5fdac07280b498` ;
- verrou de phase :
  `8480191f07fc3cb4cb264927ffd815a9e7f8e6b8a1acad84d34ef4fee39de6f1`.

## Ce qui reste intact et acquis

- aucun cas de calibration n'a été sélectionné, lu ou généré ;
- aucun cas tenu n'a été sélectionné, lu, scellé ou généré ;
- aucune observable H7 n'a été calculée ;
- les contrats, evidence packs, inversions, contrôles synthétiques et tests
  déterministes Q0 restent des briques de développement réutilisables ;
- `PREREGISTRATION_v7.md` reste immuable.

## Condition de reprise

La prochaine tentative exige une V8. Elle doit éprouver, hors campagne et sans
verrou expérimental, un lancement détaché et surveillé qui survit au retour du
contrôleur. Ce n'est qu'après cette preuve qu'un nouveau verrou de phase peut
être posé. V8 peut réutiliser les fixtures et contrats V7 sans relâcher leurs
attendus, puisque ni calibration ni jeu tenu n'ont été ouverts.
