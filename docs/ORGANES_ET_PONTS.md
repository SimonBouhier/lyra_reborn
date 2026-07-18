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
   └─────────────────────────┘         │  fingerprints · Solana       │
              ▲                        └──────────────┬───────────────┘
              │ pont (futur)                          │ epp_adapter (stub gelé)
   ┌──────────┴──────────────────────────────────────▼───────────────┐
   │  Origami_Transformer (Work_in_Progress/Origa_Tranf_Test)        │
   │  L'INSTRUMENT MÉTROLOGIQUE — géométrie de Fisher par couche     │
   │  v4 : baseline (négatif publiable ; compression finale 4/4)     │
   │  v5 (H-C, pré-enregistrée) : signature géométrique de la        │
   │  CONTESTATION épistémique                                       │
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

3. **Un pont ne se dégèle que sur validation** — le patron `epp_adapter.py`
   d'Origa est LE modèle canonique : le stub **lève une erreur à l'import**
   tant que ses conditions de dégel (pré-enregistrées, committées) ne sont pas
   remplies. « EPP consomme un instrument validé. Jamais l'inverse. » Aucun
   pont de complaisance : un organe non validé ne nourrit pas les autres.

## Ce que chaque pont pourrait porter (esquisse, PAS un engagement)

- **lyra_reborn ↔ EPP_Verdict** : Lyra soumet ses triplets consensuels (P4) à
  l'attestation ; EPP renvoie des attestations = mémoire à haute confiance
  (strate au-dessus de la pouponnière ?). À dessiner quand Simon ouvrira le
  chantier. D'ici là : récolte passive des idées d'EPP éprouvées (fingerprints
  Jaro-Winkler en cascade avant embeddings ; groupes de synonymes de relations ;
  track-record/tiers de `post_crystallization` → écologie mémorielle).
- **Origa → lyra_reborn** : si H-C (v5) confirme, la géométrie de Fisher
  devient un SIGNAL ÉPISTÉMIQUE RÉEL pour le pont P2 (une « tension » fondée
  instrumentalement — le successeur légitime de la topologie κ/ρ abandonnée).
  Condition de dégel : verdict v5 `H-C_CONFIRMÉ` aux seuils gelés.
- **Origa → EPP_Verdict** : déjà spécifié côté Origa (`epp_adapter.py`, gelé).

## Leçon méthodologique importée d'Origa

La discipline d'Origa (pré-enregistrement, seuils gelés AVANT données, négatifs
publiables, « toute exclusion exige un pré-enregistrement nouveau, jamais
rétroactif ») est l'application la plus rigoureuse de notre charte §4 observée
dans tout l'écosystème. `docs/METRIQUES_SONGE.md` suivra exactement ce
protocole à son gel.
