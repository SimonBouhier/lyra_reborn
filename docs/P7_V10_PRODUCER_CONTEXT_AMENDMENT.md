# P7 V10 — amendement : contexte de montage des producteurs

**Date :** 2026-08-29
**Moment :** après Q0 (`Q0_PASSED`, verrou
`p7_v10_q0_bc8497f…lock`, run `p7_v10_q0_20260829T211254.467768Z`), **avant**
tout verrou de calibration, avant le premier appel producteur de la campagne
et avant toute lecture de contenu du corpus
**Origine :** arrêt du runner à la preuve GPU de la calibration —
`granite3.3:latest is not fully loaded on GPU: size=27698082609,
size_vram=22765916651`

## Nature

Cet amendement ne modifie **aucun** seuil, contrat, prompt, fixture, modèle,
digest, graine, dénominateur, observable ni porte de
`PREREGISTRATION_v10.md`. Il **spécifie** un paramètre d'exploitation que la
préinscription n'a jamais fixé — la taille de fenêtre à laquelle les modèles
producteurs sont montés — parce que sa valeur par défaut rend le design
matériellement inexécutable.

## 1. Le fait observé

Ollama 0.32.15 monte un modèle à son contexte **maximum** lorsque la requête
ne demande pas de `num_ctx`. Les producteurs gelés n'en demandent aucun : le
mapping V8 (`core/knobs.py`) ne produit que `temperature`, `top_p`,
`repeat_penalty` et `num_predict`.

| modèle | paramètres | contexte max | conséquence |
|---|---|---|---|
| `mistral:latest` | 7,2 B | 32 768 | tient |
| `gemma3:latest` | 4,3 B | 131 072 | à risque |
| `granite3.3:latest` | 8,2 B | 131 072 | **27,70 Go, ne tient pas** |
| `qwen3.8:27b` (juge) | 27,3 B | 262 144 | monté explicitement à 32 768 |

Sur une carte de 24 Go, `granite3.3:latest` monté à 131 072 pèse 27,70 Go
dont 22,77 Go seulement en VRAM : ~4,9 Go débordent en RAM. La précondition
`size_vram == size` du banc A, reconduite par V10, refuse — correctement — et
le runner s'arrête **avant** le verrou de calibration, sans consommer un seul
appel. Le juge échappait au problème pour la seule raison qu'il est monté
explicitement à 32 768.

## 2. Ce qui est spécifié

Les trois producteurs sont montés à un contexte de **32 768 tokens**, fixé au
niveau du serveur Ollama (`OLLAMA_CONTEXT_LENGTH=32768`), pas dans les
requêtes.

Conséquence voulue : **aucun octet des payloads producteurs ne change.** Le
runner continue de n'envoyer aucun `num_ctx` ; les requêtes restent
exactement celles que le design gelé aurait émises. Seule l'allocation
mémoire du serveur est contrainte.

La valeur 32 768 n'est pas arbitraire : c'est le contexte maximum de
`mistral:latest`, donc la seule valeur que les quatre modèles de la campagne
acceptent tous, et celle à laquelle le juge est déjà monté.

Le runner vérifie désormais ce contexte pour chaque producteur, avec la même
précondition que pour le juge et au même endroit — avant le verrou de phase.
Un serveur mal réglé arrête donc la campagne sans rien consommer, au lieu de
la faire tourner sur une allocation non spécifiée. La valeur observée entre
au manifeste de chaque phase.

## 3. Pourquoi cela n'altère pas la mesure

Le contexte de montage fixe la taille du cache d'attention et le point de
troncature ; il ne change pas ce que le modèle calcule sur un prompt qui y
tient.

Le plus long squelette de prompt T3 sur les 72 cas (12 calibration + 60 tenu)
fait 4 237 caractères, soit ~1 211 tokens. Avec deux analyses antérieures
bornées à 768 tokens chacune par `num_predict` et la génération finale, le
pire cas demande **~3 500 tokens** de fenêtre. À 32 768, la marge est de
**9,3×** : aucune troncature n'est possible, sur aucun cas.

Le réglage s'applique identiquement aux deux bras (`ADAPTIVE` et
`STATIC_BEST` partagent le même client producteur par cas) et aux trois
producteurs. Il ne peut favoriser ni un bras, ni un modèle, ni une source.

Enfin, et c'est décisif pour la clause anti-confirmation : **aucun appel
producteur n'a été émis dans cette campagne.** Q0 ne fait intervenir que le
juge. Il ne s'agit donc pas d'ajuster un paramètre après une mesure, mais de
compléter une spécification d'exploitation avant l'ouverture de la première
phase qui en dépend.

## 4. Reprise de la chaîne après Q0

La commande unique doit repartir sans rejouer Q0, dont le verrou est posé et
le résultat acquis. La règle appliquée, vérifiable, est :

- **pas de verrou Q0** → Q0 est exécutée normalement ;
- **verrou Q0 + résumé `Q0_PASSED` sous ce gel** → Q0 n'est **pas rejouée** ;
  son résultat est repris, et le `run_id` et le SHA-256 de son journal sont
  inscrits au manifeste de la phase suivante ;
- **verrou Q0 sans résumé passant** → la commande **refuse** de continuer : la
  phase a été consommée sans franchir sa porte, et le gel interdit une
  seconde tentative.

Aucune phase n'est donc exécutée deux fois : Q0 n'est pas rejouée, et la
calibration s'ouvrira pour la première fois. La condition gelée « Q0 puis,
seulement en cas de succès, calibration puis tenu » est préservée : elle est
évaluée sur le résultat réel de Q0, simplement lu au lieu d'être reproduit.

## Compatibilité avec le gel

`PREREGISTRATION_v10.md` énumère ce qui annule V10 et exige V11 : une
correction qui dépasse la transposition juge unique, change le contrat
réduit, change le canal `response`, autorise une relance, ou touche Q0, Q1 ou
C0–C12. Le présent amendement ne fait aucune de ces choses.

- l'instrument de jugement est inchangé — juge, contrat réduit, transport,
  ordre des appels, deux orientations par paire ;
- Q0 est close et passée ; ses 18 appels ne sont ni rejoués, ni réinterprétés,
  ni complétés ;
- Q1 et C0–C12 gardent leurs seuils, leurs dénominateurs et leur ordre ;
- aucun appel n'est relancé ni réparé : la règle « aucune relance/réparation
  d'appel, aucun retrait de dénominateur » reste entière.

La clause anti-confirmation interdit d'ajuster prompts, fixtures, seuils,
contrats, enums, ordres, modèles et paramètres après l'ouverture de Q0. Le
paramètre fixé ici n'appartient à aucune de ces catégories de design : c'est
une allocation mémoire du serveur, laissée implicite par le gel, sans effet
sur le calcul et sans effet possible sur la direction d'un résultat. Elle est
désormais explicite, contrôlée avant chaque verrou et journalisée.

Si cette lecture devait être jugée trop permissive, la conséquence serait
l'arrêt de V10 après Q0 avec `H10 UNTESTED` — jamais la poursuite de la
campagne sur une allocation non spécifiée.
