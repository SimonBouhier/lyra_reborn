# P6 — journal durable et cycle des demandes

**7 septembre 2026 — étape 2 du [contrat P6](CONTRAT_USAGE_P6_v0_2026-09-07.md).**
Modifications locales sur la base Git `788971a`, non commitées et non publiées.
Le présent document décrit le code livré et ses limites. Il ne constate pas
l'achèvement du contrat conversationnel complet.

**Note de publication :** les mentions de code non commité ou non publié
décrivent le 7 septembre, date de cette réalisation. Les rapports liés sous
`data/runs/` et les exports sous `output/` restent locaux, ignorés par Git et
absents de GitHub. Les commandes et tests sont versionnés ; les liens des
preuves datées supposent une copie locale de ces artefacts.

**Vérification de développement : 57 tests Python et 7 tests JavaScript réussis.**
**Rejeu par Simon dans son PowerShell confirmé le 7 septembre à 22 h 29 :
57 tests Python et 7 tests JavaScript réussis ; 19 empreintes concordantes.**
Clients factices, bases temporaires et DOM simulé. Aucune base utilisateur migrée, aucun modèle
réel appelé, aucun serveur de production redémarré pendant cette réalisation.

> **Document d'étape historique, complété le 8 septembre.** Le serveur courant
> attend désormais SQLite v3. Utiliser le [guide du dialogue](P6_CONTEXTE_CORRECTIONS_RAPPELS_2026-09-08.md)
> pour le comportement courant, les contrôles, la migration v1/v2→v3 et les limites
> du contrôle réel Gemma. Les sections ci-dessous décrivent l'étape v2 ; leur
> migration seule ne suffit plus à démarrer le serveur courant. Les anciens
> rapports et la correspondance des empreintes restent des preuves datées.

## 1. Comportement disponible

Le navigateur attribue une identité à chaque envoi et en garde une copie locale
avant le premier appel réseau. Le serveur enregistre le texte exact, l'intention
et la conversation avant de lancer une génération. L'accusé « Demande
enregistrée » correspond à cette validation durable.

Une fois le calcul terminé, la réponse destinée à l'affichage et l'état complet
de la conversation sont validés dans la même transaction. Retrouver cette
demande restitue sa réponse enregistrée ; cela ne relance pas le modèle.
Les demandes échouées restent consultables et leurs tentatives sont distinctes.

La page réaffiche le journal de la conversation sélectionnée, par pages de
50 demandes. Les échanges nouveaux restent conservés au-delà des 50 tours de
l'ancien historique de contrôle. « Nouvelle session » change de conversation
sans effacer les précédentes. Une réponse arrivée après ce changement reste
accessible dans « Envois à reprendre ou réponses à retrouver ».

Cette étape conserve le profil actuel de contrôle et de graphe. **Le journal
consultable n'est pas encore l'historique conversationnel envoyé au modèle.**
Le profil fixe de référence, le rappel explicite et les corrections liés à un
passage sont les travaux suivants.

## 2. Identités et transitions

- **Conversation :** identité serveur stable, périmètre de l'état et du journal.
- **Demande :** identité client créée avant tout envoi. Son intention immuable
  contient `texte`, `session` initialement fournie ou `null`, et `voix` booléen.
  La session attribuée par le serveur ne remplace jamais ce `null` dans les
  répétitions du premier envoi : sinon la même demande semblerait avoir changé.
- **Tentative :** numéro croissant dans une demande. Chaque geste de relance
  reçoit aussi une identité client, conservée avant son appel réseau.

| État | Signification | Suite autorisée |
|---|---|---|
| `en_attente` | Demande durable, calcul non démarré | Premier lancement explicite ; la page l'enchaîne après l'accusé d'enregistrement. |
| `en_cours` | Tentative commencée, sans résultat validé | Lecture du statut ; une répétition ne lance pas un second calcul. |
| `echoue` | Tentative finie sans résultat validé | Nouvelle tentative sur un geste explicite de relance. |
| `interrompu` | Tentative sans résultat validé dont le calcul n'est plus actif | Même règle de relance explicite. |
| `termine` | Réponse affichable et état validés ensemble | Relecture uniquement ; résultat immuable pour cette identité. |
| `importe` | Trace d'un ancien tour v1, avec lacunes déclarées | Lecture uniquement, aucune réexécution de cette entrée. |

Même identité et même intention : résultat ou statut existant. Même identité
et intention différente : conflit 409. Même texte sous une identité nouvelle :
nouvelle demande. Répéter une identité de relance déjà utilisée ne crée pas
une tentative supplémentaire, même après un nouvel échec.

Le service garantit **au plus un résultat validé par demande**, dans le périmètre
d'un registre et d'un processus. Il ne promet pas une seule exécution physique
du modèle : après un calcul perdu avant publication, une relance explicite peut
calculer de nouveau. Aucun mécanisme ne décide automatiquement de cette relance.

Une demande en attente ou en cours occupe sa conversation. Après un échec,
un nouvel envoi est possible. Si une demande suivante a déjà été acceptée,
relancer l'ancienne est refusé : cela modifierait rétroactivement le contexte
de la suite. Le message demande alors de créer un nouvel envoi avec ce texte.
La bifurcation d'une conversation n'est pas implémentée.

## 3. Stockage et concurrence

[app/journal.py](../app/journal.py) introduit le format SQLite **v2** :

| Table | Responsabilité |
|---|---|
| `sessions` | Dernier état de contrôle validé ; son contenu JSON reste au contrat v1. |
| `requests` | Identité, intention, ordre dans la conversation, statut et réponse affichable. |
| `attempts` | Identité de relance, état, dates, contexte d'exécution et éventuelle erreur de chaque tentative. |
| `request_events` | Transitions datées : acceptation, démarrage, fin, échec, interruption ou import. |

Les transitions sont réalisées dans des transactions courtes. L'acceptation
d'une première demande enregistre également l'état initial de sa conversation.
La publication réunit état, réponse et transition terminale. Une exception avant
commit ne publie ni nouvel état ni réponse. Une exception après commit conduit
à relire la décision durable ; un résultat déjà validé ne devient pas un échec.
Si cette lecture est impossible, le service signale une issue inconnue et retire
l'objet en mémoire pour imposer une restauration ultérieure.

[app/requests.py](../app/requests.py) réserve l'identité de la demande et celle
de la conversation avant de lire et modifier leur état. La garde issue d'A01
reste détenue jusqu'à la publication ou au retour arrière. Le statut durable
est lisible pendant le calcul. Une autre conversation n'est pas retenue par
cette garde, mais peut rencontrer la contention ordinaire du disque ou du moteur.

**Aucune transaction SQLite n'attend le modèle.** Cette organisation utilise les
transactions et l'API de sauvegarde du module standard Python ; les opérations
d'écriture restent soumises à la coordination des transactions SQLite.
Sources techniques : [Python, sqlite3](https://docs.python.org/3/library/sqlite3.html)
et [SQLite, transactions](https://www.sqlite.org/lang_transaction.html).

À la première utilisation du service après démarrage, les anciennes tentatives
`en_cours` deviennent `interrompu`. Une tentative dont l'écriture d'échec a été
empêchée peut aussi être reconnue comme interrompue dans le même processus,
uniquement lorsqu'aucun calcul vivant ne détient son identité. Une demande
acceptée mais jamais lancée reste `en_attente`.

Le chargeur v1 conserve ses validations ; les contraintes v2 portent notamment
sur les statuts, les identités, les numéros de tentative, l'ordre des demandes,
les références de session et l'unicité d'une demande active par conversation.
Le JSON non fini est refusé. Il ne s'agit pas d'un dispositif général de
réparation d'une base corrompue.

## 4. Fidélité, contexte et configuration

Le journal conserve le texte soumis, y compris ses espaces et retours à la ligne.
Le parcours de génération existant applique `strip` et peut préfixer un résumé
du graphe. Chaque tentative qui atteint le moteur enregistre **avant cet appel**
le prompt réellement transmis, les options, le format de réponse, la politique
`p6_controle_graphe_v1`, le nombre de tours précédents et la configuration client.
Une erreur antérieure à cet appel laisse ce contexte absent, sans le fabriquer.

La réponse conservée est celle que la page doit afficher. Pour Echo, c'est la
description « Tour pris… » ; la sortie brute du moteur ne s'y substitue pas.
Pour les autres clients, le traitement existant retire les espaces extérieurs
et refuse une sortie vide. Les champs d'indicateurs qui accompagnent cette
réponse sont conservés avec elle.

Pour Ollama, la trace conserve modèle, adresse, délai et politique `think`.
Une relance reprend une configuration déjà utilisée par cette demande ; une
nouvelle demande ordinaire hérite de celle du dernier résultat de sa conversation,
y compris après création d'un nouveau registre. Le bouton « Demander une voix »
permet toujours un choix explicite via la configuration courante. Les clients
personnalisés restent dépendants du résolveur fourni à `SessionBook`.

Cette trace ne fige pas les poids derrière un nom de modèle et ne garantit pas
une reproduction textuelle identique. Elle ne constitue pas encore un budget
exact en tokens ni une politique de sélection des passages. La limite d'admission
de **100 000 caractères par demande** est déclarée comme telle.

## 5. API et navigateur

| Opération | Route | Effet |
|---|---|---|
| Accepter | `POST /api/demandes` | Corps `{demande, texte, session?, voix?}` ; enregistrement sans génération. |
| Retrouver | `GET /api/demandes/{id}` | Statut, réponse éventuelle, tentatives et contexte conservé. |
| Lancer | `POST /api/demandes/{id}/executer` | Première tentative ; répétition sans relance implicite d'un échec. |
| Relancer | `POST /api/demandes/{id}/relancer` | Corps `{relance}` ; nouvelle tentative explicite si son état le permet. |
| Lire le journal | `GET /api/session/{id}/journal?apres=0&limite=50` | Ordre croissant, curseur de position ; limite maximale 100. |
| Lire l'état / le registre | `GET /api/session/{id}`, `GET /api/sessions` | État protégé par la garde / résumés durables existants. |

Les routes de demandes renvoient le statut métier dans une réponse 200 quand
l'opération a pu être enregistrée, y compris si la tentative se termine par
`echoue`. Le client doit lire ce statut. Conflit : 409 ; identité inconnue : 404 ;
stockage indisponible : 503 ; requête invalide : 400 ou validation HTTP 422.
Les erreurs de tentative distinguent restauration, configuration, conservation
du contexte, calcul du tour et publication.

Avec le stockage v2, l'ancienne route `POST /api/parler` renvoie **410** et demande
de recharger la page. Son ancien chemin reste disponible dans les tests du
stockage v1 ; il n'est pas une seconde porte d'envoi du serveur v2.

[journal-client.js](../app/static/journal-client.js) conserve un envoi par clé
`lyra.demande.v1.<id>` dans `localStorage`. Une panne de stockage local empêche
le premier appel réseau et laisse le texte dans sa zone de saisie. Une coupure
réseau conserve la copie et les identités ; elle ne vaut pas échec du calcul.
Une copie de réponse terminée est retirée seulement après affichage dans la vue
concernée. Il n'y a pas de génération automatique au chargement de la page.

[p6-ui.js](../app/static/p6-ui.js) distingue la vue courante de l'opération en
cours. Changer de conversation laisse l'opération se terminer sans remplacer
le fil courant. Le journal relu peut aussi restituer les demandes non terminées
dont la copie locale manque. Effacer le stockage du navigateur retire toutefois
ses pointeurs et copies : le registre serveur demeure, mais sa navigation
complète n'est pas encore disponible dans la page.

## 6. Vérification PowerShell et résultat confirmé

Depuis le poste de Simon :

```powershell
Set-Location 'C:\Users\simon\PROJECTS\Triptique\lyra_reborn'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verifier_p6.ps1
```

Le script exige le Python du `.venv` et Node déjà installés. Il exécute les
contrôles ciblés, sans campagne P7 ni appel à Ollama, et utilise un dossier neuf
sous `data/runs/p6-verification/`. Il produit `pytest.log`, `pytest.xml`,
`javascript.log` et `verification.json` avec les codes de sortie et les
empreintes des fichiers vérifiés. Les tests de migration créent leurs propres
bases temporaires ; ils n'ouvrent pas la base de conversation utilisateur.
Le `Bypass` ne concerne que cette invocation PowerShell.

Exécution de développement du 7 septembre : **57 Python + 7 JavaScript réussis**,
un avertissement de dépréciation Starlette/httpx. Rapport local :
[verification.json](../data/runs/p6-verification/20260907-222336-fa18a815639a44fe9d52e6d7eb3670e2/verification.json)
(dossier ignoré par Git ; conserver ou transmettre le dossier pour la relecture).

**Rejeu effectué par Simon le 7 septembre à 22 h 29, puis vérifié par l'agent :**
[rapport PowerShell](../data/runs/p6-verification/20260907-222947-72f84aaff8b54e27bdec18178044a7c8/verification.json),
[résultat XML Python](../data/runs/p6-verification/20260907-222947-72f84aaff8b54e27bdec18178044a7c8/pytest.xml)
et [journal JavaScript](../data/runs/p6-verification/20260907-222947-72f84aaff8b54e27bdec18178044a7c8/javascript.log).
Les deux codes de sortie sont 0 ; le XML indique 57 tests, aucun échec, erreur
ou test ignoré ; le journal Node indique 7 réussites, aucun échec ni test ignoré.
Les empreintes des **19 fichiers déclarés dans le rapport** correspondent aux
fichiers présents lors de sa vérification. Empreinte SHA-256 du rapport :
`36a41f20108b85a9ec4e973b9e2a764617095c3812ed16ed74362f2d00751521`.

**Verdict : 🟢 PASS pour ce rejeu ciblé P6.** Le contrôle porte sur les sorties,
leur provenance déclarée, leurs chiffres et leur correspondance avec les fichiers
enregistrés. Il ne constitue pas une nouvelle revue indépendante du code, ni une
qualification live ou une preuve de migration utilisateur. Les rapports bruts
sont conservés sans modification. Leurs glyphes Node et certains accents du
libellé descriptif `scope` sont mal décodés ; les résultats numériques, le XML,
les chemins de fichiers et les empreintes restent lisibles et concordants.
L'avertissement Python concerne la dépréciation Starlette/httpx.

| Scénario du contrat | Preuves présentes | Limite |
|---|---|---|
| A01 | Garde historique + demande lisible pendant génération bloquée ; échec avant commit et exception après commit ; état accepté conservé. | Clients factices et registre unique. |
| A02–A03 | Premier accusé perdu, texte exact et identité conservés après rechargement simulé ; résultat retrouvé ; relance identifiable ; conflits. | Coupures injectées dans les tests, pas incident réseau réel. |
| A04 | Nouveau registre après début de tentative ; interruption visible sans exécution ; échec d'écriture terminale récupérable. | Aucun arrêt forcé d'un vrai serveur testé ici. |
| A05 | Acceptation ou réponse tardive après changement de vue ; résultat retrouvé sans second calcul. | Code de la page exécuté sous Node avec DOM simulé, pas qualification visuelle dans un navigateur réel. |
| A06 | 52 demandes conservées, ordre et réponses retrouvables, configuration Ollama conservée dans un nouveau registre. | Partiel : corrections et profil conversationnel à construire ; client Ollama remplacé par une fonction factice. |
| A09 | Copie d'une archive v1 de 52 tours, sorties manquantes signalées, source inchangée ; archive incohérente refusée. | Bases temporaires, aucune migration utilisateur. |

Fichiers de preuve : [demandes](../tests/test_p6_requests.py),
[HTTP](../tests/test_p6_requests_http.py), [migration](../tests/test_p6_journal_migration.py),
[client navigateur](../tests/test_journal_client.cjs), [vues](../tests/test_p6_ui.cjs),
et les contrôles antérieurs de concurrence, persistance, HTTP et premières couches.
Les contrôles de développement ont maintenant été rejoués avec succès par Simon.
La condition de rejeu PowerShell est donc satisfaite pour cette étape ; cela ne
vaut ni acceptation du contrat P6 complet ni qualification de la qualité
conversationnelle.

## 7. Migration préparée, à exécuter séparément

Le chemin par défaut reste `data/lyra_sessions.sqlite3`. Une base neuve y reçoit
le format v2 ; une ancienne base v1 y est refusée. **Ne pas supprimer la base
ancienne pour faire disparaître cette erreur.** La suite de vérification ne
lance pas cette migration et ne change pas la configuration du lanceur.

Après vérification et au moment choisi pour la bascule, arrêter le serveur
Lyra, puis créer une destination qui n'existe pas encore :

```powershell
Set-Location 'C:\Users\simon\PROJECTS\Triptique\lyra_reborn'
.\.venv\Scripts\python.exe -B -X utf8 .\scripts\migrate_p6_journal.py `
  --source .\data\lyra_sessions.sqlite3 `
  --destination .\data\lyra_journal.sqlite3
```

Lire le rapport retourné et `data/lyra_journal.migration.json`. Le script ouvre
la source en lecture seule, utilise la sauvegarde SQLite pour produire une
copie cohérente, valide les états avec le chargeur v1, puis transforme la copie.
Il refuse d'écraser la destination ou un rapport existant. En cas d'échec, la
copie reste pour inspection ; elle n'est pas annoncée comme prête à l'emploi.

Les anciens prompts récupérables sont déjà normalisés par le code v1. Ses
sorties moteur ne suffisent pas à attester ce qui était réellement affiché,
notamment avec Echo ; elles sont donc étiquetées comme telles. Les anciennes
réponses absentes restent absentes. Les dates de tour inconnues ne sont pas
inventées : les dates nouvelles sont celles de l'import. L'état de contrôle v1
reste identique dans la copie ; aucune réponse n'est générée par la migration.

Pour utiliser ensuite la copie, dans **ce même PowerShell** :

```powershell
$env:LYRA_DB_PATH = Join-Path (Get-Location).Path 'data\lyra_journal.sqlite3'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8766
```

Cette variable n'est pas un réglage permanent du lanceur `Ouvrir Lyra.vbs`.
Ne pas démarrer un second processus sur la même base. Le fichier source v1
reste disponible pour l'ancien code ; revenir à cette source ne fusionnerait
pas les nouvelles demandes enregistrées dans la copie v2.

Après cette bascule, la vérification manuelle peut examiner la reprise du fil
après rechargement, la réponse tardive lors d'un changement de vue et les boutons
de reprise d'envoi. Une qualification avec un modèle lent réel reste distincte
et exige son activation explicite. Cette réalisation ne l'a pas effectuée.

## 8. Limites avant la prochaine tranche

- Un utilisateur local, un registre et un processus. Aucun contrat multi-worker,
  service distant ou authentification nouvelle.
- Pas d'expiration ni de suppression automatique du journal. Les plafonds de
  stockage, la suppression explicite et le traitement des sauvegardes restent
  à réaliser ensemble ; aucune promesse d'effacement n'est faite ici.
- Pas encore de navigation complète entre les anciennes conversations, de
  corrections liées, de rappel de passage, de budget inspectable ou de profil
  conversationnel fixe. A07, A08 et A10 ne sont pas couverts.
- Pas d'annulation d'une demande en attente, de temporisation applicative nouvelle
  ni d'abandon d'un calcul vivant. Le client d'inférence garde son délai existant.
- Le stockage local du navigateur et la base SQLite contiennent les textes en
  clair. La page et le serveur restent destinés à `127.0.0.1`.

La prochaine décision porte sur la tranche conversationnelle de la section 6
du contrat ; le rejeu PowerShell préalable est confirmé. La migration utilisateur
reste une opération distincte, préparée et non exécutée. P7, la Jachère et les
ponts restent des chantiers séparés.
