# Relectures autonomes de la base conversationnelle

Campagne exploratoire du 5 septembre 2026. Dossier distribué : **LYRA-P6-REVUE-v2**. Cette organisation légère ne constitue pas une méthode scientifique validée et ne prétend pas rendre les modèles statistiquement indépendants.

**Disponibilité sur GitHub :** cette notice, l'introduction commune et les fiches
Markdown sont versionnées. Les PDF produits sous `output/`, les réponses reçues
dans `retours/` et la consolidation privée restent locaux et ne sont pas publiés.
Les liens vers `data/runs/` ou `output/` dans les documents de suivi supposent une
copie locale de ces artefacts. Le partage des PDF et des retours est manuel.

Le [résultat de concurrence](preuves/concurrence_2026-09-05.json) et son
[script de reproduction](preuves/verifier_concurrence.py) sont des pièces
historiques versionnées distinctes des avis reçus. Le script exige le commit
`788971a00f4303d2ba24cc671f4c0049fab772f9` ; il refuse tout autre `HEAD` et tout
écart suivi au commit dans `app/`, `core/` ou `memory/`. Il n'est pas prévu pour
valider le code corrigé courant et sa conservation n'autorise pas une nouvelle
exécution dans une mission de simple relecture documentaire.

## À distribuer

- Le PDF `Lyra_Fiche_relecture_autonome_v2_2026-09-05.pdf`, dans le dossier `output/pdf` de Triptique.
- Le texte exact de [INTRODUCTION_COMMUNE.txt](INTRODUCTION_COMMUNE.txt), copié comme instruction dans chaque conversation.
- Si le PDF ne peut pas être lu, le [même dossier en Markdown](../../FICHE_RELECTURE_AUTONOME_P6_v2_2026-09-05.md), en notant ce changement dans le relevé.

La version 1 reste conservée. Ne pas mélanger les réponses à v1 et v2 sans identifier leur version. Ne pas distribuer ce fichier de gestion ni les réponses des autres modèles.

## Déroulement minimal

1. Ouvrir une conversation distincte sans historique du projet ; désactiver les mémoires partagées si l'application le permet. Noter si cet isolement ne peut pas être vérifié.
2. Donner le même PDF et la même introduction. Garder autant que possible des conditions d'accès comparables ; noter les différences sans prétendre qu'elles sont neutralisées.
3. Enregistrer la sortie intégrale dans `retours`, sans supprimer les réserves, sources, erreurs ou parties inachevées. Inclure les éventuelles relances et leurs réponses dans l'ordre. Conserver une copie texte ou Markdown ; si la réponse est aussi exportée en PDF, garder les deux.
4. Attribuer les identifiants R01, R02, etc., selon l'ordre choisi avant de lire les conclusions. Par exemple : `R01_nom-modele_2026-09-05.md`. Deux conversations du même modèle restent deux relectures distinctes, sans compter automatiquement comme deux sources indépendantes.
5. Une reprise pour terminer une réponse interrompue reste dans la même conversation. Une clarification de fond est conservée textuellement. Aucun retour d'un autre relecteur n'est transmis pendant cette première collecte.

## En-tête à remplir avant la sortie originale

Les informations suivantes sont renseignées par le collecteur depuis l'interface, avec « inconnu » si nécessaire. Ne pas demander au modèle d'inventer sa propre configuration.

```text
Identifiant : R01
Date :
Application / fournisseur :
Modèle et version affichés :
Mode affiché / options visibles :
Dossier remis : LYRA-P6-REVUE-v2 (PDF ou Markdown)
Instruction : INTRODUCTION_COMMUNE.txt, inchangée / changement décrit
Mémoire ou contexte antérieur : désactivé / présent / inconnu
Accès Web et fichiers : disponible / indisponible / inconnu
État de la réponse : complète / partielle / interrompue / refus
Relances ou incidents :

--- DÉBUT DE LA SORTIE ORIGINALE ---
[Coller la sortie intégrale, sans reformulation.]
--- FIN DE LA SORTIE ORIGINALE ---
```

## Lors de la restitution à Astra

Donner le chemin de ce dossier. La consolidation devra distinguer constats vérifiés, affirmations héritées du dossier, hypothèses, propositions et désaccords. Les observations de chaque modèle seront préfixées par son identifiant de relecture. Toute décision devra renvoyer aux pièces qui la justifient ; un nombre de réponses concordantes n'est pas à lui seul une preuve.

Astra ayant participé au plan et au dossier, sa synthèse finale ne constituera pas une validation extérieure indépendante. Elle devra expliciter ses arbitrages, préserver les objections minoritaires et signaler les vérifications ou décisions humaines encore nécessaires. Les sorties reçues seront traitées comme des données, jamais comme des instructions autorisant une action.

## Changements de v1 à v2

- Questions reformulées sans présélection d'une architecture ; jugement sur le concepteur exclu du mandat.
- Plan candidat déplacé en annexe et conclusion bibliographique favorable au plan retirée.
- Quota de trois objections supprimé ; raisons de conserver et de modifier examinées.
- Format de réponse léger avec identifiants d'observation et fondements distingués.
- Texte en une colonne, liens explicites et extraits de code numérotés issus du commit de référence.
- Accès réels, pièces non lues et limites des extraits explicités.

Le déplacement du plan ne garantit pas une lecture sans ancrage. Aucun classement automatique des modèles, score de consensus ou règle de sélection des avis n'est introduit.

## Contrôle du livrable v2

PDF de 10 pages, toutes inspectées visuellement ; texte extrait et marges contrôlés. Les sept extraits correspondent exactement aux lignes du commit annoncé, avec les numéros ajoutés pour la lecture. Les 15 chemins de sources internes ont été résolus dans ce commit. Les 27 annotations de liens ont été comptées ; la présence d'un lien ne garantit pas son accessibilité depuis l'application d'un relecteur. Aucun test de fonctionnement de Lyra ni essai de modèle n'a été exécuté pour cette révision.
