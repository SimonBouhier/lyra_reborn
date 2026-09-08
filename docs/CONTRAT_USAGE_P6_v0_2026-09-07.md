# P6 — contrat court de la première livraison

**Version de travail : v0, 7 septembre 2026.**
**Base examinée :** `788971a00f4303d2ba24cc671f4c0049fab772f9`.

Ce document exécute l'étape documentaire retenue après l'arbitrage des relectures.
Les deux choix de Simon ci-dessous sont actés ; les garanties et le découpage
sont des propositions d'ingénierie. Ce contrat ne constate pas leur réalisation
et ne constitue pas un préenregistrement expérimental scellé.

**Disponibilité des pièces :** les guides et le résultat de concurrence cité
ci-dessous sont versionnés. Les rapports sous `data/runs/`, les exports sous
`output/`, la consolidation privée et le journal personnel des skills restent
locaux, hors publication GitHub. Les liens vers ces pièces locales ne sont pas
des téléchargements publics.

**Avancement local du 7 septembre :** la
[correction A01 de concurrence](P6_A01_CONCURRENCE_2026-09-07.md) est réalisée
et sa première sélection de 34 tests ciblés était réussie. L'étape 2
[journal et cycle des demandes](P6_JOURNAL_DEMANDES_2026-09-07.md) est maintenant
réalisée localement : la sélection élargie donne 57 tests Python et 7 tests
JavaScript réussis en développement, puis rejoués avec succès par Simon dans son
PowerShell à 22 h 29. Le rapport est vérifié et ses 19 empreintes concordent.
La condition de rejeu est satisfaite pour cette étape historique.
Aucune migration de données utilisateur n'a été exécutée.

**Actualisation du 8 septembre :** [contexte, corrections, rappels et navigation](P6_CONTEXTE_CORRECTIONS_RAPPELS_2026-09-08.md)
implémentés localement. 73 Python + 9 JavaScript réussis, navigateur vérifié sur
moteur factice. Le contrôle réel Gemma apporte un contre-exemple d'utilisation
d'une correction malgré sa présence dans le contexte. Qualification d'usage et
suppression restent ouvertes ; aucune acceptation globale de P6 n'est prononcée.
Simon autorise les contrôles directs par l'agent sans rejeu PowerShell obligatoire.
Ses réserves sur les versions des moteurs sont prises en charge par une frontière
d'adaptateur et un contrôle d'identité ; aucune installation n'a été modifiée.

## 1. Usage et décisions actées

**But :** converser en français, fermer Lyra, retrouver les échanges, poursuivre
et corriger une information dans une conversation identifiable.

Simon a choisi le 7 septembre 2026 :

- **Conversations séparées, avec rappel explicite d'un passage.** Aucun partage
  automatique de mémoire entre conversations. Un rappel désigne un passage et
  conserve sa provenance ; il n'autorise pas l'importation du reste de sa source.
- **Conservation jusqu'à suppression explicite, sans expiration automatique.**
  La réduction du contexte envoyé au modèle n'efface pas le journal conservé.

Enveloppe technique proposée : application locale, un utilisateur, un processus
serveur, plusieurs conversations et éventuellement plusieurs onglets. Plusieurs
processus ou une exposition réseau nécessiteraient un contrat supplémentaire.
L'activation d'un modèle réel reste explicite ; Echo demeure une démonstration
technique identifiable.

## 2. Identité, acceptation et interruption

Une **conversation** possède une identité stable. Une **demande** représente un
envoi intentionnel et reçoit son identifiant côté client avant le premier envoi,
y compris lorsque la conversation n'a pas encore d'identifiant serveur connu.
Une **tentative** est une exécution associée à cette demande.

- « Demande enregistrée » signifie que son texte, son identité et son rattachement
  sont conservés durablement, avant la génération. Avant cet accusé, le client
  conserve le message et son identifiant pour pouvoir vérifier ou répéter l'envoi.
- « Réponse enregistrée » signifie que le résultat destiné à l'affichage et
  l'état résultant ont été validés ensemble. Une réponse affichée comme définitive
  doit rester retrouvable après une erreur ultérieure et un redémarrage.
- Une demande possède **au plus un résultat validé**. Le même identifiant et le
  même contenu retrouvent le résultat ou le statut existant. Le même identifiant
  avec un contenu ou une intention de génération différente provoque un conflit
  explicite. Le même texte avec un nouvel identifiant est un nouvel envoi.
- Une relance après échec ou interruption est une tentative identifiable,
  explicitement demandée. Une réponse réseau perdue ne justifie pas de régénérer
  un résultat déjà enregistré. Une exécution physique unique du modèle n'est pas
  garantie lorsqu'une panne survient avant la validation du résultat.
- Une seule tentative peut modifier une conversation à la fois. Proposition
  initiale : signaler « conversation occupée » pour un second envoi, en conservant
  son texte côté client. Une autre conversation peut continuer indépendamment.
- Les états en attente, en cours, interrompu, échoué et terminé sont distinguables.
  Aucune réponse absente n'est inventée. Une erreur interne ou de sauvegarde n'est
  pas systématiquement présentée comme une indisponibilité du modèle.

## 3. Journal, contexte et corrections

Le **journal** conserve les demandes, réponses, rôles, ordre, statuts et liens de
correction. Le **contexte** décrit les passages effectivement transmis, leurs
sources et les omissions. L'**état de contrôle** conserve les réglages et signaux.
Ces responsabilités distinctes n'imposent pas des services séparés ni une copie
intégrale de chaque représentation lorsqu'une référence permet la restitution.

La fidélité porte sur le texte soumis et sur la réponse destinée à l'utilisateur.
Toute normalisation ou transformation pertinente est identifiable. Une réponse
tardive reste rattachée à sa demande, même si l'utilisateur a changé de vue.

La première livraison fournit un geste explicite de correction lié à un passage.
L'original reste consultable comme historique. Lorsqu'il est rappelé dans un
contexte actuel, sa correction doit l'accompagner, ou le passage est exclu avec
un motif visible. La correction d'une déclaration ne la transforme pas en fait
vérifié. La compréhension automatique de toute correction libre est différée.

Le contexte commence par les échanges récents et les passages explicitement
rappelés, avec leurs corrections. Sa politique, le modèle, les réglages et le
budget d'entrée/sortie sont identifiables et conservés à la reprise. Une limite
en caractères ou en tours ne doit pas être annoncée comme un budget exact en
tokens. Si un contenu indispensable dépasse le budget disponible, l'application
explique la limite au lieu de le tronquer silencieusement.

Profil de référence proposé : réglages fixes déclarés, historique explicite,
sans injection Nemeton automatique. Le contrôle adaptatif et les mémoires
dérivées restent des profils expérimentaux distincts. Ce choix facilite
l'interprétation ; aucun avantage de qualité n'est établi par ce contrat.

## 4. Conservation, suppression et anciennes sessions

Le journal n'expire pas automatiquement. Un manque de place provoque un état
explicite et préserve les échanges déjà acceptés ; il ne déclenche pas leur
suppression silencieuse.

Une suppression volontaire vise la conversation et ses dérivés gérés par Lyra.
Les copies de sauvegarde encore présentes sont signalées ; une restauration
gérée doit respecter les suppressions actées. L'application ne doit pas annoncer
un effacement complet tant que des copies concernées restent dans son périmètre
de gestion. Le mécanisme de traitement des sauvegardes sera précisé avant la
livraison de cette opération. Les exports manuels et l'effacement physique du
support ne sont pas garantis par cette opération.

La migration part d'une copie cohérente et récupérable. Le chargeur v1 conserve
ses validations ; le nouveau format possède ses propres invariants versionnés.
Les données récupérées, les transformations et les lacunes sont distinguées.
Une ancienne réponse absente n'est pas présentée comme fidèlement reconstituée.

## 5. Scénarios d'acceptation à vérifier pendant le développement

Ces scénarios décrivent les preuves attendues du contrat complet. Leur couverture
actuelle, partielle, est détaillée dans les guides du journal et du dialogue ; ce tableau ne
constitue pas un constat d'acceptation.

| ID | Situation | Résultat exigé |
|---|---|---|
| A01 | Une réponse réussit pendant qu'une autre demande échoue | La réponse acceptée reste présente après le tour suivant et après redémarrage. |
| A02 | La première réponse réseau est perdue | Le client retrouve la demande grâce à son identité, même sans connaître encore l'identifiant serveur de conversation. |
| A03 | Un envoi est répété | Même identité : aucun second résultat validé ; identité neuve : nouvelle demande ; contenu différent sous la même identité : conflit. |
| A04 | Arrêt après acceptation de la demande, avant validation du résultat | Demande retrouvable, interruption visible et relance explicite ; aucune réponse fabriquée. |
| A05 | Changement de conversation pendant une génération | La réponse rejoint sa conversation d'origine et ne remplace pas le fil courant. |
| A06 | Fermeture et reprise | Textes conservés, ordre, corrections et profil sont retrouvés. |
| A07 | Rappel d'un passage ancien corrigé | Le contexte actuel comporte sa correction ou indique pourquoi le passage a été exclu. |
| A08 | Limite de contexte atteinte | Messages retenus, omissions et budget sont inspectables ; les échanges restent dans le journal. |
| A09 | Migration d'une archive incomplète | Lacunes explicites, aucune réponse inventée, original récupérable. |
| A10 | Suppression puis restauration gérée | La suppression actée est respectée et les copies résiduelles éventuelles sont signalées. |

Les contrôles déterministes qualifient conservation, identité et contenu transmis.
Une qualification distincte avec un modèle réel devra examiner la poursuite en
français, les références aux échanges précédents et l'utilisation des corrections.
Les résultats des deux niveaux restent séparés.

## 6. Ordre de réalisation et limites

1. **Correction circonscrite de concurrence :** couvrir récupération de session,
   capture, mutation, validation et retour arrière ; satisfaire A01 avant
   d'élargir le stockage. Une protection prise après récupération d'une référence
   périmée serait insuffisante.
2. **Journal et cycle de demande :** identité, statuts, reprise réseau et cohérence
   avec l'état, puis migration préparée. Pas de transaction SQLite maintenue
   ouverte pendant une génération longue.
3. **Tranche conversationnelle :** reprise visible, navigation, contexte,
   corrections et suppression conforme au contrat.
4. **Qualification d'usage**, puis comparaison des enrichissements utiles dans
   un chantier séparé.

Au 8 septembre, la tranche 3 est réalisée pour navigation, contexte et corrections ;
la suppression et les sauvegardes constituent le reste explicite. Le rappel porte
sur un message entier et suit sa dernière correction au prochain usage. Chaque
tentative garde son contexte initial. Le contrôle réel limité ne clôt pas l'étape 4.

À préciser avant les étapes qui en dépendent : modèle et budget réellement
disponibles, délai d'attente et abandon d'une tentative, limites de stockage,
traitement des sauvegardes lors d'une suppression. Ces paramètres ne retardent
pas la préparation de la correction A01.

P7, ses données réservées, l'agentivité générale, Jachère et les ponts vers EPP
restent hors de cette livraison. Aucun push, déploiement ou migration de données
réelles n'est autorisé par ce document seul.

## 7. Fondements et conditions de révision

La consolidation privée des relectures conserve les désaccords et leur origine
dans le fichier local
`docs/relectures/2026-09-05_base_conversationnelle/CONSOLIDATION_v1_2026-09-05.md`,
non publié. Le
[résultat de concurrence](relectures/2026-09-05_base_conversationnelle/preuves/concurrence_2026-09-05.json)
est une reproduction avec client factice et bases temporaires, réalisée le
5 septembre ; il ne mesure pas la fréquence en usage réel. L'écart de mandat
de cette reproduction est consigné dans le journal méthodologique personnel
`C:\Users\simon\.codex\skills\gatekeeper\references\events.jsonl`, local et non publié.

Réexaminer le contrat si la portée d'usage change, si plusieurs processus deviennent
nécessaires, si les limites du modèle rendent la politique de contexte inadéquate
ou si l'extension révèle des couplages incompatibles avec les garanties exigées.
L'auteur ayant participé au plan, le contrat doit rester contestable par ces
preuves et par les scénarios d'acceptation.

## 8. Articulation avec la Jachère — 7 septembre 2026

La [note de cloisonnement Jachère](NOTE_ARCHITECTURE_JACHERE_CLOISONNEMENT_2026-09-07.md)
prévoit consolidation et recombinaison autonomes, avec des ponts facultatifs.
Elle confirme la séparation journal / contexte / mémoire dérivée et la portée
des conversations décidée ici. Elle n'ajoute pas la réalisation de la Jachère
aux conditions de livraison P6. La reprise commence par la correction de
concurrence A01, puis suit l'ordre de la section 6.
