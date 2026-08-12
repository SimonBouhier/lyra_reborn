# P7 V5 — arrêt avant calibration et avant mesure

**Date :** 2026-08-12
**Statut :** `V5_ABORTED_BEFORE_CALIBRATION`
**Hypothèse H5 :** non testée ; aucun verdict scientifique.

## Acquis du smoke producteur

Le contrat à ancres déterministes résout le goulot de copie verbatim de V4.
Sur l'unique source synthétique publique, les trois producteurs ont satisfait :

- COMMON T1 byte-identique entre branches ;
- cinq appels ABBA ou BAAB ;
- différence d'options ADAPTIVE aux tours 2–3 ;
- JSON Schema natif puis validation Pydantic ;
- une à trois ancres appartenant effectivement aux segments du cas ;
- contrat final complet pour les six branches.

Aucun cas de calibration ou tenu n'a été sélectionné, affiché ou généré. Ces
constats qualifient le câblage, pas H5.

## Défaut du smoke juge

Le smoke avec Mistral producteur et Gemma premier juge s'est arrêté avant tout
verdict : `JudgeProtocolError: judge exhausted its bounded evidence budget`.

Le Scope V5 limitait le juge à six étapes. Or un juge qui exploite les outils
disponibles peut légitimement consommer :

1. lecture SOURCE ;
2. lecture TRACE A ;
3. lecture TRACE B ;
4–9. vérification d'une à trois ancres par candidat ;
10. verdict.

Le budget gelé pénalise donc le comportement de vérification que le protocole
cherche précisément à provoquer. Augmenter `max_steps` ou changer les outils
toucherait le Scope ; `PREREGISTRATION_v5.md` reste immuable.

## Décision pour V6

V6 doit remplacer la vérification unitaire par un outil batch borné :

- `CHECK_SPANS(candidate=A|B)` lit les IDs déclarés dans la décision du
  candidat et retourne, en une action, chaque ID, son existence et son texte ;
- ordre minimal et maximal attendu : SOURCE, TRACE A, TRACE B, CHECK_SPANS A,
  CHECK_SPANS B, VERDICT ;
- six étapes redeviennent suffisantes sans réduire la preuve ni augmenter le
  budget ;
- le verdict avant les cinq lectures/vérifications obligatoires échoue.

Un panel `UNRESOLVED` restera un résultat valide ; l'épuisement du budget avant
les preuves obligatoires restera une erreur explicite.
