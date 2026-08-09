# Statut de la campagne Vigie shadow V1

**Statut final : `ABORTED_BEFORE_MEASUREMENT`**

La campagne définie par `PREREGISTRATION_v1.md` a été arrêtée le 2026-08-09
avant toute inférence de modèle et avant tout calcul de métrique.

## État au moment de l'arrêt

- le pool public et la file de 120 cas avaient été construits et scellés
  localement ;
- aucune ligne de prédiction n'existait dans
  `data/runs/vigie_shadow_v1/predictions.jsonl` ;
- une seule annotation humaine avait été enregistrée, sur le premier cas ;
- aucun `items.jsonl`, `labels.jsonl` ou manifeste final n'avait été produit ;
- aucun résultat scientifique, positif ou négatif, ne peut être tiré de V1.

## Motif

Le coût réel d'une revue manuelle exhaustive de 120 cas invalidait une
hypothèse opérationnelle du protocole. Les deux premiers cas affichés ont en
outre rendu visible que les 60 attaques étaient des transformations
synthétiques ajoutées par l'instrument aux porteurs publics, et non 60 attaques
naturelles découvertes dans les sources.

Le protocole V1 et son historique restent inchangés. La suite est définie dans
une pré-inscription V2 distincte : nouveaux cas non vus, labels d'attaque par
construction, provenance des labels explicite et audit humain stratifié des
cas bénins. V2 ne pourra pas être présentée comme un benchmark entièrement
annoté par des humains ni autoriser à elle seule un déploiement S1.
