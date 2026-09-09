# Organes et ponts — doctrine d'architecture inter-projets

> **Lecture au 9 septembre 2026 :** cette carte conserve les décisions et
> constats inter-projets datés ci-dessous. Le lot d'alignement ne réexamine pas
> EPP ni Origami et n'ouvre aucun pont. Pour Lyra aujourd'hui, consulter
> [ETAT_ACTUEL](ETAT_ACTUEL.md) et le [plan actif](PLAN_EDIFICATION.md).

> **État vérifié le 2026-09-05 :** EPP est local et personnel, sans publication
> blockchain (ADR-022). Le pont d'attestation reste à valider. Le sidecar Vigie
> existe sur une branche EPP distincte, absent de `main` à `84879d2` ; les
> campagnes historiques conservent leurs propres références gelées.

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
              │ pont clos v4–v7                       │ epp_adapter (stub gelé)
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

**Déclinaison interne à Lyra — 7 septembre 2026 :** la
[note de cloisonnement Jachère](NOTE_ARCHITECTURE_JACHERE_CLOISONNEMENT_2026-09-07.md)
applique cette doctrine à la consolidation, à la recombinaison et à la
Pouponnière : fonctions autonomes, propositions séparées, admission et retrait
traçables. Elle n'ouvre aucun des ponts inter-projets ci-dessous.

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

La discipline historique citée d'Origa (pré-enregistrement, seuils gelés avant
données, négatifs publiables, exclusions non rétroactives) fournit un précédent
de méthode pour la charte §4. Le superlatif antérieur ne reposait pas sur une
comparaison de l'écosystème ; il est retiré de cette présentation. Les
[métriques du Songe](METRIQUES_SONGE.md) restent candidates à réviser : leur
futur protocole devra répondre à une question propre, avec témoins et budget,
sans reprendre mécaniquement celui d'un autre instrument.
