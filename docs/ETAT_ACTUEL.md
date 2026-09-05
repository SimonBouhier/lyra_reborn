# Lyra — état actuel et limites

**Relecture : 5 septembre 2026. Base du code : `d7353d4`.**
Ce document décrit l'application disponible. Les campagnes conservent leurs
propres documents de statut et leurs préinscriptions.

## Application P6

La page locale et son serveur FastAPI relient le contrôle P0–P2 à la mémoire
P3. Chaque session possède son moteur, son graphe, son écologie et ses cas.
L'état est sauvegardé en SQLite, restauré après redémarrage et remis à l'état
précédent si la génération ou la sauvegarde échoue.

Le moteur ESMM P4 existe séparément dans `explore/esmm/`. Le tour exposé par
`app/session.py` ne l'appelle pas : il récolte des concepts du prompt et des
liens de cooccurrence, sans délibération multi-modèles.

### Limites observées

- Le modèle reçoit le message courant et un résumé de concepts du graphe.
  Les réponses antérieures, pourtant conservées, ne sont pas réinjectées.
- La page reprend les indicateurs, sans réafficher les échanges antérieurs.
- L'historique interne est borné aux 50 derniers tours. Il ne constitue pas
  une archive intégrale des réponses, préférences et corrections.
- Le registre HTTP des sessions existe ; une navigation complète dans les
  anciennes conversations reste à construire.
- Le graphe REST, le catalogue/sélecteur de modèles et l'authentification
  minimale restent des travaux d'application.
- Le service reste local, lié à `127.0.0.1`. La base contient les textes en clair.

La prochaine tranche fonctionnelle n'est pas implémentée par ce réalignement
documentaire. Le parcours « converser, reprendre, corriger, retrouver » est
une recommandation issue de la revue, pas un nouveau protocole expérimental.

## Évaluation et recherches

- **P7 : atelier métrologique**, selon la décision du 31 août.
- V11 a franchi Q0 et exécuté sa calibration, puis s'est arrêtée à Q1.
  **H11 reste `UNTESTED`**. L'avantage adaptatif contre statique n'est pas établi.
- Aucun nouveau gel V12 avant examen conjoint du budget, du contrat, de la
  référence humaine et de la règle de jugement sur données de développement.
- Les 60 cas tenus restent réservés. La revue documentaire ne les a pas ouverts.
- Jachère, Songe et agentivité générale demeurent des travaux à construire ou
  qualifier ; aucune promesse de disponibilité prochaine n'est faite.

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
- Simon a fourni la référence Opal Gardener, essayée d'abord sur les sites EPP.
  La page Vercel propre à Lyra reste un chantier distinct.
  Elle n'est pas créée par cette mise à jour.

## Vérification datée

Le **5 septembre 2026 : 127 tests hors ligne réussis**, avec un test live
explicitement exclu. La sélection portait sur les fichiers `test_*.py` sauf
`test_p7_*` et `test_vigie_campaign*`. Elle couvre notamment contrôle, mémoire,
HTTP et persistance. Elle ne remplace pas une nouvelle suite complète ni une
qualification live. Le résultat complet antérieur du 2 septembre était
284 réussis et 2 ignorés, selon le journal de passation.

Reproduire la sélection sous PowerShell, depuis le dépôt :

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
