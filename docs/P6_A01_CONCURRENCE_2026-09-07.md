# P6 — correction A01 de concurrence

**7 septembre 2026 — modification locale sur la base `788971a`.**
La correction est dans l'arbre de travail ; ce document n'annonce ni commit,
ni push, ni déploiement. Les garanties décrites portent sur les chemins HTTP
utilisant un seul `SessionBook` dans un processus serveur.

**Note de publication :** ce statut décrit la réalisation du 7 septembre ; il
ne décrit pas l'état ultérieur des commits. Les rapports de vérification sous
`data/runs/` et les exports sous `output/` restent locaux, ignorés par Git. La
reproduction de concurrence citée ci-dessous est une preuve historique versionnée.

**Étape suivante réalisée le même jour :** le
[journal et le cycle des demandes](P6_JOURNAL_DEMANDES_2026-09-07.md) réutilisent
cette garde. Sous le nouveau stockage v2, `/api/parler` renvoie 410 ; les envois
passent par `/api/demandes`, et une première session est durable dès l'acceptation,
avant la génération. Les descriptions ci-dessous conservent le périmètre et les
résultats historiques d'A01. Les limites de journal et de reprise qu'elles
mentionnent sont actualisées dans le guide de l'étape 2. Simon a rejoué avec
succès les 57 tests Python (dont les huit cas A01) et sept tests JavaScript
le 7 septembre à 22 h 29 ; le rapport et ses 19 empreintes ont été vérifiés.
Cette confirmation porte sur les contrôles ciblés hors ligne.

## Problème et résultat

Deux requêtes pouvaient récupérer le même objet conversation, puis chacune
capturer un état avant leurs générations. Le retour arrière de l'une pouvait
remplacer l'objet du registre par un état plus ancien que le résultat accepté
de l'autre. Une persistance ultérieure pouvait alors perdre ce résultat.
La [reproduction conservée du 5 septembre](relectures/2026-09-05_base_conversationnelle/preuves/concurrence_2026-09-05.json)
documente ce défaut sous client factice ; elle n'a pas été modifiée ni rejouée
sur le code corrigé.
Son [script conservé](relectures/2026-09-05_base_conversationnelle/preuves/verifier_concurrence.py)
exige exactement le commit `788971a00f4303d2ba24cc671f4c0049fab772f9` et refuse
un autre `HEAD` ou des modifications suivies dans `app/`, `core/` et `memory/`.
Il ne constitue donc pas une commande de vérification du code courant corrigé.

La correction réserve maintenant **l'identité** de la conversation avant
`require` ou `create`, et conserve cette réservation pendant la capture de
l'état, le choix du moteur, la génération, la sauvegarde, le retour arrière
éventuel et la préparation du résultat HTTP. La réservation appartient au
registre, pas à un objet que le rollback peut remplacer.

- Une seconde requête `POST /api/parler` pour cette identité reçoit **409**
  avec une indication de conversation occupée, sans appeler son modèle ni
  modifier la session. Aucun envoi automatique différé n'est créé.
- `GET /api/session/{sid}` utilise la même garde et reçoit aussi **409** si une
  opération détient l'accès. Il ne lit donc pas un état en cours de mutation.
- `GET /api/sessions` continue de lire les résumés durables dans SQLite. Une
  première session n'y figure qu'après sa première sauvegarde réussie.
- Une autre conversation peut continuer. Le verrou commun ne protège que la
  réservation et la libération de l'identité ; il n'est pas maintenu pendant
  le calcul ou les opérations SQLite.
- Si la reconstruction du retour arrière échoue, l'objet modifié a déjà été
  retiré du registre. Une erreur **503** décrit ce défaut ; l'accès ultérieur
  doit restaurer l'état durable ou signaler son indisponibilité.

La garde ne maintient aucune nouvelle transaction SQLite pendant la génération.
Elle ne conserve une entrée que pour les opérations actives. Le format des
données, le schéma SQLite et les validations du chargeur v1 sont inchangés.

## Implémentation et propagation

- [app/session.py](../app/session.py) : `SessionBusyError`, garde
  `SessionBook.exclusive`, éviction de l'objet avant reconstruction au rollback.
- [app/main.py](../app/main.py) : garde autour du cycle complet de parole et de
  la lecture d'état ; traduction des conflits en 409 et du rollback impossible
  en 503. L'identité d'une nouvelle conversation précède sa création.
- [tests/test_p6_concurrency.py](../tests/test_p6_concurrency.py) : huit cas
  déterministes supplémentaires.

La page actuelle affiche déjà le détail d'une erreur HTTP et ne supprime pas
son identifiant de conversation lors d'un 409 de reprise. Le texte envoyé reste
dans le fil de la page. La conservation durable d'une demande avant génération,
sa relance identifiable et la restauration du brouillon après rechargement
restent des étapes ultérieures du contrat P6.

## Vérification

Le premier contrôle de chevauchement a échoué avant correction : **200 reçu
au lieu de 409** pendant une génération déjà en cours. Le contrôle ajouté sur
l'échec du rollback a lui aussi échoué avant sa correction, avec remontée du
`RuntimeError` de reconstruction.

Résultat final le 7 septembre : **34 tests réussis**, dont huit nouveaux cas,
sur les quatre fichiers suivants :

```powershell
.\.venv\Scripts\python.exe -B -X utf8 -m pytest -q -p no:cacheprovider `
  tests/test_p6_concurrency.py tests/test_p6_http.py `
  tests/test_p6_first_layers.py tests/test_session_persistence.py
```

Les cinq phases de restauration, capture, génération, sauvegarde et rollback
sont retenues par des rendez-vous `Event`. Les tests vérifient le refus des
accès concurrents, l'activité d'une autre conversation, les états durables et
en mémoire, puis la conservation du résultat accepté après un tour suivant
et dans un nouveau registre. Deux autres cas couvrent la sauvegarde d'un tour
réussi et celle d'une première session ; le dernier couvre le rollback défaillant.

Conditions : Python du dépôt, FastAPI `TestClient`, client explicitement
factice, bases SQLite temporaires neuves, aucun Ollama ni corpus P7.
Un avertissement de dépréciation Starlette/httpx est présent. Les comparaisons
d'état utilisent la même représentation JSON des deux côtés, afin de comparer
les tuples de l'écologie à leurs listes sérialisées sans exclure de champ.

Cette sélection qualifie le comportement ciblé et sa compatibilité avec les
premières couches, l'HTTP et la persistance. Ce n'est ni une nouvelle suite
complète, ni un redémarrage réel du serveur, ni une qualification d'usage avec
un modèle lent. Aucun gain sémantique ou taux de panne réel n'en est déduit.

## Limites et reprise

La garde est non réentrante et locale à un registre. Les méthodes de bas niveau
de `SessionBook` restent séquentielles si elles sont utilisées sans cette garde ;
un nouvel appelant concurrent doit respecter le même contrat. Plusieurs
processus serveurs ou plusieurs registres actifs sur une même base ne sont pas
protégés par ce mécanisme et demanderaient une coordination supplémentaire.

Un moteur d'inférence commun peut toujours introduire une contention entre
conversations. L'arrêt du processus en cours de génération, l'identité durable
des demandes et les réponses réseau perdues relèvent du futur journal. Une
nouvelle requête sans identité de conversation continue de créer une nouvelle
session : l'idempotence du premier envoi n'est pas implémentée ici.

**Prochaine étape P6 :** journal et cycle de demande, puis migration préparée,
selon le [contrat d'usage](CONTRAT_USAGE_P6_v0_2026-09-07.md). La
[note Jachère](NOTE_ARCHITECTURE_JACHERE_CLOISONNEMENT_2026-09-07.md) est intégrée
à la documentation ; son implémentation reste un chantier distinct.
