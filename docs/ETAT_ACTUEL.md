# Lyra — état actuel et limites

**Alignement documentaire : 9 septembre 2026.** Ce document fait autorité sur
l'application disponible, ses intégrations et ses limites. Les statuts de
campagne font autorité sur leurs résultats scientifiques ; le
[plan d'édification](PLAN_EDIFICATION.md) porte la trajectoire et le
[registre des intentions](REGISTRE_INTENTIONS.md) conserve les objectifs.
Les résultats du 5 au 8 septembre ci-dessous sont historiques. Le rejeu
technique du 9 septembre est identifié séparément. La [carte des branches](BRANCHES.md) distingue
l'intégration locale de la publication distante.

**P6 permet techniquement de converser, reprendre, corriger et rappeler dans
une application locale.** Le journal SQLite v3, la navigation, les corrections
liées et les rappels explicites sont implémentés. Les contrôles déterministes
ne constituent pas une admission d'usage : le contrôle Gemma a conservé un
contre-exemple d'emploi d'une correction. La suppression volontaire et le
traitement des sauvegardes restent à réaliser. Le jalon d'alpha privée n'est
pas déclaré livré.

## Maturité et nature des appuis

La maturité distingue **intention → spécifié → implémenté → vérifié
techniquement → qualifié en usage → admis dans un périmètre**. Un contrôle
technique ne fait avancer que les garanties qu'il exerce. La nature de l'appui
est un autre axe : intuition interne, bibliographie, contrôle déterministe,
essai réel ou campagne confirmatoire. Les résultats `UNTESTED`, `INVALID`,
`INCONCLUSIVE`, arrêts et réfutations conservent leur sens propre.

| Objet | Maturité et intégration observées | Nature et portée de l'appui |
|---|---|---|
| P6 — dialogue de référence et journal | Implémentés ; garanties techniques vérifiées sur les scénarios datés ; qualification et admission d'usage ouvertes | Contrôles déterministes, navigateur factice, essai Gemma limité avec contre-exemple ; [guide produit](P6_CONTEXTE_CORRECTIONS_RAPPELS_2026-09-08.md) |
| P1–P2 — contrôle et pont | Implémentés dans `LyraLoop` et le profil historique ; absents du dialogue fixe | Code, contrôles ciblés et essais historiques de modulation ; aucun avantage adaptatif général établi |
| P3 — Nemeton, écologie et ispace | Primitives implémentées dans le profil historique ; aucune injection automatique dans le dialogue fixe | Contrôles déterministes des primitives et de leur parcours ; pas de bénéfice mémoriel général admis |
| P4 — ESMM | Moteur implémenté séparément ; aucun appel depuis les deux parcours P6 | Code, tests propres et essai productif historique ; pas de qualification générale ni d'admission dans le dialogue |
| P5 — agentivité générale, outils et SilenceØ | Programme à construire ; frontière Vigie spécifique existante | Contrats et contrôles ciblés de quarantaine ; aucune autonomie générale admise |
| Jachère, Songe, Pouponnière évolutive | Intentions conservées ; orientation retenue, contrats techniques proposés ; fonctions complètes à construire et qualifier | Intuitions, bibliographie antérieure à examiner et scénarios proposés ; aucun bénéfice local établi |
| Traces résiduelles et transformation paramétrique | Intentions à spécifier et étudier séparément | Essai conceptuel et pistes bibliographiques ; ni influence résiduelle ni entraînement local admis |

Les correspondances concrètes suivent. Le [BUILD_STATUS](../BUILD_STATUS.md)
indexe les composants et leur provenance sans déclarer une seconde maturité globale.

## Application P6

Les nouvelles conversations sont des
[`DialogueConversation`](../app/dialogue.py), créées par
[`app/main.py`](../app/main.py). Leur profil `conversation_reference_v1`
emploie des réglages fixes, l'historique récent avec ses rôles et les passages
explicitement rappelés. Le graphe, le contrôleur et le banc de cas ne sont pas
injectés automatiquement. L'activation d'un modèle réel est explicite ; créer
une conversation ne lance pas à soi seul une génération réelle.

Les anciennes conversations [`LyraConversation`](../app/session.py)
conservent leur profil de contrôle P0–P2 et mémoire P3. Leur chargement ne les
convertit pas en dialogue de référence. Elles n'utilisent pas les corrections
comme le nouveau profil ; ouvrir une conversation de référence pour ce parcours.

[`RequestService`](../app/requests.py) enregistre la demande avant génération
au [journal](../app/journal.py). La réponse destinée à l'affichage et l'état
résultant sont validés ensemble. Les répétitions retrouvent ce résultat ; les
relances explicites créent des tentatives distinctes. Une erreur avant
publication conserve l'état durable précédent. Si le retour arrière échoue,
l'objet modifié est retiré du registre pour imposer une restauration durable.
Une exception après publication ne retire pas un résultat déjà validé.

La [garde A01](P6_A01_CONCURRENCE_2026-09-07.md) protège le cycle de mutation
par conversation ; le statut d'une demande en cours reste lisible. Au démarrage
du registre, les tentatives antérieures encore `en_cours` deviennent interrompues,
sans relance automatique. **Un utilisateur et un seul processus serveur**
constituent l'enveloppe technique actuelle.

### Limites de contexte, conservation et moteur

- Le profil conserve au plus 30 paires récentes dans 16 000 caractères, avec
  rappels et message courant obligatoires. Ce plafond n'est pas un comptage
  exact des tokens ; le serveur est configuré pour refuser une troncature
  silencieuse. Le contexte retenu et ses omissions sont inspectables.
- Les corrections portent sur un message entier et conservent l'original.
  Les rappels suivent sa dernière correction au prochain usage ; le contexte
  d'une tentative déjà lancée reste figé. Aucun parcours transitif des rappels.
- Le journal paginé conserve les échanges sans expiration. **Suppression,
  sauvegardes et restauration respectant les suppressions restent à construire.**
  Retirer un rappel n'efface pas les réponses qui ont repris son contenu.
- Le serveur v3 refuse une ancienne base v1 ou v2. La migration préparée crée
  une copie et conserve les profils historiques ; elle n'a pas été exécutée
  sur les conversations de Simon. Le chemin par défaut reste inchangé.
- L'[adaptateur chat](../app/chat_backend.py) refuse un changement de version
  ou de digest moteur. Son contrat courant est limité à Ollama 0.33.3 ; le
  [guide produit](P6_CONTEXTE_CORRECTIONS_RAPPELS_2026-09-08.md) donne l'identité
  exacte du contrôle Gemma. Cela ne qualifie pas tous les modèles de ce runtime.
  L'isolation des runtimes et leur admission d'usage restent à construire.
- Dans l'essai Gemma, la correction est utilisée dans la conversation source,
  puis l'ancienne information réapparaît dans la destination malgré la correction
  transmise. Ce contre-exemple empêche de qualifier globalement l'usage.
- Le graphe REST, le catalogue/sélecteur de modèles et l'authentification
  minimale restent des travaux d'application. Le déploiement prévu conserve
  l'écoute sur `127.0.0.1` ; aucune exposition réseau publique n'est qualifiée.
  La base contient les textes en clair.

Le [contrat P6](CONTRAT_USAGE_P6_v0_2026-09-07.md) garde ses décisions actées :
conversations séparées, rappel explicite d'un passage, conservation jusqu'à
suppression volontaire. Ses garanties A01–A10 restent le contrat complet à
satisfaire ; les preuves des étapes techniques n'en valent pas acceptation.
L'alpha privée vise « converser, reprendre, corriger, rappeler, supprimer ».
Après sa stabilisation, le [plan](PLAN_EDIFICATION.md) prévoit des tranches
d'intégration du contrôle, des mémoires dérivées, de l'exploration et de
l'agentivité, avec le profil fixe conservé comme témoin. P6 ne résume pas
l'ambition de Lyra.

## Correspondance entre les organes et le code

| Terme ou voie | Réalisation présente | Frontière actuelle |
|---|---|---|
| Contrôle P1–P2 | [`LyraLoop`](../core/loop.py) applique le mapping des boutons, mesure des propriétés textuelles et module l'état ; avec `PIController`, le pont fournit les signaux au P+I | Proxies observables, sans qualité supérieure ni perception subjective démontrées ; volet topologique reporté selon la décision du 18 juillet |
| Autopilote | `run_autopilot` et [`measures.py`](../core/control/measures.py) régulent une dynamique synthétique | Démonstration de loi de commande sans génération de texte |
| Nemeton | [`GraphStore`](../memory/graph/store.py) : graphe non orienté typé, bornes, deltas inversibles en mémoire, compaction et sérialisation ; [injecteur borné](../memory/graph/injector.py) | Le profil historique récolte concepts et cooccurrences. Ce graphe n'est ni le journal source, ni un inventaire de relations vraies, ni une mémoire consolidée qualifiée |
| Primitif du Songe | `GraphStore.is_novel_link` vérifie l'absence d'arête directe et de voisin commun, avec filtre de hubs optionnel | Test structurel à deux sauts ignorant le type des relations ; ne démontre aucune nouveauté sémantique et ne constitue pas une boucle de Songe |
| Écologie mémorielle | [`MemoryEcology`](../memory/ecology/ecology.py) trie en pouponnière, oubli différé et compost ; réévaluation et réveil disponibles comme méthodes | Le profil historique appelle le triage, sans travail autonome hors tâche établi ; la dormance ne remplace pas la suppression du journal |
| ispace / Memento / Navigator | [`memento.py`](../memory/cbr/memento.py) retrouve des cas par cosinus sur six caractéristiques d'état et propose des cibles selon quatre stratégies | Le profil historique appelle `case_guided`. Primitives de rappel/navigation, sans espace latent appris ni projection générale d'identité ; état → options reste dans `core/knobs.py` |
| Surface affective | [`AffectiveSurface`](../core/affect.py) dérive un affichage de valence depuis les signaux du pont ; option désactivée par défaut dans `LyraLoop` | Affichage sans second pilote des réglages ; aucune émotion ressentie démontrée |
| Exploration ESMM | [`explore/esmm/`](../explore/esmm/) : lacunes, exploration séquentielle, consensus sémantique et inscription de triplets | Ni `LyraConversation` ni `DialogueConversation` ne l'appelle ; intégration applicative et qualification de l'apport à faire |

Les sources de contrôles correspondantes incluent
[mémoire intégrée](../tests/test_memory_integration.py),
[graphe](../tests/test_graph_store.py), [écologie](../tests/test_ecology.py),
[cas et navigation](../tests/test_cbr.py),
[premières couches P6](../tests/test_p6_first_layers.py) et
[persistance](../tests/test_session_persistence.py). Leur présence et les
résultats historiques ne sont pas présentés comme un nouveau rejeu.

## Jachère, Songe et fonctions futures

La [note Jachère du 7 septembre](NOTE_ARCHITECTURE_JACHERE_CLOISONNEMENT_2026-09-07.md)
fait référence pour l'orientation : consolidation de mémoire, recombinaison et
sélection de modules ont des résultats, droits et budgets propres ; leurs
ponts sont facultatifs. Ses contrats techniques et scénarios J01–J16 restent
à implémenter et qualifier. Aucun travail de fond ni pont n'est activé par la note.

La **Pouponnière évolutive** vise génération, évaluation, sélection et adoption
ou compostage de modules de scaffold. Elle est distincte de la strate mémorielle
nommée pouponnière. Le **Songe** conserve consolidation et recombinaison comme
fonctions autonomes, ainsi que l'horizon d'une consolidation paramétrique future ;
les opérations sur contexte, graphe ou scaffold ne prouvent pas une modification
des poids.

Les [métriques du Songe](METRIQUES_SONGE.md) sont des **candidates à réviser
avant gel**. Les appuis bibliographiques antérieurs ne prouvent ni identité
de mécanisme avec Lyra ni bénéfice local. Nouveauté structurelle, modularité
et présence d'un candidat utile ne suffisent pas à établir l'effet causal de
la méthode. Aucune qualification du Songe n'est acquise.

Les [traces résiduelles](ESSAI_TRACES_RESIDUELLES.md) restent une intention
distincte : influence conditionnelle, faible, bornée et décroissante, avec
possibilité de rester sans effet. Elles ne justifient aucune injection
automatique dans la P6 de référence.

La note permet des admissions automatiques selon une politique approuvée et
qualifiée ; elle n'impose pas une décision humaine pour chaque résultat.
La [charte de transformation](../manifeste/CHARTE_TRANSFORMATION.md) conserve
son statut de **texte candidat à ratification**. Sa récupération documentaire
ne ratifie pas le texte ni ne confère au système l'autorité exclusive de sa
transformation. Le [registre](REGISTRE_INTENTIONS.md) conserve aussi les
questions ouvertes de continuité, contrôle, agentivité et vocabulaire.

## Évaluation et recherches

**P7 reste un atelier métrologique.** Le statut canonique de V11 est
[`V11_ARRETEE_APRES_CALIBRATION` — H11 `UNTESTED`](P7_V11_STATUS.md).
Q0 a été franchie, la calibration exécutée, puis Q1 a arrêté la campagne.
L'avantage adaptatif contre statique n'est pas établi ; H11 n'est pas réfutée.
Les 60 cas tenus restent réservés et n'ont pas été consultés pour cet alignement.

Une reprise exige une question nommée, un budget, une condition d'arrêt et les
[neuf conditions post-V11](CADRAGE_EXTERNE_P6_P7_POST_V11.md#9-conditions-dentrée-dune-éventuelle-v12) :
budget/contrat, effet de longueur, sensibilité à la position, règle de jugement,
référence humaine, adjudication/TIE/INVALID, version distincte de l'instrument,
justification du jeu tenu et maintien de P6 exploitable en cas d'échec.
Aucun nouveau gel V12 ni campagne n'est lancé par cet alignement.
La Jachère exige des mesures adaptées à ses fonctions ; cela n'impose pas de
rouvrir H11 ni de « terminer P7 » avant de préciser ses contrats.

Le [diagnostic exploratoire P6 des rappels](P6_DIAGNOSTIC_RAPPELS_2026-09-08.md)
est séparé de l'application et de P7 : plan exploratoire scellé, quatre
admissions techniques et 6 336 réponses collectées sur quatre configurations.
Les dossiers de relecture sont prêts ; aucune confirmation indépendante ni
admission d'usage n'en découle. Une réponse techniquement valide peut être
sémantiquement incorrecte. Le diagnostic ne rouvre pas automatiquement la série H.

## Preuves datées et accès

**Rejeu du 9 septembre — alignement local :** après les fusions Pages et
charte (base d'intégration `cd73735`), le script existant
[`verifier_p6.ps1`](../scripts/verifier_p6.ps1) a réussi **73 tests Python et
9 tests JavaScript**, avec moteurs factices, SQLite temporaire et DOM simulé.
Rapports locaux, non téléchargeables depuis GitHub :
`data/runs/p6-verification/20260909-111547-fdbc5f0e7ef34a96a5b54eeef93984bd/`
(`verification.json`, `pytest.xml`, `pytest.log`, `javascript.log`). Le manifeste
conserve les empreintes des fichiers exercés. L'avertissement de dépréciation
Starlette/httpx n'a pas causé d'échec ; aucun runtime n'a été mis à jour.
Ce rejeu ne qualifie ni l'usage sur modèle réel ni le rendu navigateur.

| Date et objet | Résultat historique rapporté | Portée et source |
|---|---|---|
| 8 septembre — produit P6 | 73 tests Python + 9 JavaScript réussis ; parcours navigateur factice ; trois générations Gemma | Conservation, contexte, API, migration sur copie et client ; contre-exemple sémantique conservé dans le [guide produit](P6_CONTEXTE_CORRECTIONS_RAPPELS_2026-09-08.md) |
| 8 septembre — instrument de diagnostic | 212 tests réussis ; 6 336 traces terminales techniquement valides + quatre admissions, soit 6 340 générations | Instrument séparé, corpus synthétique et collecte ; pas une confirmation indépendante. [Rapport](P6_DIAGNOSTIC_RAPPELS_2026-09-08.md) et [index d'empreintes](preuves/P6_MANIFESTE_PUBLIC_2026-09-08.json) |
| 7 septembre — journal et demandes | 57 Python + 7 JavaScript réussis, puis rejeu Simon à 22 h 29 ; 19 empreintes concordantes lors du contrôle historique | Clients factices, SQLite temporaire, DOM simulé ; [guide](P6_JOURNAL_DEMANDES_2026-09-07.md) |
| 5 septembre — sélection hors ligne historique | 127 tests réussis ; un test live explicitement exclu | Contrôle, mémoire, HTTP et persistance ; périmètre conservé dans l'historique Git de cette page ; aucune qualification live générale |

Les traces `data/runs/` et exports `output/` sont locaux et ignorés par Git.
Les liens vers ces traces dans les guides ne sont pas des téléchargements
GitHub. Sources, plans et guides versionnés permettent de
[reproduire le diagnostic](../experiments/p6_recall/README.md),
[exporter les paquets](P6_RAPPEL_EXPORTS_2026-09-08.md) et
[choisir les pièces à transmettre](P6_RELECTURE_MODE_EMPLOI_2026-09-08.md).
L'index public d'empreintes ne remplace pas les pièces locales ni une réplication.

Le contrôle hors ligne ciblé est décrit par
[`scripts/verifier_p6.ps1`](../scripts/verifier_p6.ps1). Le défaut de garde
historique de `tests/test_bridge.py` reste connu : toute valeur non vide de
`LYRA_LIVE`, y compris `0`, active son test réel. Le script P6 ciblé retire
temporairement cette variable. Seul le paragraphe « Rejeu du 9 septembre »
désigne son exécution dans le présent alignement.

## Organes et présentation

EPP demeure un organe distinct, hors de cet alignement ; aucun pont courant
ni disponibilité inter-dépôts n'est déduit du sidecar historique. La frontière
Vigie de Lyra est documentée dans [VIGIE_QUARANTINE](VIGIE_QUARANTINE.md).
Origami n'est conservé ici que pour la trace de sa série v4–v7 close, résultat
v7 0/6 sous son protocole ; aucun signal Fisher importé dans Lyra ou EPP.
La doctrine reste dans [ORGANES_ET_PONTS](ORGANES_ET_PONTS.md).

Le site statique présente le projet ; il n'est pas l'application P6.
L'état des branches, la provenance des apports Pages et de la charte, et la
distinction entre `main` locale et distante sont consignés uniquement dans la
[carte datée](BRANCHES.md). Une intégration locale n'établit pas la conformité
du site public. La page Vercel inspirée d'Opal Gardener reste un chantier distinct.
