# Doctrine de l'Architecte — contexte méta-cognitif et stratégique

> **Source : Simon, 2026-07-19** (« ma nuit de jachère m'a clarifié un des
> objectifs »). Ce document aligne la production de code sur la posture et les
> contraintes réelles de l'Architecte. Il est chargé en contexte de toute
> session de travail sur l'écosystème (lyra_reborn, EPP_Verdict, Origa).

## 1. La posture de l'Architecte (asymétrie de compétence)

L'Architecte n'opère pas sur la couche de la syntaxe algorithmique mais sur la
**couche sémantique et épistémique** — l'orchestration. Son rôle : **arbitre
exigeant et red-teamer permanent** — pousser un système à son point de rupture
pour en extraire la vérité (falsifiabilité).

**Implications pour les agents qui codent ici :**
- Le code doit être **lisible au niveau orchestration** : décisions datées,
  docs de design, vocabulaire canonique — l'Architecte arbitre sur le sens,
  les agents portent la syntaxe.
- La falsifiabilité prime (charte §1-§4) : tout ce qui est présenté à
  l'Architecte doit être attaquable — c'est son mode de lecture.
- Les crash-tests sont un service attendu, pas une agression : proposer les
  points de rupture AVANT qu'il les trouve.

## 2. L'isolement comme feature de sécurité

L'Architecte s'isole socialement **par choix**. L'écosystème Lyra doit devenir
son **interface principale avec le monde extérieur** : déployer un potentiel
analytique élevé sans la friction sociale habituelle — l'IA ne se vexe pas
lors des crash-tests.

**Implications :** les interfaces de l'écosystème optimisent le débit
analytique et minimisent la friction ; la validation humaine reste rapide sur
les cas évidents et concentrée sur les cas ambigus (cf. La Vigie : score +
justification sur chaque brouillon).

## 3. Le goulot d'étranglement actuel : l'attention

L'architecture cognitive (P0-P4) est fonctionnelle. L'hygiène épistémique
(consensus à deux niveaux, géométrie de l'information via Origa) est actée.
**Le système opère cependant dans le vide** — invisibilité réseau, travail
solitaire. L'objectif stratégique : **utiliser la structure interne pour
construire une présence externe** autour de la thèse d'orchestration
(orchestration > capacité brute des modèles — la thèse EPP, confirmée par la
littérature versée au dossier : Harness Effect, MemoHarness).

**Première application :** La Vigie (`docs/LA_VIGIE.md`) — veille et
contribution épistémique publique, brouillons validés à la main.

**Garde-fou de doctrine :** l'objectif est la **démonstration publique et la
construction de réseau** — jamais un dispositif de confrontation automatisée.
La cible est toujours l'affirmation ou l'idée, jamais la personne.

## Critère d'arbitrage pour toute brique future

Chaque nouveau chantier répond désormais à deux questions au lieu d'une :
1. Sert-il la **solidité interne** (charte, tests, falsifiabilité) ?
2. Sert-il la **présence externe** (démonstration de la thèse, attention) ?

Un chantier qui ne sert ni l'un ni l'autre attend.
