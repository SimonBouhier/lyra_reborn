# P7 V10 — plan de construction du runner

**Date :** 2026-08-29
**Contrainte maîtresse :** `PREREGISTRATION_v10.md` (gel `bc8497f`) +
`docs/P7_V10_PRERUN_AMENDMENT.md`. Toute divergence runner/prérég invalide le
run. Rien ne tourne avant que la chaîne complète (Q0 → calibration → tenu →
scoreur) soit implémentée, testée hors-ligne et smoke-testée sans Ollama.

## Ce qui existe déjà (réutiliser, ne pas réécrire)

| Brique | Fichier | Rôle |
|---|---|---|
| Paire de politiques (T1 commun, ABBA/BAAB, 5 appels) | `eval/p7_trajectory.py` | unité du tenu |
| Contrat producteur + segmentation S001… | `eval/p7_contracts.py` | décisions éditoriales |
| Evidence pack + inversion + hash canonique | `eval/p7_evidence.py` | `build_evidence_pack`, `invert_evidence_pack` |
| Contrat réduit (autorité) + prompt + validation | `eval/p7_v10_q1.py` | `CompactJudgeVerdict`, `compact_judge_prompt`, `validate_compact_judgment`, `verify_judge_fully_loaded_on_gpu` |
| Transport Ollama `JSON_ONLY_PROMPTED` | `eval/p7_judge_backend.py` | `OllamaJudgeBackend` + `JudgeBackendRequest(max_tokens=512, context_tokens=32768)` — sémantique exacte du runner Q-1 (`scripts/p7_v10_q1.py:272`) |
| Fixtures Q0 + orientations + mapping | `eval/p7_v7_q0.py` | incorporées V8, inchangées |
| Presets statiques | `core/control/reactive.py` | `creative`, `focused`, `strict` (+ vérifier `default`) |
| Corpus source scellé | `corpora/vigie_shadow_v1/candidate_pool.jsonl` | SHA gelé `074e0cec…f6f0` (V8 §Calibration) |
| Patron runner/verrous/GPU/journal | `scripts/p7_gemma3_admission.py`, `scripts/p7_v9.py` | à imiter |

## Couches (une couche = un commit + ses tests, dans cet ordre)

1. **`eval/p7_v10.py` — noyau pur** *(FAIT dans ce commit)* : constantes
   gelées (juge, digests, plafonds 18/432/432/900/360 = 2 142), requête juge
   octet-identique à Q-1, matrice Q0 (3×2×3), évaluation Q0, règle de
   résolution juge unique (stable après inversion ET non-TIE), garde de
   complétude des phases.
2. **`eval/p7_v10_corpus.py`** : lecture du pool + vérification du SHA gelé,
   exclusions (IDs V1/V2/calibration, doublons, filtres PII V2 — les
   retrouver dans le code vigie V2), fenêtre 400–3 000 caractères, sélection
   déterministe `sha256(seed || "heldout" || source || external_id)` de
   60 cas (20 GitHub / 20 HN / 20 arXiv), calibration 12 bénins V2
   (`sha256(seed || "calibration" || item_id)`, quatre par source),
   scellement : comptes + hashes, **aucun contenu affiché ni journalisé**.
   Seed globale 20260817 (V8).
3. **`eval/p7_v10_calibration.py`** : par cas × producteur, 4 trajectoires
   preset indépendantes (3 tours, 12 appels producteur par cas-producteur) ;
   packs des 6 paires de presets ; jugement juge unique dans les deux ordres
   (72 comparaisons/producteur avant inversion) ; sélection STATIC_BEST
   (score primaire victoires résolues, départages V8, départage lexical
   journalisé = échec Q1 s'il est nécessaire) ; recalcul sous 3 retraits de
   source ; porte Q1 = même gagnant dans ≥ 2 retraits.
4. **`eval/p7_v10_heldout.py`** : 60 cas × 3 producteurs ×
   `run_policy_pair` (STATIC_BEST issu de la calibration), affectation
   déterministe 30 ABBA / 30 BAAB par producteur, packs, jugement juge
   unique deux ordres, aucun parallélisme producteur.
5. **`eval/p7_v10_scoring.py`** : O1–O24, C0–C12 transposées (résolu =
   stable après inversion + non-TIE), Wilson 95 %, ratios de médianes,
   p95 nearest-rank, verdicts H10 par producteur + global — **chaque énoncé
   porte la mention de l'amendement** (« juge unique — indépendance
   inter-famille non disponible » + « avantage selon cet instrument gelé »).
6. **`scripts/p7_v10.py` — commande unique** *(coquille FAITE : Q0 + garde)* :
   `run` = Q0 → calibration → tenu → scoreur ; un verrou exclusif par phase,
   créé après la preuve GPU de la phase ; interruption après verrou = phase
   invalide. Compléter les phases 2–5 puis retirer leurs stubs ; la garde de
   complétude interdit tout run tant qu'un stub subsiste.
7. **Smoke de cycle de vie** (patron `scripts/p7_v8.py::run_lifecycle_smoke`) :
   sans Ollama, sans corpus, sans fixture Q0 — obligatoire avant run vivant.

## Pièges connus

- Le banc A a montré que le budget se consomme **au verrou** : chaque phase
  vérifie tout ce qui est vérifiable AVANT de créer le sien.
- `keep_alive` : le juge doit rester résident pendant sa phase (Q-1 utilisait
  `keep_alive: "30m"` au préflight) ; producteurs et juge ne résident jamais
  ensemble au-delà de la VRAM — blocs séquentiels comme V8.
- Préset `default` : vérifier sa définition exacte dans
  `core/control/reactive.py` avant la couche 3.
- Les 4 fichiers `eval/p7_v10_q1.py`, `p7_v7_q0.py`, `p7_evidence.py`,
  `p7_trajectory.py` sont gelés : **ne jamais les modifier** — envelopper.
- `num_predict=512` (contrat réduit), pas 2048 : les 2 048 du banc A
  concernaient le contrat complet.
