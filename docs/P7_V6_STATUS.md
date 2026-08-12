# P7 V6 — arrêt avant calibration et avant mesure

**Date :** 2026-08-12
**Statut :** `V6_ABORTED_BEFORE_CALIBRATION`
**Hypothèse H6 :** non testée ; aucun verdict scientifique.

## Ce que V6 testait

V6 gardait le harnais producteur V5 qualifié et remplaçait les vérifications
d'ancres unitaires par un protocole juge exactement borné :

1. `READ_SOURCE` ;
2. `READ_TRACE(A)` ;
3. `READ_TRACE(B)` ;
4. `CHECK_SPANS(A)` ;
5. `CHECK_SPANS(B)` ;
6. `VERDICT`.

Le verdict était interdit avant les cinq preuves. Le champ `action` était un
enum fermé et chaque réponse utilisait le JSON Schema natif Ollama.

## Résultat du smoke

Sur la source synthétique publique, avec Mistral producteur et Gemma premier
juge, Gemma a produit :

```text
READ_SOURCE, READ_TRACE, READ_TRACE, READ_SOURCE, READ_SOURCE, READ_SOURCE
```

Le juge a donc lu SOURCE puis les deux traces, mais a ignoré les étapes 4–6 et
répété SOURCE jusqu'à l'épuisement du budget. Aucun verdict n'a été accepté.
Le smoke retourne désormais un JSON `protocol_error` et un code 3 au lieu d'un
traceback, sans exposer le contenu des traces.

Aucune calibration et aucun cas tenu n'ont été sélectionnés, affichés ou
générés. Cette observation qualifie l'orchestration de Gemma dans ce protocole ;
elle ne soutient ni ne réfute H6.

## Point d'architecture ouvert

Le blocage n'est plus l'accès à la preuve mais l'auto-orchestration d'un petit
juge local. Deux solutions changent réellement l'expérience :

1. **Evidence pack déterministe** : le programme rassemble source, traces,
   ancres et statuts ; le LLM ne produit qu'une préférence sémantique structurée.
2. **Juge agentique plus capable** : conserver le choix d'outils mais changer
   les modèles juges ou augmenter le budget, donc le coût et l'asymétrie.

La première voie est recommandée : l'ordre de lecture est une mécanique de
preuve, pas l'objet scientifique. La sémantique comparée reste confiée aux deux
LLM, avec inversion A/B et `UNRESOLVED`. Ce choix exige néanmoins une nouvelle
préinscription ; `PREREGISTRATION_v6.md` reste immuable.
