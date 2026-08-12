# P7 — tranche verticale V3

**Statut :** harnais synthétique V5 à ancres source construit puis arrêté avant
calibration ; aucune campagne réelle exécutée.
**Dernière préinscription gelée :** `PREREGISTRATION_v5.md`, au commit
`f367930f91c61ec5829bd5fcc1e9507e46ba154e` et estampillée au commit
`d7c0bcb`. Statuts antérieurs : `docs/P7_V3_STATUS.md` et
`docs/P7_V4_STATUS.md`. Statut V5 : `docs/P7_V5_STATUS.md`.

## Ce que cette tranche prouve

Le chemin minimal existe de bout en bout sans toucher au jeu tenu :

1. COMMON T1 est généré une seule fois et copié byte-for-byte dans les deux
   traces ;
2. Lyra observe ce préfixe tandis que STATIC_BEST garde ses boutons ;
3. Lyra change les options effectives du tour 2, tandis
   que la baseline les garde fixes ;
4. le client synthétique produit alors des sorties différentes ;
5. les quatre appels de branche suivent ABBA ou BAAB, pour cinq appels physiques
   par cas ;
6. la source est segmentée déterministiquement en `S001…` et le tour final doit
   satisfaire un contrat Pydantic fermé en référant une ancre existante ;
7. le juge anonyme doit lire la source et les deux traces complètes avec des
   outils locaux bornés ;
8. chaque comparaison est rejouée ordre inversé ; instabilité, égalité ou
   désaccord donnent `UNRESOLVED`.

Cette preuve porte sur le câblage et les invariants. Elle ne montre aucune
amélioration de qualité et n'utilise aucun résultat LLM réel.

## Reproduire

Dans l'environnement Lyra où Pydantic 2.13.4 est installé :

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_p7_vertical_slice.py -q
```

Résultat attendu à l'état de ce document : `7 passed`.

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
.\.venv\Scripts\python.exe scripts\p7_smoke.py --model mistral:latest `
  --execution-order ABBA
```

Le script ne publie que le digest du modèle, l'ordre, le nombre d'appels, les
options, tailles et SHA-256 des sorties, les invariants du tour 1 et le statut
du contrat final. Codes non nuls : 2 si un contrat final échoue ; 3 si
prompt/options du préfixe copié diffèrent ; 4 si les deux traces ne contiennent
pas exactement la même sortie COMMON T1.

Le smoke Mistral V3 du 2026-08-12 avait rendu le code 4 parce que V3 générait le
tour 1 deux fois. V4 le génère une fois puis le partage ; voir
`docs/P7_V3_STATUS.md`.

Smoke live du panel sur la même source synthétique :

```powershell
.\.venv\Scripts\python.exe scripts\p7_judge_smoke.py `
  --producer mistral:latest --execution-order ABBA
```

Le script utilise les deux autres modèles comme juges, chacun dans les deux
ordres. Il ne publie que préférences anonymes, nombre d'étapes, stabilité et
résolution du panel. `UNRESOLVED` est un résultat valide ; une violation du
protocole d'outils reste une erreur explicite.

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
