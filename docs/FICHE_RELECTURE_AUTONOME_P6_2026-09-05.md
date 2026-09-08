# Lyra - Fiche de relecture autonome

**Objet :** décider de la prochaine base conversationnelle, avant développement.
**Date :** 5 septembre 2026 · **Version :** 1 · **Statut :** proposition soumise à contradiction.
**Lecture estimée :** 12 minutes, hors inspection du code.

## 1. Le projet et la décision attendue

Lyra ajoute du contrôle et de la mémoire à un modèle de langage local exécuté avec Ollama. Cette application Python adapte des paramètres de génération à partir de signaux textuels et conserve un graphe de concepts et un état de session. Elle n'entraîne pas un nouveau modèle.

Le projet est développé avec une forte assistance d'IA. Cette fiche est rédigée par l'assistant ayant proposé le plan et sollicite une contradiction indépendante ; elle ne vaut pas validation extérieure.

**Usage candidat :** converser en français, fermer l'application, retrouver les échanges, poursuivre et corriger une information. La mémoire entre conversations reste à cadrer. Construire cet interlocuteur local et démontrer la supériorité du contrôle adaptatif sont deux objectifs distincts.

**Question centrale :** quelle évolution minimale permet cet usage avec des comportements vérifiables ? Extension, séparation de composants et nouvelle base sont à comparer. La refonte n'est pas acquise.

### Vocabulaire utile

- **P6** : chantier de l'application utilisable. **P7** : chantier d'évaluation de l'avantage du contrôle adaptatif face à des réglages fixes.
- **Tour** : demande utilisateur et réponse associée. Une tentative interrompue doit pouvoir être distinguée d'un tour accepté.
- **Journal** : échanges conservés. **Contexte** : contenu effectivement transmis au modèle pour une réponse. **État de contrôle** : réglages et signaux internes. Ces trois objets ne sont pas interchangeables.
- **Nemeton** : graphe conceptuel actuel. **Memento** : stockage et rappel par similarité de cas. **ESMM** : moteur d'exploration multimodèle présent ailleurs dans le dépôt.

### État de référence

Code étudié : branche `codex/p7-meta-arret`, commit **788971a00f4303d2ba24cc671f4c0049fab772f9**, dépôt [SimonBouhier/lyra_reborn](https://github.com/SimonBouhier/lyra_reborn/tree/788971a00f4303d2ba24cc671f4c0049fab772f9). La persistance a été introduite par `d7353d4`.

| Élément | Comportement constaté dans le code | Limite pour l'usage visé |
|---|---|---|
| Application | Serveur FastAPI, page locale, moteur propre à chaque session. [C1, C2] | Parcours quotidien encore incomplet. |
| Persistance | État sérialisé en SQLite ; restauration ; retour à l'état précédent sur plusieurs erreurs prises en charge. [C1-C3] | Aucun journal intégral des réponses affichées ; garantie de concurrence à préciser. |
| Contexte du modèle | Message courant, précédé d'un bloc Nemeton si le graphe n'est pas vide. [C2] | Les anciennes réponses ne sont pas réinjectées. |
| Historique | Les 50 derniers couples entrée/sortie internes sont conservés. [C4, C5] | L'entrée inclut le contexte ajouté ; en mode démonstration, la sortie interne diffère du texte affiché. |
| Mémoire | Au plus cinq concepts lexicaux récoltés par demande, liens de cooccurrence, triage et ajout d'un cas. [C2, C6] | Cela ne démontre ni rappel pertinent, ni compréhension, ni correction durable. |
| Interface | Reprend l'identifiant de session et ses indicateurs ; liste des sessions disponible côté serveur. [C1, C7] | Ne réaffiche pas les échanges à la reprise ; navigation entre anciennes conversations à construire. |

**Portée des preuves :** inspection du code et des tests, sans nouvelle exécution pour cette fiche. Les risques ci-dessous sont des déductions de lecture lorsqu'aucune reproduction n'est citée. Le document d'état [D1] rapporte 127 tests hors ligne réussis le 5 septembre ; ce résultat historique ne qualifie pas les fonctions proposées.

<!-- pagebreak -->

## 2. Les bifurcations à examiner

### Q1. Que doit signifier « Lyra se souvient » ?

Faut-il seulement reprendre une conversation, retrouver des passages à la demande, ou réutiliser automatiquement des informations entre projets ? Distinguer faits rapportés, préférences, hypothèses et affirmations produites par Lyra. Une proposition de l'assistant ne doit pas devenir une décision de l'utilisateur par simple répétition.

**Réponse attendue :** un périmètre initial explicite, la provenance nécessaire et les règles de correction, de portée et de non-utilisation. Examiner aussi la tension entre journal conservé et demande d'effacement ; ne pas promettre simultanément immutabilité et effacement intégral sans préciser leur sens.

### Q2. Qu'est-ce qu'un tour fiable malgré une interruption ?

Le serveur modifie l'objet de session, appelle le modèle et sauvegarde ensuite l'état. Aucun identifiant de tentative ni mécanisme de déduplication n'apparaît dans le contrat HTTP. Aucun verrou couvrant tout le tour d'une session n'a été trouvé dans ce parcours. [C1-C3]

**Risques à reproduire :** deux envois simultanés ; réponse du modèle suivie d'une panne avant sauvegarde ; sauvegarde réussie mais réponse HTTP perdue. SQLite garantit l'atomicité de ses transactions, pas celle de l'appel à Ollama et des objets Python. [T1]

**Réponse attendue :** ordre des opérations, états visibles après panne et règle de reprise. Une même demande peut être reconnue grâce à un identifiant explicite ; cela ne garantit pas une seule génération physique après une panne. Deux messages identiques peuvent également être intentionnels. [T2]

### Q3. Quelle information fournir au modèle, sous quel budget ?

L'injecteur actuel sélectionne les concepts par degré et récence, dans un bloc plafonné à 1 200 caractères ; il ne recherche pas les passages pertinents pour la question. Le client utilise `/api/generate` et ne retourne que le texte de réponse, sans remonter les compteurs de tokens. [C6, C8]

**Réponse attendue :** politique initiale comparée à un historique simple ; découpage des échanges ; budget d'entrée et de sortie ; traitement des références comme « la seconde option ». Définir les rôles des messages, les contenus omis et leur traçabilité. Examiner `/api/chat`, qui accepte des messages structurés, sans supposer qu'un changement de point d'entrée suffit. [T3]

### Q4. Comment éviter que la mémoire change silencieusement ce que mesure le contrôle ?

Le même texte composé est aujourd'hui envoyé au modèle puis utilisé pour calculer les métriques de la boucle. Ajouter l'historique peut donc changer les signaux de contrôle, même à demande utilisateur inchangée. [C2, C4]

**Réponse attendue :** contrat séparant demande, contexte et entrée des capteurs ; justification de chaque signal ; stratégie de compatibilité avec les appels d'évaluation. Les noms « cohérence » ou « tension » désignent ici des signaux calculés, pas des qualités sémantiques déjà validées.

### Q5. Quelle migration préserve honnêtement l'existant ?

Les réponses internes au-delà des 50 derniers tours ne sont pas conservées dans cet historique. Des demandes brutes restent présentes dans l'écologie ; elles ne suffisent pas à reconstituer toutes les réponses affichées. L'état complet est réécrit à chaque sauvegarde. [C2-C5]

**Réponse attendue :** données récupérables, lacunes à signaler, sauvegarde et retour arrière de migration ; horizon de croissance acceptable. Ne pas fabriquer des réponses manquantes ni attribuer une configuration précise à un ancien tour sans preuve.

### Q6. Quel degré d'autonomie accorder aux composants existants ?

Le tour P6 n'appelle pas ESMM. Le rappel Memento intervient après l'ajout du cas courant et sa suggestion n'alimente pas la réponse qui vient d'être générée. Son utilité conversationnelle reste à établir. [C2]

**Réponse attendue :** composants à conserver, isoler, différer ou remplacer, avec motifs. Examiner une référence à réglages fixes avant d'attribuer des gains au contrôle adaptatif. L'exploration automatique, les actions externes et un service public ne font pas partie du premier lot proposé.

<!-- pagebreak -->

## 3. Plan candidat et preuves de sortie

L'ordre suivant est une proposition révisable. Le relecteur peut fusionner, réduire ou remplacer des lots s'il explicite les conséquences.

| Lot | Contenu proposé | Preuve attendue avant de poursuivre |
|---|---|---|
| A. Contrat d'usage | Définir tour, tentative, journal, contexte, souvenir dérivé, correction et portée entre sessions. | Quelques scénarios sans ambiguïté, avec résultat attendu et situations où Lyra doit demander une précision. |
| B. Conservation et reprise | Journal durable, cohérence avec l'état de contrôle, règle de concurrence, déduplication et migration. | Reprise après panne simulée ; aucune réponse rattachée à la mauvaise demande ; anomalies visibles ; retour arrière de migration vérifié sur copie. |
| C. Contexte et interface | Historique rendu visible, navigation, brouillon récupérable, contenu transmis borné et inspectable. | Parcours fermer/reprendre/poursuivre ; origine des réponses conservée ; contenu reçu par un client déterministe vérifiable. |
| D. Mémoire utile et corrigible | Tester correction et sélection des souvenirs ; comparer aux références simples avant d'ajouter une organisation plus élaborée. | Résultats séparant conservation, récupération du passage et justesse de la réponse ; coûts et erreurs de non-pertinence rapportés. |

**Comparateurs envisagés, à préciser :** contexte récent seul ; historique complet lorsqu'il tient dans le budget ; sélection de passages sources ; puis éventuel enrichissement par Nemeton. Garder le modèle et la politique de génération identiques pour comparer les mémoires. Examiner ensuite le contrôle adaptatif dans une comparaison distincte.

Les fenêtres de contexte, modèles locaux retenus, ressources matérielles disponibles, latence acceptable, durées de conservation et portée entre projets ne sont pas fixés par cette fiche. Un nombre de conversations ou de caractères ne remplace pas un budget en tokens qualifié pour le modèle utilisé. [T3]

### Situations minimales à confronter au contrat

Ces cas sont des exemples de conception, pas un jeu de mesure gelé ni une suite déjà exécutée.

| Situation | Comportement candidat à examiner |
|---|---|
| Fermer puis rouvrir | Retrouver les échanges sauvegardés et leur ordre ; distinguer clairement une tentative inachevée. |
| Double clic ou nouvel envoi après délai | Une même tentative ne crée pas deux tours acceptés ; un nouvel envoi intentionnel reste possible. |
| Changer de session pendant une réponse | La réponse tardive reste liée à sa conversation d'origine. |
| « Reprends la deuxième option » | Retrouver la bonne proposition antérieure ou demander laquelle si le contexte est insuffisant. |
| « Le rendez-vous a été déplacé de mardi à jeudi » | Utiliser jeudi pour l'état courant et conserver la possibilité de distinguer ce qui avait été annoncé auparavant. |
| « Mon hypothèse est X », puis demande de critique | Conserver le statut d'hypothèse ; ne pas transformer le souvenir en preuve de X. |
| Question sur un autre projet ou sur un fait absent | Ne pas imposer un souvenir hors sujet ; reconnaître l'information manquante. |
| Ancienne session partiellement récupérable | Montrer la lacune sans reconstruction présentée comme originale. |

**Deux niveaux de validation :** les tests déterministes vérifient la conservation, l'ordre, les contrats et la sélection de contexte. Les essais avec un modèle évaluent ensuite l'usage de ce contexte. Une réussite du premier niveau ne prouve pas la qualité du second. Les futurs essais comparatifs sur données réelles devront définir leur protocole avant mesure ; aucun n'est lancé par cette fiche.

<!-- pagebreak -->

## 4. Sources externes : apports et limites

Revue ciblée réalisée le 5 septembre 2026 : lecture du registre scientifique existant [D3], recherches sur arXiv portant sur la mémoire conversationnelle longue et sur la récupération/compression, lecture des résumés des cinq premiers résultats de chaque requête, approfondissement de méthodes pertinentes et repérage complémentaire sur Semantic Scholar. Ce n'est pas une revue systématique exhaustive.

Les implications ci-dessous sont des propositions pour Lyra. Aucun résultat publié n'est assimilé à une validation de son code ou de ses modèles locaux.

| Source primaire | Résultat ou méthode utile | Limite et conséquence proposée |
|---|---|---|
| [L1. MemGPT - Packer et al., 2023/2024](https://arxiv.org/html/2310.08560) | Organise un contexte limité et des stockages externes ; conserve les messages retirés du contexte et permet leur rappel. | La gestion autonome repose notamment sur les appels de fonctions du modèle. Retenir la distinction stockage/contexte sans adopter toute l'orchestration. |
| [L2. LongMemEval - Wu et al., ICLR 2025](https://arxiv.org/html/2410.10813) | Sépare extraction, raisonnement entre sessions, temporalité, mise à jour et abstention ; distingue récupération et lecture. Remplacer les échanges par des faits ou résumés peut dégrader les réponses détaillées. | Conversations en partie simulées et éditées par des humains ; juge automatique qualifié dans leur cadre. Importer les dimensions d'évaluation et la provenance, pas leurs scores comme seuils locaux. |
| [L3. ConvoMem - Pakhomov et al., 2025, prépublication](https://arxiv.org/html/2511.10523) | Compare historique complet, mémoire avec récupération et approches hybrides sur des corpus croissants ; l'historique complet constitue une référence forte dans plusieurs configurations. | Les analyses utilisent notamment Gemini et Mem0. « 150 conversations » dépend du corpus, du modèle et du coût : aucun seuil équivalent n'est établi pour Lyra. |
| [L4. PersistBench - Pulipaka et al., 2026, prépublication](https://arxiv.org/html/2602.01146) | Examine l'influence inappropriée de souvenirs hors sujet et le renforcement de convictions, avec un contrôle où la mémoire est utile. | Souvenirs synthétiques fournis au modèle et cas recherchés pour déclencher des erreurs ; ne mesure pas toute la construction de mémoire ni leur fréquence en usage naturel. Ajouter des cas d'usage pertinent et de non-utilisation. |
| [L5. EngramaBench - Acuna, 2026, prépublication](https://arxiv.org/html/2604.21229) | Compare un graphe, Mem0 et l'historique complet avec le même modèle de réponse ; avantage du graphe sur une catégorie, pas au score global. | 150 questions, cinq profils ; certaines heuristiques non publiées et coûts de construction exclus. L'étude motive une comparaison, pas le choix automatique d'un graphe. |

### Références d'ingénierie

- [T1. SQLite - transactions](https://www.sqlite.org/transactional.html) et [isolation](https://www.sqlite.org/isolation.html) : garanties à situer à la frontière de la base. La transaction ne couvre pas un appel externe au modèle.
- [T2. AWS Builders' Library - Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) : identifiant de demande, traitement cohérent des répétitions et ambiguïté des délais d'attente. À adapter à une application locale, sans importer une infrastructure distribuée inutile.
- [T3. Ollama - Chat API](https://docs.ollama.com/api/chat) et [Context length](https://docs.ollama.com/context-length) : messages structurés, compteurs retournés et contexte configurable. La version installée, le modèle et le budget réel restent à qualifier.

**Conclusion provisoire de la revue :** le socle conversationnel proposé reste plausible ; le choix d'une mémoire complexe, sa portée entre conversations et les preuves de sa pertinence restent ouverts. Le relecteur est invité à chercher des travaux contraires ou plus directement applicables.

<!-- pagebreak -->

## 5. Périmètre futur, dossier de preuves et réponse demandée

### Frontières à préserver

**P7 n'a pas établi l'avantage adaptatif.** Le statut canonique rapporte une calibration V11 exécutée puis un arrêt avant le test final ; H11 reste `UNTESTED`. Les 60 cas tenus sont réservés à une future évaluation justifiée. Leurs contenus ne sont pas nécessaires à cette relecture et ne doivent pas être ouverts dans ce cadre. Les calculs et interprétations statistiques de P7 ne sont pas revalidés par cette fiche. [D2]

Le cœur de génération est partagé avec des chemins d'évaluation : une évolution P6 doit expliciter sa compatibilité. L'exploration ESMM et les idées de consolidation hors conversation, appelées « Jachère » et « Songe », restent distinctes du premier parcours. Le futur site public de présentation est également distinct de l'exposition du serveur local et de ses données.

**État Git à ne pas confondre avec `main` :** au relevé local du 5 septembre, `origin/main...HEAD` compte un commit propre à `main` et 87 propres à la branche de travail. Le commit de référence ci-dessus doit servir à la lecture ; une intégration dans `main` serait une décision séparée. La note locale non versionnée `Programme P7 · mise à plat.txt` est exclue du dossier et n'est pas nécessaire pour répondre.

### Sources internes, liées au commit étudié

Les liens suivants pointent vers une version précise, indépendante des modifications futures de la branche. En cas de divergence documentaire, vérifier le code et le statut daté ; une description historique n'est pas une preuve d'intégration actuelle.

| Repère | Source à inspecter | Ce qu'elle permet de vérifier |
|---|---|---|
| C1 | [app/main.py, ligne 64](https://github.com/SimonBouhier/lyra_reborn/blob/788971a00f4303d2ba24cc671f4c0049fab772f9/app/main.py#L64) | Tour HTTP, erreurs, sauvegarde, endpoints de session. |
| C2 | [app/session.py, ligne 136](https://github.com/SimonBouhier/lyra_reborn/blob/788971a00f4303d2ba24cc671f4c0049fab772f9/app/session.py#L136) | Assemblage du contexte, graphe, écologie, cas ; états et restauration plus bas. |
| C3 | [app/storage.py, ligne 117](https://github.com/SimonBouhier/lyra_reborn/blob/788971a00f4303d2ba24cc671f4c0049fab772f9/app/storage.py#L117) | Sauvegarde SQLite et validations. |
| C4 / C5 | [core/loop.py, ligne 111](https://github.com/SimonBouhier/lyra_reborn/blob/788971a00f4303d2ba24cc671f4c0049fab772f9/core/loop.py#L111) ; [core/state.py, ligne 51](https://github.com/SimonBouhier/lyra_reborn/blob/788971a00f4303d2ba24cc671f4c0049fab772f9/core/state.py#L51) | Entrée des métriques et historique borné. |
| C6 | [memory/graph/injector.py, ligne 13](https://github.com/SimonBouhier/lyra_reborn/blob/788971a00f4303d2ba24cc671f4c0049fab772f9/memory/graph/injector.py#L13) ; [app/harvest.py](https://github.com/SimonBouhier/lyra_reborn/blob/788971a00f4303d2ba24cc671f4c0049fab772f9/app/harvest.py) | Sélection et bornes des concepts. |
| C7 / C8 | [app/static/index.html, ligne 175](https://github.com/SimonBouhier/lyra_reborn/blob/788971a00f4303d2ba24cc671f4c0049fab772f9/app/static/index.html#L175) ; [core/llm.py, ligne 57](https://github.com/SimonBouhier/lyra_reborn/blob/788971a00f4303d2ba24cc671f4c0049fab772f9/core/llm.py#L57) | Reprise, envoi, réponse tardive ; contrat Ollama. |
| C9 | [Tests HTTP](https://github.com/SimonBouhier/lyra_reborn/blob/788971a00f4303d2ba24cc671f4c0049fab772f9/tests/test_p6_http.py) ; [persistance](https://github.com/SimonBouhier/lyra_reborn/blob/788971a00f4303d2ba24cc671f4c0049fab772f9/tests/test_session_persistence.py) ; [premières couches](https://github.com/SimonBouhier/lyra_reborn/blob/788971a00f4303d2ba24cc671f4c0049fab772f9/tests/test_p6_first_layers.py) | Cas d'isolation, restauration, erreurs et passage contrôle/mémoire. |
| D1 / D2 / D3 | [État actuel](https://github.com/SimonBouhier/lyra_reborn/blob/788971a00f4303d2ba24cc671f4c0049fab772f9/docs/ETAT_ACTUEL.md) ; [statut V11](https://github.com/SimonBouhier/lyra_reborn/blob/788971a00f4303d2ba24cc671f4c0049fab772f9/docs/P7_V11_STATUS.md) ; [registre scientifique](https://github.com/SimonBouhier/lyra_reborn/blob/788971a00f4303d2ba24cc671f4c0049fab772f9/STATE_OF_ART.md) | Résultats rapportés, limites et contexte scientifique antérieur. |

### Format de retour souhaité

1. **Avis général :** poursuivre, réduire le périmètre ou revoir la base ; préciser les limites de votre inspection.
2. **Réponses à Q1-Q6 :** recommandation, alternative crédible, preuve ou source, incertitude restante.
3. **Trois objections prioritaires :** pour chacune, conséquence concrète et moyen de vérifier ou de réfuter le risque. L'absence d'objection doit être motivée, pas recherchée.
4. **Plan amendé :** premier lot réalisable, critères de sortie et conditions qui justifieraient une refonte ou une relecture humaine spécialisée.
5. **Informations réellement manquantes :** distinguer les décisions d'usage à demander au concepteur des choix techniques que l'équipe peut résoudre seule.

**Mandat :** critiquer la cohérence de la base proposée, pas confirmer sa séduction. Signaler explicitement ce qui est constaté, déduit ou hypothétique. Si le code n'a pas été consulté, limiter l'avis à l'architecture décrite. Cette fiche ne demande ni implémentation, ni déploiement, ni campagne expérimentale.
