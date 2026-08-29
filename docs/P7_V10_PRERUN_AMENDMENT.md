# P7 V10 — amendement de portée avant run

**Date :** 2026-08-29
**Moment :** après gel V10 (`bc8497f6bb083ff2c27632ded784e13ea264cc5d`),
avant tout verrou, tout appel et toute lecture de corpus
**Origine :** observation de Simon Bouhier à la relecture du gel

## Nature

Cet amendement ne modifie **aucun** seuil, contrat, prompt, fixture, modèle,
paramètre, dénominateur ni porte de `PREREGISTRATION_v10.md`. Le design gelé
est intact. Il borne uniquement la **portée des énoncés** que les verdicts
V10 pourront soutenir, et lève une ambiguïté de présentation. Il lie la
rédaction de la note de résultats V10, quelle qu'en soit l'issue.

## 1. Portée épistémique de l'instrument

La faiblesse centrale de V10 n'est pas statistique mais épistémique :
`qwen3.8:27b` ne mesure pas directement la qualité éditoriale ; il mesure
**la préférence de `qwen3.8:27b` sous un contrat déterminé**.

Un résultat positif pourra donc soutenir :

> « La politique adaptative produit un avantage robuste **selon cet
> instrument gelé** (juge unique qualifié, contrat réduit, portes C0–C12). »

Il ne pourra **pas** établir :

> « Lyra prend objectivement de meilleures décisions éditoriales » ;

ni :

> « des humains préféreraient systématiquement ses trajectoires ».

La note de résultats V10 devra reprendre cette distinction en propres termes,
au même titre que la mention « juge unique — indépendance inter-famille non
disponible ». Le même bornage vaut symétriquement pour un résultat négatif :
il établirait l'absence d'avantage *selon cet instrument*, pas l'inutilité de
la politique.

Une validation à ancrage humain de l'instrument (accord entre le juge gelé et
un jugement humain aveugle sur un échantillon) reste possible comme
**expérience future indépendante, sous son propre gel** — jamais comme
extension rétroactive de V10.

## 2. Clarification : répétitions et inversion

La formule « répétitions et inversion comme contrôles d'auto-cohérence »
(règle méta §3, reprise dans le gel V10) se répartit ainsi, sans changement
du design :

- les **trois répétitions** appartiennent à **Q0 uniquement** ;
- pendant la campagne (calibration et tenu), chaque paire reçoit **une fois
  chaque orientation** — deux appels juge par paire.

Cette structure détecte une incohérence entre orientations ; elle ne sépare
**pas complètement** le biais de position de la variabilité stochastique
(température 0 ne garantissant pas à elle seule un déterminisme parfait du
runtime). Les portes C3 (résolution : stable après inversion et non-TIE),
C4 (stabilité ≥ 75 %) et C12 (validité ≥ 95 %) protègent le verdict contre
les conséquences pratiques de cette limite. C'est une **limite
d'interprétation, pas un motif d'annulation** : O24 publiera les taux par
orientation pour la rendre inspectable.

## Compatibilité avec le gel

Aucun run n'a été lancé, aucun verrou créé, aucun corpus lu. La clause
anti-confirmation de V10 interdit d'ajuster l'instrument après l'ouverture de
Q0 ; le présent amendement, antérieur à toute ouverture et sans effet sur
l'instrument, restreint la force des revendications au lieu de l'étendre.
Toute extension future de portée exigerait, elle, une expérience nouvelle
sous son propre gel.
