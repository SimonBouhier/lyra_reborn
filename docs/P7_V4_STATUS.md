# P7 V4 — arrêt avant calibration et avant mesure

**Date :** 2026-08-12
**Statut :** `V4_ABORTED_BEFORE_CALIBRATION`
**Hypothèse H4 :** non testée ; aucun verdict scientifique.

## Acquis du smoke synthétique

La correction causale de V4 fonctionne sur les trois producteurs gelés :

- COMMON T1 est strictement identique dans les deux traces ;
- cinq appels physiques sont exécutés selon ABBA ou BAAB ;
- les options ADAPTIVE divergent effectivement de STATIC_BEST aux tours 2–3 ;
- le champ natif Ollama `format` produit des objets JSON conformes au schéma.

Ces constats qualifient le câblage, pas la qualité de la politique.

## Matrice de compatibilité du contrat

Un seul cas synthétique public a été exécuté par modèle, sans juge et sans
contenu du corpus :

| Producteur | Ordre | COMMON T1 | ADAPTIVE | STATIC_BEST |
|---|---|---:|---|---|
| `mistral:latest` | ABBA | identique | citation absente | contrat satisfait |
| `gemma3:latest` | BAAB | identique | citation absente | citation absente |
| `granite3.3:latest` | ABBA | identique | citation absente | contrat satisfait |

« citation absente » signifie que le JSON et le schéma Pydantic sont valides,
mais que le texte déclaré comme citation est une paraphrase et non une
sous-chaîne exacte de la source normalisée.

Aucun cas de calibration ou tenu n'a été sélectionné, affiché ou généré. Cette
matrice n'entre dans aucune observable O1–O14 et ne soutient ni ne réfute H4.

## Décision méthodologique

Le contrat V4 confond trop fortement deux capacités : prendre une bonne décision
éditoriale et recopier verbatim un passage. Sur des modèles locaux de 4–8B, le
smoke indique que la seconde capacité risque de devenir une porte dominante,
sans être la question scientifique principale.

`PREREGISTRATION_v4.md` reste immuable. V5 doit remplacer la chaîne libre
`quote` par un identifiant de segment source déterministe :

1. la source normalisée est découpée avant génération en segments bornés
   `S001`, `S002`, …, sans LLM ;
2. ces identifiants et textes sont affichés dans SOURCE ;
3. `evidence` référence un `source_span_id` appartenant à l'enum du cas ;
4. Pydantic et le validateur prouvent l'existence de l'ancre ;
5. le panel juge si le segment soutient réellement la portée revendiquée.

Il n'y aura toujours ni réparation, ni citation inventée acceptée, ni score cheap
dans le juge. Le changement retire un artefact extractif du contrat objectif ;
il ne favorise pas une branche.
