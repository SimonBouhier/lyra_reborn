# Lyra Reborn

## Project context

Lyra is a Python project for a cognitive control layer over a local LLM, primarily Ollama. Keep experimental and evaluation claims traceable to the relevant run, fixture, manifest, and status document.

## Working rules

- Read the nearest relevant test and implementation before changing behavior.
- Keep changes small and preserve append-only evidence, deterministic fixtures, seeds, hashes, and preregistration documents.
- Do not alter historical run artifacts or preregistration files unless explicitly requested.
- Treat `INVALID`, `UNTESTED`, and aborted evaluation statuses as meaningful results; do not silently convert them into semantic failures or passes.
- Prefer the Python standard library for the core unless an existing optional extra is the right boundary.
- Do not invent Ollama responses or evaluation evidence. State clearly when a local model or service is unavailable.
- Do not treat a visible effect (a model chatting, a page lighting up) as fulfillment of a plan layer. First layers of P6 prove the control+memory path; a live voice is an explicit later step (`LYRA_LIVE=1` or the page's "Demander une voix"), never auto-enabled because Ollama happens to be running.
- Before modifying shared control, evaluation, or evidence code, add or update a focused test.

## Verification

Use the repository virtual environment on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```

For a focused change, run the narrowest relevant test first, for example:

```powershell
python -m pytest tests\test_<area>.py -q
```

The project declares `pytest` under the `dev` optional dependency. Ollama-backed checks may require a running local Ollama service and must be distinguished from deterministic tests.

## Useful orientation

- `core/`: control, state, affect, LLM and loop primitives
- `eval/`: evaluation contracts, evidence, judges and trajectories
- `tests/`: deterministic regression tests
- `docs/`: campaign status and experimental records
- `scripts/`: runnable campaign and smoke scripts
