# Lyra (reborn)

Une couche de contrôle cognitive au-dessus d'un LLM local (Ollama). **Consolidation
honnête** de ~23 prototypes audités (voir `docs/PLAN_EDIFICATION.md`) : on prend les
découvertes réelles, éparpillées sur deux ans, et on en fait un seul tout branché,
testé, et qui fait ce que la doc dit.

> Le LLM *utilise* Lyra ; il n'*est pas* Lyra.

## État réel (pas la vision — cf. charte §4)

Ce dépôt en est à : **fondations (P0) + noyau de contrôle (P1) + mémoire (P3)**.
Ce qui existe et est **testé** :

- `core/knobs.py` — les 4 boutons ρ/δr/τc/κ et leur mapping vers les options de
  génération. **Source unique de vérité.**
- `core/llm.py` — client Ollama avec le **correctif `options{}`** (les paramètres
  de génération sont imbriqués, pas étalés à la racine ; c'était le bug silencieux
  du canon d'origine) + un `EchoClient` déterministe hors-ligne pour les tests.
- `core/loop.py` — la boucle réelle (`LyraLoop`) : boutons → options → génération →
  métriques cheap réelles → politique réactive → garde-fous → EWMA ; et un
  **autopilote P+I** (`run_autopilot`) pour la loi de commande.
- `core/control/` — contrôleur **P+I à intégrateur fuyant** (version fonctionnelle
  portée de `lyra_framework_bundle`), garde-fous (clamp + hystérésis + réfractaire),
  politique réactive, politique de **phase λ**.
- `core/metrics/cheap.py` — métriques sans modèle (répétition, structure, overlap,
  troncature, carry-over).
- `memory/graph/` — le **nemeton** : graphe sémantique typé avec **deltas
  auditables + rollback**, bornes anti-explosion bruyantes, compaction, primitif
  local de nouveauté k=2 (pour le futur Songe), injecteur de prompt borné.
- `memory/ecology/` — l'**écologie mémorielle** : pouponnière / journal d'oubli /
  compost, réévaluation différée, **réveil des items compostés** (l'oubli est un
  différé, pas une suppression).
- `memory/cbr/` — **Memento** : rappel par cas (cosinus) + navigateur à 4
  stratégies (stabilize / explore / case_guided / balanced).

Le reste (`explore/esmm/`, `agency/`, `app/`, `eval/`, `core/topology/`,
`research/`) est **stub** : dossiers-ancres avec la référence de leur phase et de
leur source. Voir `BUILD_STATUS.md`.

## Démarrer

```bash
python -m pytest -q            # la suite de tests (aucune dépendance)
python scripts/demo.py         # démo hors-ligne, déterministe
LYRA_LIVE=1 python scripts/demo.py   # avec un Ollama réel (pip install requests)
```

## Repères

- `manifeste/CHARTE.md` — les 6 règles anti-pathologies (à respecter).
- `manifeste/VOCABULAIRE.md` — sens canonique de ρ/δr/τc/κ, Φ, phase λ, nemeton…
- `docs/PLAN_EDIFICATION.md` — le plan directeur des 8 phases (P0→P7).
- `BUILD_STATUS.md` — ce qui est fait, ce qui est stub, et le pont vers les audits.
