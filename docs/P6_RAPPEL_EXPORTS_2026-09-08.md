# Export autonome de relecture P6

Date : 2026-09-08. Périmètre : outil de préparation documentaire interne.
Aucune relecture externe indépendante n'est exécutée ou revendiquée par cet outil.
Aucun appel à un modèle, envoi, publication, nouvelle mesure ou accès à P7.

## Entrée explicite et deux étapes

`experiments.p6_recall.packets.build_packet(destination, files, stage="protocol",
context_markdown=None)` reçoit une liste blanche explicite : un dictionnaire de
noms relatifs dans l'archive vers des fichiers individuels. Le nom `destination`
désigne **un nouveau dossier**, avec un parent déjà existant. L'outil crée ce
dossier, une archive voisine `<destination>.zip` et son empreinte
`<destination>.zip.sha256`. La valeur retournée est le chemin absolu du ZIP.

Les deux étapes sont distinctes :

- `protocol` : relecture du plan avant ses résultats ; par exemple un
  `PLAN_EXPLORATOIRE_v1.md`, du corpus de développement autorisé, des templates,
  le code du scoreur et les contrats nécessaires. Le nom « protocole » de cette
  étape ne transforme pas un plan exploratoire en préenregistrement confirmatoire.
- `results` : relecture des résultats bruts explicitement sélectionnés et de
  leur méthode, sans synthèse de l'auteur. Les traces expérimentales doivent
  figurer dans la liste blanche pour être présentes ; la trace de fabrication
  de l'archive ne peut pas les remplacer.

La même introduction et les mêmes rubriques sont données à chaque destinataire
d'une étape. Les rapports Markdown et JSON sont renvoyés manuellement et
séparément ; aucun rapport reçu n'est réinjecté dans les paquets des autres.

## Exemple d'appel après gel des pièces

L'exemple suivant illustre l'API. Il n'a pas été exécuté pour fabriquer un paquet
final ; la sélection réelle doit être remplacée par les pièces figées et relues.

```python
from pathlib import Path
from experiments.p6_recall.packets import build_packet

archive = build_packet(
    Path("exports/p6_protocol_v1"),  # exports/ existe ; p6_protocol_v1 n'existe pas
    files={
        "PLAN_EXPLORATOIRE_v1.md": Path("pieces_figees/PLAN_EXPLORATOIRE_v1.md"),
        "experiments/p6_recall/corpus.py": Path("experiments/p6_recall/corpus.py"),
    },
    stage="protocol",
    context_markdown="## Définitions du dossier\n\nDéfinitions neutres des pièces jointes.\n",
)
```

Le contexte transmis s'ajoute à une explication commune autonome des rappels,
des corrections et de la différence entre lecture documentaire et exécution.
Il ne doit pas contenir de conclusion locale ni de réponse d'un autre relecteur.
Les fichiers sources sont copiés sans modification dans `pieces/`.

## Contenu du paquet

| Fichier | Fonction |
| --- | --- |
| `README_RELECTURE.md` | Objet neutre, phase, mandat documentaire, exclusions, inventaire |
| `CONTEXTE_AUTONOME.md` | Vocabulaire et contexte neutre, plus contexte fourni |
| `FORMULAIRE_RELECTURE.md` | Rapport demandé en sept rubriques |
| `FORMULAIRE_RELECTURE.json` | Formulaire structuré vierge, avec exemples de champs distincts des constats |
| `FICHE_RELECTURE.pdf` | Introduction, contexte et formulaire lisibles sans outil de développement |
| `PROTOCOLE_COMPLET.pdf` | Plan complet dérivé du Markdown sélectionné via `protocol_alias` |
| `pieces/...` | Uniquement les fichiers explicitement autorisés |
| `export_trace.jsonl` | Trace de fabrication, déclarée non expérimentale, empreinte de chaque pièce |
| `manifest.json` | Version, étape, absence de relecture effectuée, provenance, tailles et SHA256 |
| `manifest.sha256` | SHA256 de tous les autres fichiers, y compris le manifeste JSON |

Le manifeste SHA256 ne se hache pas lui-même. L'empreinte détachée du ZIP porte
sur ses octets complets. Les métadonnées de date ZIP sont fixées à l'époque ZIP
pour la stabilité ; elles ne sont pas une date d'exécution expérimentale.

Le formulaire demande identité/version, rôle documentaire ou exécution
autorisée, pièces réellement lues, environnement, commandes, outils disponibles
et utilisés, autorisations reçues, écarts de mandat, constats, citations de
preuves, hypothèses alternatives, limites, propositions, verdict et portée.
Les constats et le verdict sont initialement vides. Les exemples de structure
JSON ne sont pas des observations préremplies.

## Exclusions et limites du filtrage

Aucun dossier n'est parcouru récursivement. Les fichiers voisins non listés
ne sont pas inclus. Les chemins absolus dans l'archive, les traversées `..`,
les séparateurs Windows, les noms réservés, les collisions de casse et les
conflits fichier/dossier sont refusés. Les liens symboliques sources sont refusés.
Les sources doivent être des fichiers individuels non vides, sauf les
initialisateurs Python `__init__.py` vides, conservés pour la résolution des packages.

Les chemins manifestement nommés P7, utilisateur/user/users, confirmation,
holdout, synthèse/conclusions et retours de relecteurs sont refusés côté source
et alias. Le conteneur système Windows `C:\Users` est reconnu comme tel ; un
dossier `users/` dans le projet reste exclu. Les bases `.db`, `.sqlite` et
`.sqlite3` sont exclues. L'étape protocole refuse en plus les chemins nommés
résultats/results/outcomes. Les dossiers de confirmation sont exclus même si
une source reçoit un alias neutre. Des traces de cas déjà consommés peuvent
être sélectionnées dans un dossier de runs autorisé pour la phase résultats.

Ce contrôle de noms n'analyse pas le sens des pièces. La liste blanche doit
donc avoir été relue pour exclure toute synthèse ou observation orientante
cachée dans un nom neutre, tout retour reçu et toute donnée utilisateur.
En particulier, le guide P6 contenant les résultats et
`scripts/check_p6_chat.py` contenant une observation orientante ne font pas
partie des pièces à sélectionner pour la relecture de méthode.

Les noms, le code et la configuration peuvent révéler des facteurs ou familles.
L'outil ne revendique pas d'anonymisation forte ou d'aveuglement garanti.
Il ne transforme pas un contrôle technique interne en avis externe indépendant.

## PDF sans installation

`render_markdown_pdf(markdown, destination)` est une fonction publique pour
rendre aussi un Markdown de protocole transmis séparément. Elle gère titres,
paragraphes, listes, blocs de code et tableaux Markdown simples ; le fichier
Markdown original demeure la source complète. Les images, liens interactifs
et extensions Markdown avancées ne sont pas interprétés.

Le rendu emploie ReportLab installé dans l'interpréteur courant, sinon le runtime
Python Codex déjà fourni. `P6_PACKET_PDF_PYTHON` permet de désigner un autre
interpréteur existant contenant ReportLab. Aucune dépendance n'est installée.
L'environnement du projet reste inchangé. Ici, le runtime fourni contient
ReportLab 4.4.9 et Poppler ; le pont depuis le venv du projet a été exercé.

Un dossier, ZIP, empreinte ou PDF existant n'est jamais remplacé. Une erreur
après création peut laisser un dossier incomplet pour inspection ; il faut
employer une nouvelle destination pour la reprise. L'absence de ZIP et
d'empreinte détachée interdit de considérer ce dossier comme un export terminé.

## Vérification effectuée sur des fixtures techniques

Commande : `.venv/Scripts/python.exe -m pytest tests/test_p6_recall_packets.py -q`.
Les contrôles ciblent l'intégrité ZIP, toutes les empreintes, les fichiers
non vides, le refus d'écrasement, les chemins dangereux, les exclusions, la
non-inclusion des fichiers voisins et les champs de rapport vierges.
Ils n'établissent aucun résultat expérimental sur les rappels P6.

Le PDF de fixture comporte trois pages. Extraction pypdf vérifiée pour les
accents et la fin du formulaire ; trois pages rendues avec Poppler et inspectées
visuellement : marges, numéros de page, textes et titres lisibles, sans débordement.
Les archives des tests sont des fixtures temporaires ; aucun ZIP final n'est
fabriqué par le simple ajout de cet outil.

## Exporteur des pièces figées et portabilité

`scripts/export_p6_recall_packets.py` applique une recette fermée aux deux étapes.
Il conserve les chemins du dépôt sous `pieces/`, qui devient la racine de travail
après extraction. Les imports du corpus et du runner n'appellent aucun modèle.
La recette inclut leurs dépendances `app/context.py`, `app/dialogue.py`,
`app/chat_backend.py`, `core/llm.py`, les initialisateurs, les scripts P6 et les
tests déterministes. Les sceaux et les sources du manifeste de campagne sont
vérifiés avant export. Aucune source de mesure n'est modifiée.

```powershell
# Parent output/p6-recall/ existant ; destination neuve.
.venv/Scripts/python.exe -B -X utf8 scripts/export_p6_recall_packets.py `
  --stage protocol --destination output/p6-recall/01_methode_v1
# Invocation séparée, seulement lorsque les résultats sont autorisés à l'export.
.venv/Scripts/python.exe -B -X utf8 scripts/export_p6_recall_packets.py `
  --stage results --destination output/p6-recall/02_resultats_v1 --raw-jsonl
```

La méthode inclut le plan scellé complet en Markdown et PDF, les sources et les
métadonnées préparées `cases`, `conditions`, `jobs`, `models`, `manifest` ; elle
ne lit pas les dossiers de qualification et de résultats. La phase résultats
ajoute les pièces de qualification nommées par leur manifeste, les réservations
et résultats de chaque job planifié, leurs sidecars présents et les fichiers
de progression du runner. Les analyses agrégées et les avis ne sont pas sélectionnés.

`PORTABILITE.md` décrit les commandes documentaires et distingue tests, analyse
locale et génération autorisée. `SOURCES_EXPORT.json` décrit les empreintes et
l'origine des pièces. La copie scellée du plan dans le dossier de campagne est
incluse avec ses chemins relatifs ; le lecteur n'a pas besoin du chemin absolu
du poste d'origine. Les imports et les tests ciblés depuis `pieces/` n'exigent
pas une installation du projet complet.

La phase résultats produit aussi des PDF du canal final intégral, regroupés par
modèle puis par volumes déterministes de 1 600 traces : quatre PDF de sorties
pour les quatre configurations de ce plan complet. Chaque entrée compacte cite
identifiant de job, cas, condition, graine et statut technique ; le modèle est
celui du volume. L'identifiant renvoie au JSON exact, dont le SHA256 figure au
manifeste. Chaque transcription existe aussi en Markdown. Le sommaire
énumère les volumes sans interpréter les réponses. `--raw-jsonl` copie en plus les
objets JSON complets sélectionnés, sans score ni analyse partielle. Les corps HTTP
exacts restent dans les fichiers JSON originaux. Le formulaire exige de déclarer
les documents réellement lus et les limites de contexte ; une lecture PDF seule
ne vaut pas inspection intégrale du code ou des traces.

`REFERENCE_CORPUS.md` et son PDF sont dérivés uniquement des JSON préparés :
les 24 cas avec question, valeurs ancienne/actuelle et rôle, les conditions,
puis les messages exacts des 16 cellules et des témoins du premier cas avec
leur vérité déclarée. Ce cas est explicitement un exemple déterministe ; aucun
générateur n'est importé ou exécuté et aucune sortie ne choisit les exemples.
Les listes de messages affichent le SYSTEM, les rôles, les frontières et la
consigne de sortie. `jobs.json` conserve exhaustivement tous les stimuli.
