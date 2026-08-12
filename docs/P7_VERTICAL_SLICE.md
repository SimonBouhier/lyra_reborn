# P7 — tranche verticale V3

**Statut :** harnais synthétique construit ; aucune campagne réelle exécutée.
**Préinscription :** `PREREGISTRATION_v3.md`, gelée au commit
`a5c3769baffbf19472188baef78a64bf4f8cb3a8` et estampillée au commit
`b54a47b`.

## Ce que cette tranche prouve

Le chemin minimal existe de bout en bout sans toucher au jeu tenu :

1. ADAPTIVE et STATIC_BEST commencent avec le même état, le même prompt, les
   mêmes options et la même graine ;
2. la sortie du premier tour est donc identique dans le client contrôlé ;
3. Lyra observe cette sortie et change les options effectives du tour 2, tandis
   que la baseline les garde fixes ;
4. le client synthétique produit alors des sorties différentes ;
5. le tour final doit satisfaire un contrat Pydantic fermé et citer exactement
   la source ;
6. le juge anonyme doit lire la source et les deux traces complètes avec des
   outils locaux bornés ;
7. chaque comparaison est rejouée ordre inversé ; instabilité, égalité ou
   désaccord donnent `UNRESOLVED`.

Cette preuve porte sur le câblage et les invariants. Elle ne montre aucune
amélioration de qualité et n'utilise aucun résultat LLM réel.

## Reproduire

Dans l'environnement Lyra où Pydantic 2.13.4 est installé :

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_p7_vertical_slice.py -q
```

Résultat attendu à l'état de ce document : `5 passed`.

Régressions directes du noyau :

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests\test_modulation.py tests\test_bridge.py tests\test_affect.py -q
```

Résultat attendu : `14 passed, 1 skipped` ; le skip est le test Ollama live
conditionné par `LYRA_LIVE`.

Smoke-test producteur live, toujours sur source synthétique et sans afficher les
sorties :

```powershell
.\.venv\Scripts\python.exe scripts\p7_smoke.py --model mistral:latest
```

Le script ne publie que le digest du modèle, les options, tailles et SHA-256 des
sorties, les invariants du tour 1 et le statut du contrat final. Codes non nuls :
2 si un contrat final échoue ; 3 si prompt/options du tour 1 diffèrent ; 4 si le
runtime produit deux sorties différentes malgré prompt/options/graine égaux.

Le smoke Mistral du 2026-08-12 a rendu le code 4. V3 est donc arrêtée avant
mesure ; voir `docs/P7_V3_STATUS.md`.

Le test complet contient encore une contrainte historique de la campagne V1 :
`tests/test_vigie_campaign.py::test_frozen_epp_sidecar_revision_is_verified`
échoue si le dépôt voisin EPP n'est pas positionné sur le sidecar gelé
`3a274cd`. Ce rouge externe n'est ni masqué ni corrigé par P7.

## Ce qui manque avant toute mesure tenue

- inscrire proprement Pydantic dans l'extra d'évaluation ;
- construire et tester la sélection calibration/heldout sans afficher les
  contenus ;
- exécuter un smoke-test live sur un cas synthétique, séparément pour chaque
  modèle producteur et juge ;
- figer les payloads, hashes, mappings aveugles et compteurs de ressources ;
- implémenter le scoreur déterministe C0–C8 ;
- seulement ensuite sceller les 60 cas et lancer les générations.
