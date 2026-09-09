# Carte des branches — alignement local du 9 septembre 2026

Relevé daté, pas compteur permanent. Sources : références locales enregistrées
avant opération, `git merge-base --is-ancestor`, identifiants d'arbres et merges
ci-dessous. Aucun fetch ni contrôle distant frais : `origin/*` désigne ici des
références connues localement. [État de l'application](ETAT_ACTUEL.md),
[intentions conservées](REGISTRE_INTENTIONS.md), [ordre des chantiers](PLAN_EDIFICATION.md).

## Point de départ et intégration

La branche de travail `codex/p7-meta-arret` était à
`15bcede4d1b876821524dd1f6d53c51879497c6a`, avec index et worktree propres et un
seul worktree. main locale était à `b8a1079b7329a192cd4731a87932f5c2a330d4f0` ;
origin/main connue à `0dd08094100df9e40ad378493f19c289da2f91a7`.
`origin/main...HEAD` donnait **1 / 90** : divergence, pas simple retard.
Aucun tag ni opération Git interrompue n'a été trouvé.

La branche `codex/alignement-conservatoire-2026-09-09` part de la pointe de
travail, puis conserve les contributions par deux fusions sans squash :

| Fusion | Commit | Apport propre vérifié |
|---|---|---|
| origin/main connue | `c47b3d9` | Trois pages, feuille de style, `.nojekyll`, workflow Pages |
| charte de transformation | `cd73735` | [Texte candidat](../manifeste/CHARTE_TRANSFORMATION.md), conservé intégralement ; aucune ratification implicite |

Les commits documentaires `b99d22d` et `faa64f1` appartiennent à cette branche
d'intégration. **main locale a été avancée en fast-forward à `faa64f1` après
les contrôles disponibles**, puis reçoit le relevé de livraison sur la même
filiation. La pointe attendue a été relue et l'ascendance vérifiée par
`git merge-base --is-ancestor` ; `git update-ref` avec l'ancienne pointe attendue
effectue l'avance atomique. main n'était ouverte dans aucun worktree. Cette
méthode évite un aller-retour par l'ancien arbre et ses conversions de fins de
ligne ; elle ne force ni divergence ni réécriture. main et la branche
d'intégration portent le même état à la livraison.

**Réserve de livraison : rendu navigateur non observé dans cette session.**
Le script P6 a réussi 73 tests Python et 9 JavaScript ; les trois pages et leurs
liens internes répondent en HTTP local. `agent-browser` n'est pas disponible
et l'inventaire du connecteur de navigateur est vide. Ces contrôles ne remplacent
pas une observation visuelle ni un parcours navigateur frais du README.
La revue documentaire et la conservation Git sont vérifiées ; le lot A–D
reste à compléter sur ce contrôle visuel avant de le déclarer entièrement vérifié.
Le rapport local `output/lyra-alignement-2026-09-09/LIVRAISON.md`, dans le
workspace parent, conserve les pointes exactes et les limites des preuves.
Toutes les branches historiques restent conservées ; aucune suppression prévue.

## Classement exhaustif des références de départ

Chaque groupe ci-dessous partage exactement le même commit. L'ascendance a
été contrôlée après les deux fusions ; l'égalité des arbres Pages a été
contrôlée indépendamment. Un nom de branche ne sert pas de preuve d'intégration.

| Références de départ | Commit complet | Destination et preuve |
|---|---|---|
| `codex/environment-hygiene`<br>`origin/codex/environment-hygiene` | `ad00853edba74b7fd5acc3cae8f11a5a9ba902b7` | Intégrée : commit ancêtre de l’intégration. |
| `codex/lyra-transformation-charter`<br>`origin/codex/lyra-transformation-charter` | `e9c45740d76a94b4fefd9a9be64cd2a1663ddc7c` | Intégrée : commit ancêtre de l’intégration. |
| `codex/p7-judge-backend-bench`<br>`origin/codex/p7-judge-backend-bench` | `d6297d1667f4560592b9e039725150600af51e15` | Intégrée : commit ancêtre de l’intégration. |
| `codex/p7-meta-arret`<br>`origin/codex/p7-meta-arret` | `15bcede4d1b876821524dd1f6d53c51879497c6a` | Intégrée : commit ancêtre de l’intégration. |
| `codex/p7-policy-eval-v3`<br>`origin/codex/p7-policy-eval-v3` | `f8ed91a6f65b4da6cdd22d62fc9a34d0c0ad0b56` | Intégrée : commit ancêtre de l’intégration. |
| `codex/p7-policy-eval-v4`<br>`origin/codex/p7-policy-eval-v4` | `b90fe61a84ff7e85285a7af0702f3ac2cb286e01` | Intégrée : commit ancêtre de l’intégration. |
| `codex/p7-policy-eval-v5`<br>`origin/codex/p7-policy-eval-v5` | `d2ae569cb6f9c3aff817942cc5ba601e05fd8add` | Intégrée : commit ancêtre de l’intégration. |
| `codex/p7-policy-eval-v6`<br>`origin/codex/p7-policy-eval-v6` | `7e64060d26560051ed0073dfd1fe73b6e0b9a2b8` | Intégrée : commit ancêtre de l’intégration. |
| `codex/p7-policy-eval-v7`<br>`origin/codex/p7-policy-eval-v7` | `e8e5c6bd127264a0a5c7053ae90a65b694437360` | Intégrée : commit ancêtre de l’intégration. |
| `codex/p7-policy-eval-v8`<br>`origin/codex/p7-policy-eval-v8` | `252f832a0bb8bebee17b4b30b77d460d0b84ff47` | Intégrée : commit ancêtre de l’intégration. |
| `codex/p7-policy-eval-v9`<br>`origin/codex/p7-policy-eval-v9` | `f3ef6422c6f3ad59534ee9e9e77b19f7a46bfdd5` | Intégrée : commit ancêtre de l’intégration. |
| `codex/p7-qwen38-admission`<br>`origin/codex/p7-qwen38-admission` | `0c2489e16b36c6e034a3cfde1330b13f3bf0a1b2` | Intégrée : commit ancêtre de l’intégration. |
| `codex/p7-v10-q1`<br>`origin/codex/p7-v10-q1` | `cdd7ff8b98c76fcca66d26dd871f5e8c1979aa5f` | Intégrée : commit ancêtre de l’intégration. |
| `codex/vigie-shadow-campaign-v1`<br>`origin/codex/vigie-shadow-campaign-v1` | `fb9faf92230072052f021707b8b7557911734cd1` | Intégrée : commit ancêtre de l’intégration. |
| `codex/vigie-shadow-campaign-v2`<br>`origin/codex/vigie-shadow-campaign-v2` | `77040ee61b8e54cdce12da34081902a3c8fe8a11` | Intégrée : commit ancêtre de l’intégration. |
| `main` | `b8a1079b7329a192cd4731a87932f5c2a330d4f0` | Intégrée : commit ancêtre de l’intégration. Pointe initiale de main locale, conservée par sauvegarde après son avance en fast-forward. |
| `origin/main` | `0dd08094100df9e40ad378493f19c289da2f91a7` | Intégrée : commit ancêtre de l’intégration. |
| `origin/qa/github-pages-smoke` | `2ddf6eb543dbdf51ad8587f4ea6c7ba082f7f1a1` | Redondante en contenu avec origin/main de départ (arbres identiques), commit non ancêtre ; provenance et branche conservées. |

## Protection et retour

Références locales créées sans remplacer de référence existante, puis résolues
et comparées au commit attendu :

| Référence de sauvegarde | Commit vérifié |
|---|---|
| `backup/alignement-2026-09-09/charte` | `e9c45740d76a94b4fefd9a9be64cd2a1663ddc7c` |
| `backup/alignement-2026-09-09/main-locale` | `b8a1079b7329a192cd4731a87932f5c2a330d4f0` |
| `backup/alignement-2026-09-09/origin-main` | `0dd08094100df9e40ad378493f19c289da2f91a7` |
| `backup/alignement-2026-09-09/qa-pages` | `2ddf6eb543dbdf51ad8587f4ea6c7ba082f7f1a1` |
| `backup/alignement-2026-09-09/travail` | `15bcede4d1b876821524dd1f6d53c51879497c6a` |

Un bundle local `output/lyra-alignement-2026-09-09/avant.bundle`, dans le
workspace parent Triptique, complète ces références : `git bundle verify`
confirme un historique complet avec 39 références. Il contient uniquement
le contenu Git suivi. Retour possible par nouvelle branche ou worktree sur
une référence de sauvegarde, ou par revert d'un commit selon le cas ; aucun
reset destructeur ni restauration aveugle de changements utilisateur.

Le même dossier local contient `refs-before.txt`, `tracked-tree-before.txt`
et `status-before.txt`. L'inventaire d'arbres enregistre les identifiants de
blobs sans ouvrir les contenus, y compris les fixtures/contrats/empreintes.
Ces artefacts locaux ne sont pas des téléchargements publics.

## Preuves conservées et données locales

Les préenregistrements v1–v11, statuts de campagnes, amendements, contrats
d'admission, `P7_META_ARRET.md`, fixtures, seeds et le couple
`experiments/p6_recall/v1/PLAN_EXPLORATOIRE_v1.md` / `.sha256` sont conservés.
Le contrôle final compare les blobs et vérifie que seuls les documents actifs
et supports de présentation prévus ont changé. Les sceaux détachés disponibles
dans les runs restent à leur emplacement ; ce relevé ne prétend pas qu'un
fichier `.sha256` suivi accompagne chaque préenregistrement.

Les règles de [`.gitignore`](../.gitignore) distinguent notamment :

- `data/runs/` et `output/p6-recall/` : preuves et exports locaux ignorés ;
- `data/*.db`, `data/*.sqlite*` : bases locales, non ouvertes ni migrées ;
- corpus Vigie capturés et labels, retours de relecture, diagnostics privés :
  restent locaux selon leurs règles d'exclusion ;
- `docs/pdfs/` et `docs/*.pdf` : cache de lecture tiers, non redistribué ;
- `.env`, clés et secrets : hors contenu suivi, non lus.

Les sauvegardes Git **ne protègent pas** ces données ignorées. Aucun nettoyage,
déplacement ou copie privée vers Git n'a été effectué. Le seul nouveau run
est la régression P6 autorisée, avec données factices et bases temporaires.
L'inventaire n'ouvre pas les 60 cas tenus et ne lance aucune campagne.

## Frontière de publication

main locale réconciliée ne signifie pas main publique mise à jour.
origin/main connue reste inchangée. Un futur push sur main comprenant ces
fichiers satisfait les filtres du [workflow Pages](../.github/workflows/pages.yml)
et peut déployer `site/` sur GitHub Pages. Il exige une demande explicite de
publication ; la présente intégration n'exécute ni push, ni déploiement, ni PR.
La vitrine distante devra être observée après cette éventuelle publication.
