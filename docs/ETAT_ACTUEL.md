# Lyra — état actuel et limites

**Relecture : 5 septembre 2026. Base du code : `d7353d4`.**
Ce document décrit l'application disponible. Les campagnes conservent leurs
propres documents de statut et leurs préinscriptions.

**Actualisation — 8 septembre 2026, travaux issus de la base `788971a` :**
[A01 concurrence](P6_A01_CONCURRENCE_2026-09-07.md),
[journal et demandes](P6_JOURNAL_DEMANDES_2026-09-07.md), puis
[contexte, corrections et rappels](P6_CONTEXTE_CORRECTIONS_RAPPELS_2026-09-08.md)
réalisés sur la branche `codex/p7-meta-arret`. **73 tests Python et 9 JavaScript réussis** ;
parcours navigateur vérifié avec moteur factice. Un contrôle Gemma réel limité
valide le transport, mais révèle une mauvaise utilisation d'un rappel corrigé.
Qualité d'usage non admise ; aucune migration utilisateur ni mise en service distante.

Le [diagnostic des rappels corrigés](P6_DIAGNOSTIC_RAPPELS_2026-09-08.md) est
achevé : plan exploratoire scellé, quatre appels d'admission technique et
6 336 réponses collectées sur quatre configurations, séparément du produit.
Les 212 tests de l'instrument ont réussi. Les dossiers de relecture externe sont
prêts ; aucune confirmation indépendante ni admission d'usage n'en découle.
Le statut scientifique et les preuves de cette exploration sont suivis dans cette note.

## Application P6

Les nouvelles conversations suivent un profil fixe sans injection automatique
du graphe, du contrôleur ni des cas. L'historique récent conserve les rôles ;
les rappels sont limités aux messages choisis et à leur dernière correction.
Les anciennes conversations de contrôle P0–P2 et mémoire P3 conservent ce profil
historique. Les demandes sont enregistrées avant génération dans un journal SQLite v3.
La réponse destinée à l'affichage et l'état résultant sont validés ensemble.
Les répétitions retrouvent ce résultat ; les relances explicites créent des
tentatives distinctes. Une erreur avant publication conserve l'état durable
précédent. Si le retour arrière échoue, l'objet modifié est retiré du registre
pour imposer une restauration depuis le stockage durable. Une exception après
publication ne retire pas un résultat déjà validé.

La garde A01 protège la conversation pendant son cycle de mutation ; le journal
permet de lire le statut d'une demande en cours. Au démarrage d'un nouveau
registre, les tentatives antérieures encore `en_cours` sont déclarées interrompues,
sans relance automatique. Un seul processus serveur est pris en charge.

Le moteur ESMM P4 existe séparément dans `explore/esmm/`. Aucun des deux parcours
P6 ne l'appelle. L'ancien tour de contrôle récolte des concepts et cooccurrences ;
le nouveau dialogue de référence ne fait pas cette collecte.

### Limites observées

- L'assemblage du dialogue conserve au plus 30 paires récentes dans 16 000
  caractères, avec rappels et message courant obligatoires. Ce plafond n'est pas
  un comptage exact des tokens ; le serveur est configuré pour refuser une
  troncature silencieuse. Le contexte et ses omissions sont inspectables.
- Les corrections sont liées à un message entier et n'effacent pas l'original.
  Les rappels suivent leur dernière correction au prochain usage ; le contexte
  d'une tentative déjà lancée reste figé. Aucun parcours transitif des rappels.
- Le journal, paginé dans la page, conserve les échanges sans expiration.
  La suppression et le traitement des sauvegardes restent à construire.
  Retirer un rappel n'efface pas les réponses qui ont pu reprendre son contenu.
- Le serveur v3 refuse une ancienne base v1 ou v2. La migration préparée crée
  une copie et conserve les profils historiques ; elle n'a pas été exécutée sur
  les conversations de Simon. Le chemin par défaut reste inchangé.
- La navigation entre conversations est disponible. L'adaptateur refuse un
  changement de version/digest moteur ; le déploiement isolé des runtimes et
  leur admission d'usage restent à construire. Qwen n'a pas été exécuté ici.
- Gemma répond correctement à une correction dans la conversation source, puis
  reprend l'ancienne information dans la destination du rappel malgré la correction
  transmise. Ce contre-exemple empêche de qualifier globalement l'usage.
- Le graphe REST, le catalogue/sélecteur de modèles et l'authentification
  minimale restent des travaux d'application.
- Le service reste local, lié à `127.0.0.1`. La base contient les textes en clair.

Le parcours « converser, reprendre, corriger, retrouver » est réalisé techniquement
dans l'application locale. Sa qualification d'usage et l'effacement conforme restent ouverts.

Le [contrat P6 du 7 septembre](CONTRAT_USAGE_P6_v0_2026-09-07.md) précise les
choix actés : conversations séparées, rappel explicite d'un passage,
conservation jusqu'à suppression volontaire. Le guide du journal distingue les
preuves acquises en développement, les scénarios partiellement couverts et les
garanties encore à construire. Le guide du dialogue donne la migration actuelle ;
les preuves de ces étapes ne valent pas acceptation du contrat complet.

## Évaluation et recherches

- **P7 : atelier métrologique**, selon la décision du 31 août.
- V11 a franchi Q0 et exécuté sa calibration, puis s'est arrêtée à Q1.
  **H11 reste `UNTESTED`**. L'avantage adaptatif contre statique n'est pas établi.
- Aucun nouveau gel V12 avant examen conjoint du budget, du contrat, de la
  référence humaine et de la règle de jugement sur données de développement.
- Les 60 cas tenus restent réservés. La revue documentaire ne les a pas ouverts.
- Jachère, Songe et agentivité générale demeurent des travaux à construire ou
  qualifier ; aucune promesse de disponibilité prochaine n'est faite.
- La [note Jachère du 7 septembre](NOTE_ARCHITECTURE_JACHERE_CLOISONNEMENT_2026-09-07.md)
  retient consolidation et recombinaison autonomes, ponts facultatifs et
  résultats séparés. Les anciennes métriques du Songe doivent être révisées
  avant gel ; aucun pont ni travail de fond n'est activé par cette note.

Le statut scientifique canonique est [P7_V11_STATUS](P7_V11_STATUS.md).
Les premières lectures corrigées ne doivent pas être utilisées à la place de
son diagnostic final.

## Organes et branches

- **EPP** : organe d'attestation personnel, blockchain retirée. Le pont
  d'attestation est futur. Le sidecar Vigie est sur une branche EPP séparée ;
  son existence ne signifie pas disponibilité dans `main`.
- **Origami** : série v4–v7 close, résultat v7 0/6 sous son protocole.
  Aucun signal Fisher importé dans Lyra ou EPP.
- **Branche de travail** : `codex/p7-meta-arret`. Au 5 septembre, 85 commits
  sur GitHub hors de `main` au relevé initial, avant publication de la persistance
  `d7353d4`. La branche de travail reste `codex/p7-meta-arret` ; sa publication
  ne constitue pas une fusion dans `main`.
  `main` porte séparément le site statique de démonstration GitHub Pages.
- **Charte de transformation** : PR #1 en brouillon, branche distincte.
  Elle ne doit pas être présentée comme ratifiée ou intégrée.
- La note `Programme P7 · mise à plat.txt` est locale et non versionnée.
- Les traces de campagne (`data/runs/`) et les archives de relecture (`output/`)
  restent locales, ignorées par Git. Leurs liens dans les notes de preuve ne sont
  donc pas consultables sur GitHub. Les sources, le plan scellé, les tests et les
  guides sont versionnés : [reproduire la collecte](../experiments/p6_recall/README.md),
  [exporter les paquets](P6_RAPPEL_EXPORTS_2026-09-08.md),
  [choisir les pièces à transmettre](P6_RELECTURE_MODE_EMPLOI_2026-09-08.md).
- Simon a fourni la référence Opal Gardener, essayée d'abord sur les sites EPP.
  La page Vercel propre à Lyra reste un chantier distinct.
  Elle n'est pas créée par cette mise à jour.

## Vérification datée

Le **8 septembre 2026, instrument de diagnostic : 212 tests réussis**, sans échec,
erreur ni test ignoré. La collecte comporte 6 336 traces terminales techniquement
valides, plus quatre appels d'admission technique, soit 6 340 générations réelles.
Le [rapport de campagne](P6_DIAGNOSTIC_RAPPELS_2026-09-08.md) distingue ces contrôles
de l'exactitude sémantique et de la confirmation indépendante encore à organiser.
Ce bilan ne remplace pas les preuves de l'application ci-dessous.

Le **8 septembre 2026 : 73 Python + 9 JavaScript réussis**, parcours navigateur
avec moteur factice et contrôle local Gemma de trois générations. Le
[guide de cette tranche](P6_CONTEXTE_CORRECTIONS_RAPPELS_2026-09-08.md) référence
les rapports et le contre-exemple sémantique. Simon autorise désormais les tests
directs par l'agent ; aucun rejeu humain systématique n'est exigé.

Le **7 septembre 2026 : 57 tests Python et 7 tests JavaScript réussis** pour
le journal, les demandes, la migration sur bases temporaires, la concurrence,
la persistance et le client de la page. Le DOM est simulé et tous les moteurs
sont factices ; le guide [P6 journal](P6_JOURNAL_DEMANDES_2026-09-07.md) donne
les preuves et leurs limites. La commande destinée à Simon est
`powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verifier_p6.ps1`.
Simon a exécuté cette commande avec succès le même jour à 22 h 29. Les deux
codes de sortie sont 0 et les 19 empreintes du rapport correspondent aux fichiers
présents lors de cette vérification historique. La condition de rejeu PowerShell est satisfaite ; la portée reste celle
des contrôles ciblés simulés, sans qualification avec un modèle réel.

Le **5 septembre 2026 : 127 tests hors ligne réussis**, avec un test live
explicitement exclu. La sélection portait sur les fichiers `test_*.py` sauf
`test_p7_*` et `test_vigie_campaign*`. Elle couvre notamment contrôle, mémoire,
HTTP et persistance. Elle ne remplace pas une nouvelle suite complète ni une
qualification live. Le résultat complet antérieur du 2 septembre était
284 réussis et 2 ignorés, selon le journal de passation.

Commande de la sélection historique du 5 septembre, distincte du contrôle P6
ciblé actuel :

```powershell
Remove-Item Env:LYRA_LIVE -ErrorAction SilentlyContinue
$testFiles = Get-ChildItem tests -Filter 'test_*.py' |
    Where-Object { $_.Name -notmatch '^test_p7_|^test_vigie_campaign' } |
    ForEach-Object { $_.FullName }
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider -k 'not test_live_bridge_on_real_model' @testFiles
```

**Défaut de garde observé, non corrigé ici :** le test live de
`tests/test_bridge.py` traite toute valeur non vide de `LYRA_LIVE` comme
activation, y compris `0`. Le premier passage a donc déclenché un smoke Ollama
qui a reçu une erreur HTTP 500. Aucun runner de campagne n'a été lancé.
