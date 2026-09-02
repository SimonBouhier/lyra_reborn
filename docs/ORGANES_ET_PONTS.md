# Organes et ponts — doctrine d'architecture inter-projets

> **Décision Simon, 2026-07-18.** Lyra n'est pas un monolithe en croissance :
> c'est un **OS cognitif** auquel se greffent des **organes indépendants**,
> reliés par des **ponts**. D'autres organes viendront.

## La carte actuelle

```
   ┌─────────────────────────┐         ┌──────────────────────────────┐
   │  lyra_reborn            │  pont   │  EPP_Verdict                 │
   │  L'OS COGNITIF          │◄───────►│  MOTEUR D'ATTESTATION        │
   │  contrôle · mémoire ·   │ (futur) │  DE CONNAISSANCE             │
   │  exploration · Jachère  │         │  ESMM mûr · attestations 5D ·│
   └─────────────────────────┘         │  SQLite · gouvernance GitHub  │
              ▲                        └──────────────┬───────────────┘
              │ pont (futur)                          │ epp_adapter (stub gelé)
   ┌──────────┴──────────────────────────────────────▼───────────────┐
   │  Origami_Transformer (Triptique/Origa_Tranf_Test)               │
   │  L'INSTRUMENT MÉTROLOGIQUE — géométrie de Fisher par couche     │
   │  série v4–v7 close ; v7 HF_DÉMENTI 0/6                         │
   │  pont Fisher gelé : non défendable comme signal épistémique     │
   └─────────────────────────────────────────────────────────────────┘
```

## Les trois règles (décision du 2026-07-18)

1. **Indépendance stricte.** Chaque organe fonctionne SANS les autres. Pas de
   fusion : les objectifs diffèrent (Lyra = intériorité et modulation ;
   EPP = attestation vérifiable de connaissance ; Origa = mesure instrumentale).
   `lyra_reborn` garde donc son ESMM interne compact — EPP_Verdict n'est pas une
   dépendance, c'est un organe.

2. **Le pont est un contrat mince, pas un couplage.** Un pont = un adaptateur
   dans `bridges/` (à naître), qui traduit entre les vocabulaires des deux
   organes. Il peut manquer sans casser l'hôte.

3. **Un pont ne se dégèle que sur validation** — le patron historique
   `epp_adapter.py` d'Origa rend cette règle exécutable : le stub **lève une
   erreur à l'import** tant que ses conditions ne sont pas remplies. La v5 les
   avait provisoirement satisfaites ; les contrôles v6–v7 ont invalidé l'usage
   d'ingénierie visé. « EPP consomme un instrument validé. Jamais l'inverse. »
   Aucun pont de complaisance : un organe non validé ne nourrit pas les autres.

## Ce que chaque pont pourrait porter (esquisse, PAS un engagement)

- **lyra_reborn ↔ EPP_Verdict** : Lyra soumet ses triplets consensuels (P4) à
  l'attestation ; EPP renvoie des attestations = mémoire à haute confiance
  (strate au-dessus de la pouponnière ?). À dessiner quand Simon ouvrira le
  chantier. D'ici là : récolte passive des idées d'EPP éprouvées (fingerprints
  Jaro-Winkler en cascade avant embeddings ; groupes de synonymes de relations ;
  track-record/tiers de `post_crystallization` → écologie mémorielle).
- **Origa → lyra_reborn** : **GELÉ DÉFINITIVEMENT POUR LA SÉRIE v4–v7
  (2026-07-26).** v5 avait trouvé une séparabilité brute (`HC_CONFIRMÉ`, 3/4),
  mais v6 a retiré sa spécificité géométrique et v7 a rendu `HF_DÉMENTI` 0/6.
  La géométrie de Fisher actuelle n'est donc pas importée comme signal P2.
  Cela n'affirme pas qu'aucune géométrie épistémique ne puisse exister ; cela
  clôt ce pont-ci avec cet instrument-ci.
- **Origa → EPP_Verdict** : **GELÉ pour la même raison.** Le stub historique
  et ses preuves restent des artefacts ; ils ne constituent plus une voie
  d'intégration active. Une éventuelle étude future repartirait comme projet
  indépendant, sous un nouveau pré-enregistrement, sans réactivation tacite.

## Leçon méthodologique importée d'Origa

La discipline d'Origa (pré-enregistrement, seuils gelés AVANT données, négatifs
publiables, « toute exclusion exige un pré-enregistrement nouveau, jamais
rétroactif ») est l'application la plus rigoureuse de notre charte §4 observée
dans tout l'écosystème. `docs/METRIQUES_SONGE.md` suivra exactement ce
protocole à son gel.
