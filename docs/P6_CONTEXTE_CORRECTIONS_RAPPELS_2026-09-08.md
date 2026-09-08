# P6 — contexte, corrections, rappels et frontière du moteur

**8 septembre 2026 · réalisation locale sur `788971a` · non publiée.**
Suite du [contrat P6](CONTRAT_USAGE_P6_v0_2026-09-07.md) et du
[journal des demandes](P6_JOURNAL_DEMANDES_2026-09-07.md).
La mention « non publiée » situe cette réalisation avant les commits de
publication. Les rapports liés sous `data/runs/` et les exports sous `output/`
restent locaux, ignorés par Git et absents de GitHub ; leurs liens supposent
une copie locale des preuves. Les sources, tests et commandes restent versionnés.

Les recommandations de la tranche sont approuvées par Simon. Il autorise
désormais l'agent à lancer directement les contrôles réalisables sur ce poste ;
un rejeu dans son PowerShell n'est plus une condition systématique.

**Résultat :** contexte conversationnel, corrections liées, rappels choisis et
navigation sont implémentés. **73 tests Python et 9 tests JavaScript réussis**,
parcours navigateur vérifié sur un moteur factice. Le contrôle réel Gemma valide
le transport et le refus d'une entrée trop longue, mais révèle une réponse qui
ignore la correction d'un rappel. **La qualité conversationnelle reste à qualifier.**
Aucune mise à jour d'Ollama, téléchargement de modèle, exécution Qwen, migration
utilisateur ou campagne P7 n'a été réalisée.

## 1. Ce qui change dans une nouvelle conversation

Le nouveau profil `conversation_reference_v1` prend l'historique du journal
avec les rôles `user` et `assistant`. Il ne construit ni contrôleur, ni graphe,
ni Memento, ni écologie ; aucune mémoire dérivée n'est injectée automatiquement.
Les anciennes conversations conservent leur profil historique de contrôle.

Le profil fixe contient :

| Paramètre | Valeur initiale |
|---|---|
| Fenêtre d'historique | Au plus 30 paires complètes récentes |
| Plafond applicatif d'entrée | 16 000 caractères, messages système et rappels compris |
| Contexte Ollama demandé | `num_ctx=8192` tokens |
| Sortie maximale demandée | `num_predict=1024` tokens |
| Génération | `temperature=0.3`, `top_p=0.9`, `repeat_penalty=1.0`, `think=false` |
| Débordement serveur | `truncate=false`, `shift=false` |

Ce profil constitue une référence technique initiale, pas un optimum démontré.
Les options non spécifiées restent celles du modèle et du moteur ; leur identité
est enregistrée. Le budget en caractères **ne mesure pas les tokens**. Le
template du modèle et la tokenisation peuvent faire dépasser le contexte réel.
Le refus serveur est alors conservé comme échec explicite, sans réessai caché.

L'assemblage conserve le message courant et tous les rappels actifs. Il ajoute
les paires récentes complètes dans l'enveloppe restante ; il ne découpe pas un
message ni une correction pour faire rentrer le tout. Les omissions précisent
leur motif. Une paire trop grande ferme la fenêtre des paires plus anciennes.
Les demandes non terminées, démonstrations et imports sans réponse conversationnelle
validée sont exclus de l'historique envoyé, avec un motif conservé.

Si les éléments obligatoires seuls dépassent le plafond, aucun appel au modèle
n'a lieu. L'erreur est visible dans la demande ; ce refus avant assemblage
complet n'a pas de contexte transmis à présenter. Le journal conserve le texte.

## 2. Corrections et rappels : sémantique exacte

L'unité de cette version est **un message entier**, utilisateur ou assistant,
appartenant à un échange terminé. La sélection d'une sous-chaîne arbitraire
n'est pas implémentée. Un message a une provenance : conversation, demande et rôle.

Une correction est une nouvelle déclaration liée à ce message. L'original et
les corrections antérieures sont conservés ; la dernière correction remplace la
précédente pour les prochains usages. Elle n'est jamais présentée comme une
vérification factuelle indépendante. L'historique envoyé conserve le rôle de
l'original et ajoute la correction comme déclaration utilisateur identifiée.

Chaque geste possède une identité durable côté navigateur avant envoi.
Répéter une correction identique sous la même identité retrouve son résultat.
Une modification concurrente de sa version précédente provoque un conflit 409.
La page relit alors les versions, garde le texte proposé et attend un nouveau
clic pour le soumettre après la nouvelle tête. Un accusé perdu conserve au
contraire exactement l'identité et le contenu initiaux jusqu'à résolution.

Un rappel relie explicitement une conversation de destination à ce message.
Il inclut son original et sa dernière correction sous forme de passage cité,
avec la provenance. Il n'importe ni les autres messages de la source ni ses
propres liens de rappel. Si le texte sélectionné contient déjà une citation,
celle-ci reste évidemment du texte : le mécanisme ne prétend pas effacer les
informations présentes dans le message choisi.

**Choix retenu : les corrections suivent les rappels lors de leur prochain usage.**
La lecture des sources est cohérente dans une courte transaction SQLite.
Le contexte obtenu est figé et enregistré **par tentative** avant la génération.
Corriger ou retirer un rappel pendant le calcul ne change pas cette tentative.
Une relance volontaire après échec peut donc avoir un contexte différent ; ses
deux versions restent inspectables et l'identité de moteur déjà choisie est conservée.

« Retirer du contexte » désactive le lien pour les prochains assemblages. Cela
n'efface ni la source, ni les contextes déjà enregistrés, ni les réponses qui
ont pu en reprendre une information. Ce geste n'est pas une suppression de données.

## 3. Interface et API

La liste « Conversations conservées » permet de rouvrir une conversation,
même après perte du pointeur local, tant que sa base serveur est disponible.
Le journal est paginé. Les résultats tardifs restent attachés à leur conversation.

Chaque échange terminé propose « corriger / rappeler » pour ses deux messages
et « Voir le contexte » pour les tentatives enregistrées. Le dialogue de passage
montre original, provenance, corrections et destination. Les rappels actifs
sont visibles dans la conversation de destination et peuvent être retirés.
Les textes du journal sont rendus en texte, sans interpréter leur HTML.

Dans une conversation neuve, « Envoyer » prépare une démonstration sans modèle.
« Demander une voix » active explicitement le moteur installé choisi par la
configuration existante. Après activation, les envois utilisent le moteur de
cette conversation ; le bouton n'est pas un sélecteur permettant une substitution.
Les indicateurs de contrôle historique sont masqués dans le profil de référence.

| Opération ajoutée | Route / corps |
|---|---|
| Créer une conversation vide | `POST /api/conversations` · `{conversation}` |
| Lire un message et ses révisions | `GET /api/passages/{demande}/{role}` |
| Déclarer une correction | `POST /api/passages/{demande}/{role}/corrections` · `{correction, texte, precedente}` |
| Lire les rappels actifs | `GET /api/session/{session}/rappels` |
| Ajouter un rappel | `POST /api/session/{session}/rappels` · `{rappel, source, role}` |
| Retirer un rappel | `POST /api/session/{session}/rappels/{rappel}/retirer` |

Les routes du journal et des tentatives restent celles de l'étape 2. L'ancienne
route `/api/parler` reste fermée avec le nouveau stockage. L'API des corrections
peut documenter un message historique complet, mais l'ancien profil de contrôle
ne consomme pas ces corrections : ouvrir une conversation de référence pour les
utiliser. Les entrées importées incomplètes ne sont pas rappelables.

## 4. Architecture face aux évolutions d'Ollama et des modèles

Les versions figées sont une contrainte de compatibilité utile. La fragilité
vient surtout du coût et de l'étendue d'un changement non isolé ou non vérifié.
La nouvelle frontière est [OllamaChatAdapter](../app/chat_backend.py) : elle reçoit
messages structurés et profil, puis renvoie texte final, raison d'arrêt et compteurs.
Le journal, les corrections et les rappels ne dépendent pas du protocole Ollama.
`core/llm.py` et le chemin expérimental de contrôle n'ont pas été remaniés.

À la première activation, l'adaptateur conserve nom exact, digest du modèle,
version du serveur, adresse et délai. Il revérifie version et digest avant
chaque génération. Une divergence refuse le calcul ; elle ne déclenche ni
mise à jour, ni téléchargement, ni substitution. La reprise conserve cette
identité, y compris après l'échec d'une première tentative.

La liste de versions du contrat d'adaptateur est actuellement limitée à
**Ollama 0.33.3**. Cela ne qualifie pas tous les modèles disponibles sur cette
version. Le seul contrôle réel de cette tranche porte sur **Gemma 3 4.3B Q4_K_M**,
tag `gemma3:latest`, digest
`a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a`.
Une autre version est refusée jusqu'à adaptation vérifiée de cette frontière ;
ce refus n'est pas la preuve que cette version serait intrinsèquement incompatible.

Le dossier [Qwen admission v2](P7_QWEN38_ADMISSION_V2_STATUS.md) documente
**0.32.14**, alors que `/api/version` répond **0.33.3** le 8 septembre.
L'admission historique ne se transfère donc pas automatiquement. Le précédent
[incident documenté](P7_QWEN38_ADMISSION_STATUS.md) concernait notamment un
démarrage avant disponibilité des bibliothèques GPU, suivi d'un repli CPU ;
il ne démontre pas à lui seul une incompatibilité générale de Qwen.

Pour pérenniser le montage, progression proposée :

1. Conserver le contrat de conversation et le stockage indépendants des moteurs.
2. Associer une admission à un ensemble précis : adaptateur, runtime, digest,
   options, template, tokenizer et environnement GPU. Séparer conformité de l'API,
   budget, exécution GPU et qualité d'usage. Un test d'interface ne vaut pas
   admission conversationnelle ; l'observation Gemma ci-dessous le montre.
3. Qualifier une nouvelle combinaison à côté de celle utilisée : autre processus
   et port, environnement de dépendances distinct, éventuellement conteneur si
   cela facilite réellement l'isolation GPU et système. Cette isolation reste à
   installer ; elle n'est pas apportée par une simple classe Python.
4. Promouvoir explicitement la combinaison validée dans un nouveau profil. Les
   conversations existantes gardent leur profil ; leur éventuelle conversion
   devient une opération distincte et traçable, sans réécrire leurs tentatives.
5. Garder l'ancien runtime et ses artefacts jusqu'à vérification du retour arrière.
   Revenir à une base antérieure ne fusionne pas les échanges produits entre-temps.

La vérification avant appel réduit les dérives silencieuses ; elle ne verrouille
pas un processus Ollama contre une modification extérieure pendant l'appel.
Pilotes GPU, matériel et options implicites peuvent aussi influencer le résultat.
Les sorties ne sont donc pas promises identiques bit à bit. Le déploiement général
nécessitera cette isolation et une matrice d'admission ; ils ne sont pas annoncés
comme achevés par cette tranche.

Fondements : [API chat Ollama](https://docs.ollama.com/api/chat),
[contrat du tag 0.33.3](https://raw.githubusercontent.com/ollama/ollama/v0.33.3/api/types.go),
[options du Modelfile](https://docs.ollama.com/modelfile),
[contexte et mémoire](https://docs.ollama.com/context-length).
La présence des champs dans le tag est une preuve documentaire ; le refus réel
ci-dessous est une preuve d'exécution distincte.

## 5. Stockage et migration préparée

[DialogueStore](../app/dialogue_store.py) ajoute les tables `corrections`,
`correction_heads` et `recalls` au journal. **Format SQLite v3**, avec états de
conversation historique v1 et référence v2. Ces numéros désignent des contrats
différents. Le chargeur de référence valide son schéma, son profil et son moteur.
Les anciennes validations v1 restent actives pour les archives de contrôle.

Le serveur courant attend une base v3. Une base v1 ou v2 existante est refusée,
sans conversion silencieuse. [migrate_p6_dialogue.py](../scripts/migrate_p6_dialogue.py)
prépare une copie v3 depuis v1 ou v2, valide les archives et refuse tout écrasement.
La source s'ouvre en lecture seule ; les profils historiques ne sont pas convertis.
La copie et ses rapports restent disponibles pour inspection en cas d'échec.
Le script v1→v2 de l'étape 2 seul ne suffit plus au serveur courant.

**Commandes de bascule préparées, non exécutées sur les données utilisateur.**
Arrêter le serveur qui utilise la source avant de basculer, choisir une destination
neuve, lire le rapport puis démarrer un seul processus sur la copie :

```powershell
Set-Location 'C:\Users\simon\PROJECTS\Triptique\lyra_reborn'
.\.venv\Scripts\python.exe -B -X utf8 .\scripts\migrate_p6_dialogue.py `
  --source .\data\lyra_sessions.sqlite3 `
  --destination .\data\lyra_dialogue_v3.sqlite3
# Après examen de lyra_dialogue_v3.dialogue-migration.json :
$env:LYRA_DB_PATH = Join-Path (Get-Location).Path 'data\lyra_dialogue_v3.sqlite3'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8766
```

La variable ne modifie pas durablement le lanceur VBS. Le chemin source peut
être une autre base v2 déjà choisie par l'installation. Aucune suppression
explicite, politique de sauvegarde ou fusion entre copies n'est ajoutée ici.

## 6. Preuves et limites de la vérification

### Contrôles déterministes

[Rapport du 8 septembre](../data/runs/p6-verification/20260908-102233-74d68cd6665f4a97a1ce8cc71378276f/verification.json) :
**73 Python + 9 JavaScript réussis**, aucun échec ni test ignoré ; avertissement
de dépréciation Starlette/httpx inchangé. Le script conserve XML, journaux et
empreintes. Il utilise des clients factices, SQLite temporaire et un DOM simulé.

Preuves nouvelles : [contexte et isolation](../tests/test_p6_context.py),
[API](../tests/test_p6_context_http.py), [adaptateur](../tests/test_p6_chat_backend.py),
[migration v1/v2→v3](../tests/test_p6_dialogue_migration.py) et
[client de page](../tests/test_p6_ui.cjs). Elles couvrent notamment non-transitivité,
corrections concurrentes, contexte figé pendant calcul, nouvelle tentative,
publication avant/après commit et refus d'une identité moteur modifiée.

Le premier lancement élargi avait révélé sept échecs de la fixture HTTP v1,
qui gardait le nouveau constructeur de conversation. Cette fixture choisit
maintenant explicitement `LyraConversation` ; ses assertions historiques sont
conservées. [Le premier rapport](../data/runs/p6-verification/20260908-102127-d7a7b93f645c40af87bf5df9cc618953/verification.json)
reste conservé, sans réécriture.

### Navigateur réel, moteur factice

Parcours exécuté dans le navigateur Codex sur `127.0.0.1:8767`, avec
[serveur factice explicite](../tests/p6_browser_server.py) et base séparée :
échange, correction mardi→jeudi, rappel dans une conversation neuve, contexte
inspecté, retrait, rechargement et demande suivante sans rappel actif.
Original, correction et rôles sont visibles ; aucun avertissement ni erreur
n'est retourné par le journal de console consulté. Les captures de la page et
du dialogue ont été inspectées. L'icône de site absente renvoie 404 sans affecter
le parcours. Serveur temporaire arrêté et onglet fermé après vérification.
[Compte rendu](../data/runs/p6-conversation/browser-232c74302f2246c3963aacc6c4201f45/verification.json).

### Contrôle réel limité : résultat technique et contre-exemple d'usage

[Rapport brut Gemma](../data/runs/p6-conversation/live-474e2b0f1f68412294fcbce1a58879f6/verification.json),
produit par [check_p6_chat.py](../scripts/check_p6_chat.py) avec `--model gemma3:latest`.
Trois générations locales sur données synthétiques, aucune donnée réservée.
L'identité runtime/modèle est identique avant et après. Une entrée de
**20 011 tokens pour 8 192 disponibles est refusée HTTP 400**, conformément au
refus de troncature demandé. Cela ne mesure pas la borne exacte de tous les modèles.

L'échange initial dit mardi et demande « noté ». La correction liée dit jeudi.
Dans la même conversation, Gemma répond : « Le jour corrigé du rendez-vous est
jeudi. » Dans la destination du rappel, il répond : **« Noté. Mardi. »**
Le contexte conservé comporte pourtant l'original et la correction `correction`.
Le `status=passed` du rapport couvre uniquement les assertions techniques
annoncées dans `expected`, pas la conformité sémantique de cette réponse.
Le contre-exemple est conservé ; aucune sélection d'un meilleur essai ne le remplace.

**Conclusion limitée :** la fidélité des messages envoyés et la stabilité du
journal sont vérifiées sur les scénarios exercés. L'admission d'usage du modèle
reste ouverte, notamment lorsqu'un message rappelé mêle instruction ancienne
et information corrigée. Il faudra examiner représentation des passages et
capacité du moteur sur des cas distincts avant de qualifier cet usage. Aucun
classement de modèles ni taux de réussite n'est déduit de ces trois générations.

### Couverture restante

A06–A08 disposent maintenant de preuves techniques sur reprise, corrections,
budget et rappels. A10 (suppression et copies) reste à réaliser. Restent aussi :
qualification conversationnelle, arbitrage des paramètres de production,
isolation du runtime, abandon de calcul et gestion des sauvegardes. La lecture
du journal complet avant sélection du contexte n'est pas encore optimisée pour
de très longues conversations. Un utilisateur et un processus serveur restent
l'enveloppe testée ; pas de contrat multi-worker ni d'exposition réseau publique.

Cette note est une justification révisable de l'auteur ayant participé au plan.
Elle ne prononce pas l'acceptation du contrat P6 complet et ne rouvre pas P7.

Un [diagnostic exploratoire séparé](P6_DIAGNOSTIC_RAPPELS_2026-09-08.md) examine
depuis le 8 septembre quatre configurations et les combinaisons de présentation
du rappel. Son état de collecte et les dossiers de relecture sont suivis dans
cette nouvelle note ; le contrôle Gemma ci-dessus reste une preuve historique.
