# Lyra Local Atelier — Baseline **B03 + P1P2** — Starter Kit

> **But**: relancer l’atelier Lyra en local (Windows, Ollama + `gpt-oss:20b`) avec une boucle stable (cohérence/fit/pressure/tension), contrôleurs (anti‑windup), phase λ, PatternEngine (R2/R1/R0), journalisation complète et carte **Nemeton** (PCA 2D). Inclut un **router minimal** prêt pour A/B.

---

## TL;DR
1) Installe Python 3.10+ et [Ollama](https://ollama.com) (port 11434). Télécharge `gpt-oss:20b`.
2) `pip install -r requirements.txt`
3) Lance `run_lyra_B03_nemeton.bat` (ou `run_lyra_P1P2.bat`).
4) Ouvre `data/runs/<RUN_ID>/nemeton_map.png` + `nemeton_metrics.json`.
5) Si OK (critères §8), enchaîne 2–3 runs nommés proprement.

---

## Arborescence (proposée)
```
.
├─ README.md
├─ requirements.txt
├─ run_lyra_B03_nemeton.bat
├─ run_lyra_P1P2.bat
├─ data/
│  ├─ config.json
│  ├─ last_state.json
│  └─ runs/
│     └─ <RUN_ID>/
│        ├─ metrics_log.csv
│        ├─ loop3_log.jsonl
│        ├─ RUNINFO.json
│        ├─ state_*.json
│        ├─ nemeton_map.csv
│        ├─ nemeton_map.png
│        └─ nemeton_metrics.json
├─ prompts/
│  ├─ system_lyra.txt
│  └─ system_router.txt
└─ src/
   ├─ __init__.py (optionnel)
   ├─ run_loop3.py
   └─ lyra_router.py
└─ tools/
   └─ apply_p1p2_patch.py
```

---

## 0) Vue d’ensemble
```
[Utilisateur] ─▶ (1) Loop Lyra  (src/run_loop3.py)
              │     a) Mesures: coherence, fit, pressure, tension
              │     b) Contrôleurs: pressure↔δr, tension↔τc (+ anti-windup)
              │     c) Phase λ : gating parcimonieux + cooldown
              │     d) PatternEngine : heuristiques de régime (R2/R1/R0)
              │     e) LLM (Ollama, gpt-oss:20b) → propose JSON "next_action"
              │
              ├─ Logs par run: data/runs/<RUN_ID>/{metrics_log.csv, loop3_log.jsonl, RUNINFO.json, state_*.json}
              └─ (2) Nemeton : projection PCA 2D + métriques de trajectoire
```
**État Lyra (résumé)** : ρ (cohésion), δr (exploration), τc (cap de tension), + graphe interne.
**Boucle (30 pas par défaut)** : propose → contrôle → mesure → log → projette sur la carte.

---

## 1) Métriques maison (bornées [0,1])
- **coherence** : densité du graphe + moyenne absolue des poids (proxy stabilité structure).
- **fit** : positivité moyenne + faible variance (proxy alignement interne), pondéré par ρ et AmpInit.
- **pressure** : combinaison de δr et τc (charge ressentie).
- **tension** : pénalise (1−coh), (1−fit) et la pressure (charge globale).
> **Note**: formules exactes dans `src/run_loop3.py`, stables et normalisées.

---

## 2) Contrôle (baseline « B03 + P1P2 »)
### 2.1 Consignes et gains (extrait `data/config.json`)
```json
{
  "control": {
    "tension_setpoint": 0.55,
    "pressure_setpoint": 0.45,

    "kp_tension": 0.23,
    "kp_pressure": 0.07,

    "ki_pressure": 0.012,
    "pressure_i_leak": 0.03,
    "pressure_i_max": 0.12,
    "pressure_i_split_tau": 0.65,

    "tension_band": 0.05,
    "pressure_band": 0.06,

    "tau_c_limits": [0.22, 1.60],

    "pressure_tau_share_delta_r_gate": 0.82,
    "pressure_tau_share_gain": 0.12,

    "pressure_margin": 0.02,
    "delta_r_nudge_down": 0.02,
    "delta_r_nudge_high": 0.025,
    "delta_r_floor": 0.28,
    "delta_r_soft_cap": 0.90
  }
}
```

### 2.2 Phase λ (gating)
Variables d’environnement:
```
LYRA_LAMBDA_THRESHOLD=0.90
LYRA_LAMBDA_ATTENUATION=0.96
LYRA_LAMBDA_TAU_GAIN=1.04
LYRA_LAMBDA_TAU_BIAS=0.015
LYRA_LAMBDA_COOLDOWN=5
```
Principe: booster **rare et contrôlé** (jamais en rafale).

### 2.3 PatternEngine (R2/R1/R0)
- **R2 (sur‑régime)** : tension trop au‑dessus, pressure + marge, ou τc trop haut → **freiner**.
- **R1 (croisière)** : proche consignes, τc bas → **laisser travailler**.
- **R0 (productif)** : zone intermédiaire où **capitaliser** (modulation de ρ, légère exploration).

---

## 3) Carte Nemeton (PCA 2D, z‑score)
Générée automatiquement à la fin d’un run :
- `nemeton_map.csv` (step, x, y)
- `nemeton_map.png` (trajet + couleur=pressure)
- `nemeton_metrics.json`

**Métriques** :
- **directionality** (= déplacement net / longueur du chemin) → 1 rectiligne, 0 sinueux/stationnaire.
- **mean_turn** (angle moyen entre pas) → élevé = beaucoup de virages.

---

## 4) Journalisation & hygiène
- Par run uniquement : tous les fichiers sous `data/runs/<RUN_ID>/`.
- `metrics_log.csv` inclut **run_id** en première colonne.
- `RUNINFO.json` : snapshot de config + `LYRA_NOTES`.
- `last_state.json` mis à jour à la fin (point de reprise).
- Sanitisation du `RUN_ID` dans les `.bat` (pas d’espaces/virgules/points).

---

## 5) Baseline obtenue & patchs
- **B01** : partage τc activé (`share_gain=0.12`) + intégral `0.015` → pressure ~0.48, τc plancher `0.22`.
- **B02** : `ki_pressure=0.012` → pressure ~0.464, τc toujours `0.22`, mieux mais haut.
- **B03** : `pressure_margin=0.02` → pressure ~0.451 (pile setpoint), τc=0.25 (débloqué), δr~0.35.
- **Nemeton++** : carte enrichie (trajet, couleur, métriques).
- **P1P2** : `kp_pressure=0.07`, `pressure_i_leak=0.03`, `delta_r_nudge_high=0.025` + anti‑windup → limite dérives >0.47 et casse l’intégral mal orienté.

---

## 6) Router « utilisable tout de suite »
- `src/lyra_router.py` + `prompts/system_router.txt`.
- k=3 échantillons, score simple + steering (temp/top_p) selon l’état Lyra.
- A/B recommandé sur 10 prompts (utilité, clarté, hallucination).
- Objectif court terme : si le router gagne ≥7/10, on l’active par défaut.

---

## 7) Démarrer (Windows, Ollama)
### 7.1 Run baseline (B03 + Nemeton)
`run_lyra_B03_nemeton.bat`
```bat
@echo off
setlocal EnableDelayedExpansion
for /f %%i in ('powershell -NoProfile -Command "(Get-Date).ToString(\"yyyyMMdd_HHmmss\")"') do set TS=%%i
set LYRA_RUN_ID=pi_leaky_B03_!TS!
set LYRA_NOTES=share=0.12; ki=0.012; pm=0.02
python -m src.run_loop3 --nemeton
endlocal
```

### 7.2 Appliquer P1+P2 (stabilité pressure)
`run_lyra_P1P2.bat`
```bat
@echo off
python tools\apply_p1p2_patch.py
python -m src.run_loop3 --nemeton
```

---

## 8) Critères « ok on passe à la suite » (fenêtre 30 pas)
- `pressure_mean ∈ [0.44, 0.46]`
- `tension_mean ∈ [0.54, 0.58]`
- `τc_min ≥ 0.22` (pas collé au plancher)
- `max_R2_streak < 10`
- `lambda_count` faible (0 la plupart du temps)
- Sur la carte : **directionality ↑**, **mean_turn** modéré.

---

## 9) Cap (prochaines étapes)
- **Geler** la baseline (B03+P1P2) et produire 2–3 runs **nommés proprement**.
- **Router A/B** : mesurer le gain qualitatif « sans fine‑tune ».
- **Atlas Nemeton** : fusionner les cartes (PCA gelée) ⇒ poches R0/R1/R2 récurrentes.
- **Chat loop** : appliquer le contrôle à une conversation interactive (profilage par régime ⇒ paramètres d’échantillonnage).
- **Micro‑sweeps responsables** (un paramètre à la fois) :
  - si pressure > 0.47 : `pressure_margin=0.015` **ou** `share_gain=0.10`.
  - si trajectoire « frise » (mean_turn↑) : `pressure_band=0.07` **ou** `kp_tension=0.20`.

---

## 10) Check‑list relance (autre session)
- Ollama OK (port 11434) + modèle `gpt-oss:20b`.
- `data/config.json` conforme §2.1 (**P1P2 appliqué**).
- `data/last_state.json` présent (sinon, ré‑initialisé).
- Lancer `run_lyra_B03_nemeton.bat` **ou** `run_lyra_P1P2.bat`.
- Vérifier `RUNINFO.json` (notes & snapshot).
- Regarder `nemeton_map.png` + `nemeton_metrics.json` (directionality / mean_turn).
- **Archiver** `data/runs/<RUN_ID>/` (ne pas écraser).
- Pour usage prod : activer le **router (k=3)** et faire un mini A/B.

---

## 11) Fichiers — Contenu complet

### `requirements.txt`
```txt
numpy
pandas
scikit-learn
matplotlib
requests
```

### `data/config.json`
> Si absent, `src/run_loop3.py` génère ce contenu par défaut.
```json
{
  "control": {
    "tension_setpoint": 0.55,
    "pressure_setpoint": 0.45,
    "kp_tension": 0.23,
    "kp_pressure": 0.07,
    "ki_pressure": 0.012,
    "pressure_i_leak": 0.03,
    "pressure_i_max": 0.12,
    "pressure_i_split_tau": 0.65,
    "tension_band": 0.05,
    "pressure_band": 0.06,
    "tau_c_limits": [0.22, 1.60],
    "pressure_tau_share_delta_r_gate": 0.82,
    "pressure_tau_share_gain": 0.12,
    "pressure_margin": 0.02,
    "delta_r_nudge_down": 0.02,
    "delta_r_nudge_high": 0.025,
    "delta_r_floor": 0.28,
    "delta_r_soft_cap": 0.90
  },
  "loop": {
    "steps": 30,
    "seed": 1337
  },
  "llm": {
    "model": "gpt-oss:20b",
    "endpoint": "http://localhost:11434/api/generate",
    "temperature_base": 0.7,
    "top_p_base": 0.9
  }
}
```

### `data/last_state.json`
> Ré‑écrit en fin de run. Si absent, créé à la volée.
```json
{
  "rho": 0.70,
  "delta_r": 0.35,
  "tau_c": 0.25,
  "lambda_cooldown": 0,
  "random_seed": 1337
}
```

### `prompts/system_lyra.txt`
```txt
Tu es le moteur d’action Lyra. À chaque tour, propose une action JSON compacte nommée "next_action" pour faire progresser le travail en conservant une pression proche de 0.45 et une tension proche de 0.55.

Contrainte: réponds UNIQUEMENT par un JSON valide. Schéma conseillé:
{
  "action": "<verbe court>",
  "focus": "<zone de travail>",
  "delta_r_suggestion": <0..1>,
  "rho_adjust": -0.02..0.02,
  "notes": "<très bref (≤120c)>"
}
```

### `prompts/system_router.txt`
```txt
Tu es un routeur/éditeur Lyra. Tu produis des sorties utiles, claires, non‑hallucinées. Priorise :
1) structure logique (listes courtes, étapes numérotées),
2) citations justifiées quand nécessaire,
3) concision avant exhaustivité, mais pas au détriment de la clarté.
```

### `tools/apply_p1p2_patch.py`
```python
import json, pathlib
CONFIG = pathlib.Path('data/config.json')
CONFIG.parent.mkdir(parents=True, exist_ok=True)
if CONFIG.exists():
    cfg = json.loads(CONFIG.read_text(encoding='utf-8'))
else:
    cfg = {"control":{}}
ctrl = cfg.setdefault("control", {})
ctrl.update({
    "kp_pressure": 0.07,
    "pressure_i_leak": 0.03,
    "delta_r_nudge_high": 0.025
})
CONFIG.write_text(json.dumps(cfg, indent=2), encoding='utf-8')
print("P1P2 patch applied → data/config.json updated.")
```

### `src/run_loop3.py`
```python
from __future__ import annotations
import os, json, time, math, random, argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, List

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

try:
    import requests
except Exception:
    requests = None

# ---------------------- Utils ----------------------
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
RUNS = DATA / 'runs'
PROMPTS = ROOT / 'prompts'

DEFAULT_CONFIG = {
    "control": {
        "tension_setpoint": 0.55,
        "pressure_setpoint": 0.45,
        "kp_tension": 0.23,
        "kp_pressure": 0.07,
        "ki_pressure": 0.012,
        "pressure_i_leak": 0.03,
        "pressure_i_max": 0.12,
        "pressure_i_split_tau": 0.65,
        "tension_band": 0.05,
        "pressure_band": 0.06,
        "tau_c_limits": [0.22, 1.60],
        "pressure_tau_share_delta_r_gate": 0.82,
        "pressure_tau_share_gain": 0.12,
        "pressure_margin": 0.02,
        "delta_r_nudge_down": 0.02,
        "delta_r_nudge_high": 0.025,
        "delta_r_floor": 0.28,
        "delta_r_soft_cap": 0.90
    },
    "loop": {"steps": 30, "seed": 1337},
    "llm": {
        "model": "gpt-oss:20b",
        "endpoint": "http://localhost:11434/api/generate",
        "temperature_base": 0.7,
        "top_p_base": 0.9
    }
}

LAMBDA = {
    "THRESH": float(os.getenv('LYRA_LAMBDA_THRESHOLD', 0.90)),
    "ATT": float(os.getenv('LYRA_LAMBDA_ATTENUATION', 0.96)),
    "TAU_GAIN": float(os.getenv('LYRA_LAMBDA_TAU_GAIN', 1.04)),
    "TAU_BIAS": float(os.getenv('LYRA_LAMBDA_TAU_BIAS', 0.015)),
    "COOLDOWN": int(os.getenv('LYRA_LAMBDA_COOLDOWN', 5)),
}

# ---------------------- State ----------------------
@dataclass
class LyraState:
    rho: float = 0.70
    delta_r: float = 0.35
    tau_c: float = 0.25
    lambda_cooldown: int = 0
    random_seed: int = 1337

    # simple internal graph (weights in [-1,1])
    def init_graph(self, n: int = 12):
        rng = np.random.default_rng(self.random_seed)
        W = rng.normal(0, 0.3, size=(n, n))
        np.fill_diagonal(W, 0.0)
        self.W = np.clip(W, -1.0, 1.0)

    def step_graph(self, k: float):
        # small relaxation toward coherence influenced by rho and delta_r
        W = self.W
        W += 0.02 * self.rho * np.sign(W) - 0.015 * self.delta_r * W
        noise = (np.random.randn(*W.shape)) * (0.01 + 0.01 * (1 - self.rho))
        self.W = np.clip(W + noise, -1.0, 1.0)


# ---------------------- IO helpers ----------------------

def load_or_init_config() -> Dict[str, Any]:
    DATA.mkdir(parents=True, exist_ok=True)
    cfg_path = DATA / 'config.json'
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
    else:
        cfg = DEFAULT_CONFIG
        cfg_path.write_text(json.dumps(cfg, indent=2), encoding='utf-8')
    return cfg


def load_or_init_state(seed: int) -> LyraState:
    st_path = DATA / 'last_state.json'
    if st_path.exists():
        d = json.loads(st_path.read_text(encoding='utf-8'))
        st = LyraState(**{**LyraState().__dict__, **d})
    else:
        st = LyraState(random_seed=seed)
        st.init_graph()
        st_path.write_text(json.dumps(asdict(st), indent=2), encoding='utf-8')
    if not hasattr(st, 'W'):
        st.init_graph()
    return st


def save_state(st: LyraState):
    (DATA / 'last_state.json').write_text(json.dumps({k:v for k,v in asdict(st).items() if k != 'W'}, indent=2), encoding='utf-8')


# ---------------------- Metrics ----------------------

def graph_density(W: np.ndarray, thr: float = 0.1) -> float:
    n = W.shape[0]
    m = (np.abs(W) > thr).sum() - (np.abs(np.diag(W)) > thr).sum()
    max_m = n * (n - 1)
    return float(m) / max_m if max_m else 0.0


def coherence(W: np.ndarray) -> float:
    dens = graph_density(W)
    mean_abs = float(np.mean(np.abs(W)))
    return float(np.clip(0.5 * dens + 0.5 * mean_abs, 0.0, 1.0))


def fit_metric(W: np.ndarray, rho: float, amp_init: float = 1.0) -> float:
    pos_mean = float(np.mean(np.clip(W, 0, 1)))
    var = float(np.var(W))  # ~[0,1]
    var_pen = float(np.clip(1.0 - var, 0.0, 1.0))
    base = 0.6 * pos_mean + 0.4 * var_pen
    return float(np.clip(base * (0.5 + 0.5 * rho) * amp_init, 0.0, 1.0))


def pressure_metric(delta_r: float, tau_c: float) -> float:
    tau_scaled = np.clip((tau_c - 0.22) / (1.60 - 0.22), 0.0, 1.0)
    return float(np.clip(0.5 * delta_r + 0.5 * tau_scaled, 0.0, 1.0))


def tension_metric(coh: float, fit: float, pressure: float) -> float:
    inv = (1 - coh) + (1 - fit) + pressure
    return float(np.clip(inv / 3.0, 0.0, 1.0))


# ---------------------- LLM ----------------------

def ollama_generate(model: str, prompt: str, temperature: float, top_p: float) -> str:
    endpoint = DEFAULT_CONFIG['llm']['endpoint']
    if requests is None:
        return '{"action":"noop","focus":"offline","delta_r_suggestion":0.35,"rho_adjust":0.0,"notes":"requests not installed"}'
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "options": {"temperature": temperature, "top_p": top_p},
            "stream": False
        }
        r = requests.post(endpoint, json=payload, timeout=60)
        r.raise_for_status()
        out = r.json().get('response', '').strip()
        return out
    except Exception as e:
        return '{"action":"noop","focus":"error","delta_r_suggestion":0.35,"rho_adjust":0.0,"notes":"'+str(e)+'"}'


def build_prompt(system_path: Path, context: Dict[str, Any]) -> str:
    sys = (system_path.read_text(encoding='utf-8') if system_path.exists() else '')
    header = (
        f"[STATE] rho={context['rho']:.3f} delta_r={context['delta_r']:.3f} "
        f"tau_c={context['tau_c']:.3f} pressure={context['pressure']:.3f} "
        f"tension={context['tension']:.3f}\n"
    )
    return sys + "\n\n" + header + "Réponds par un JSON 'next_action'."


# ---------------------- Control ----------------------

def apply_control(cfg: Dict[str, Any], st: LyraState, meas: Dict[str, float], integrator: Dict[str, float]) -> Dict[str, Any]:
    c = cfg['control']
    # errors
    e_p = c['pressure_setpoint'] - meas['pressure']
    e_t = c['tension_setpoint'] - meas['tension']

    # Pressure PI with leak & anti-windup split between delta_r and tau_c
    I = integrator.get('p', 0.0)
    I = I + c['ki_pressure'] * e_p - c['pressure_i_leak'] * I
    I = float(np.clip(I, -c['pressure_i_max'], c['pressure_i_max']))
    integrator['p'] = I

    # proportional parts
    p_p = c['kp_pressure'] * e_p
    p_t = c['kp_tension'] * e_t if abs(e_t) > c['tension_band'] else 0.0

    # share to tau if delta_r above gate
    share = c['pressure_tau_share_gain'] if st.delta_r > c['pressure_tau_share_delta_r_gate'] else 0.0

    # nudge logic around margins
    if meas['pressure'] > c['pressure_setpoint'] + c['pressure_margin']:
        st.delta_r -= c['delta_r_nudge_high']
    elif abs(e_p) < c['pressure_band']:
        st.delta_r -= c['delta_r_nudge_down'] * math.copysign(1, st.delta_r - c['pressure_setpoint'])

    # apply PI split
    d_delta_r = (1 - c['pressure_i_split_tau']) * (p_p + I)
    d_tau = c['pressure_i_split_tau'] * (p_p + I) + share * (p_p + I)

    # apply tension P on tau_c
    st.tau_c += d_tau + p_t
    st.delta_r += d_delta_r

    # clamp
    st.tau_c = float(np.clip(st.tau_c, c['tau_c_limits'][0], c['tau_c_limits'][1]))
    st.delta_r = float(np.clip(st.delta_r, c['delta_r_floor'], c['delta_r_soft_cap']))

    return {"e_p": e_p, "e_t": e_t, "I_p": I, "p_p": p_p, "p_t": p_t}


# ---------------------- Phase lambda ----------------------

def maybe_lambda(st: LyraState, coh: float, fit: float) -> bool:
    triggered = False
    if st.lambda_cooldown > 0:
        st.lambda_cooldown -= 1
        return False
    signal = max(coh, fit)
    if signal >= LAMBDA['THRESH']:
        st.delta_r *= LAMBDA['ATT']
        st.tau_c = st.tau_c * LAMBDA['TAU_GAIN'] + LAMBDA['TAU_BIAS']
        st.lambda_cooldown = LAMBDA['COOLDOWN']
        return True
    return triggered

# ---------------------- Regime ----------------------

def regime_label(cfg: Dict[str, Any], tension: float, pressure: float, tau_c: float) -> str:
    c = cfg['control']
    if (tension > c['tension_setpoint'] + c['tension_band']) or (pressure > c['pressure_setpoint'] + c['pressure_margin']) or (tau_c > 1.40):
        return 'R2'
    if (abs(tension - c['tension_setpoint']) <= c['tension_band']) and (abs(pressure - c['pressure_setpoint']) <= c['pressure_band']) and (tau_c < 0.40):
        return 'R1'
    return 'R0'


# ---------------------- Nemeton ----------------------

def build_nemeton(run_dir: Path, traj_feats: List[List[float]], pressures: List[float]):
    X = np.asarray(traj_feats, dtype=float)
    # z-score
    X = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-9)
    pca = PCA(n_components=2, random_state=0)
    XY = pca.fit_transform(X)
    # metrics
    diffs = np.diff(XY, axis=0)
    seglen = np.linalg.norm(diffs, axis=1)
    path_len = float(seglen.sum()) if len(seglen) else 0.0
    disp = float(np.linalg.norm(XY[-1] - XY[0])) if len(XY) > 1 else 0.0
    directionality = float(disp / (path_len + 1e-9))
    # mean turn
    angles = []
    for i in range(len(diffs) - 1):
        a, b = diffs[i], diffs[i+1]
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na > 1e-9 and nb > 1e-9:
            cosang = np.clip(np.dot(a, b) / (na * nb), -1.0, 1.0)
            angles.append(math.acos(cosang))
    mean_turn = float(np.mean(angles)) if angles else 0.0

    # save csv
    df = pd.DataFrame({
        'step': np.arange(len(XY)),
        'x': XY[:,0],
        'y': XY[:,1],
        'pressure': pressures[:len(XY)]
    })
    df.to_csv(run_dir / 'nemeton_map.csv', index=False)

    # plot
    plt.figure(figsize=(6,5), dpi=140)
    sc = plt.scatter(df['x'], df['y'], c=df['pressure'], cmap='viridis')
    plt.plot(df['x'], df['y'], linewidth=1, alpha=0.5)
    plt.colorbar(sc, label='pressure')
    plt.title('Nemeton PCA map (pressure color)')
    plt.tight_layout()
    plt.savefig(run_dir / 'nemeton_map.png')
    plt.close()

    # metrics json
    meta = {
        'directionality': directionality,
        'mean_turn': mean_turn,
        'steps': len(XY)
    }
    (run_dir / 'nemeton_metrics.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')


# ---------------------- Main loop ----------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--nemeton', action='store_true', help='Generate Nemeton map at end')
    args = ap.parse_args()

    cfg = load_or_init_config()
    random.seed(cfg['loop']['seed'])
    np.random.seed(cfg['loop']['seed'])

    st = load_or_init_state(cfg['loop']['seed'])

    # run id & dir
    run_id = os.getenv('LYRA_RUN_ID')
    if not run_id:
        ts = time.strftime('%Y%m%d_%H%M%S')
        run_id = f"lyra_{ts}"
    run_id = ''.join(ch for ch in run_id if ch.isalnum() or ch in ('-', '_'))
    run_dir = RUNS / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # logs
    metrics_csv = run_dir / 'metrics_log.csv'
    jsonl = run_dir / 'loop3_log.jsonl'

    # RUNINFO
    notes = os.getenv('LYRA_NOTES', '')
    info = {
        'run_id': run_id,
        'notes': notes,
        'config_snapshot': cfg,
        'ts_start': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    (run_dir / 'RUNINFO.json').write_text(json.dumps(info, indent=2), encoding='utf-8')

    # metrics header
    with metrics_csv.open('w', encoding='utf-8', newline='') as f:
        f.write('run_id,step,coherence,fit,pressure,tension,delta_r,tau_c,rho,regime,lambda_tick\n')

    integrator = {'p': 0.0}
    lambda_count = 0

    traj_feats = []
    traj_pressures = []

    # loop
    for step in range(cfg['loop']['steps']):
        st.step_graph(k=0.02)
        coh = coherence(st.W)
        fit = fit_metric(st.W, st.rho, amp_init=1.0)
        pres = pressure_metric(st.delta_r, st.tau_c)
        tens = tension_metric(coh, fit, pres)

        # Phase lambda
        lam = maybe_lambda(st, coh, fit)
        if lam: lambda_count += 1

        # Regime
        reg = regime_label(cfg, tens, pres, st.tau_c)

        # LLM proposal (optional)
        ctx = {'rho': st.rho, 'delta_r': st.delta_r, 'tau_c': st.tau_c, 'pressure': pres, 'tension': tens, 'regime': reg}
        prompt = build_prompt(PROMPTS / 'system_lyra.txt', ctx)

        # steering from regime
        t_base = cfg['llm']['temperature_base']
        p_base = cfg['llm']['top_p_base']
        if reg == 'R2':
            t_use, p_use = max(0.2, t_base - 0.3), max(0.7, p_base - 0.1)
        elif reg == 'R1':
            t_use, p_use = t_base, p_base
        else: # R0
            t_use, p_use = min(1.0, t_base + 0.1), min(1.0, p_base + 0.05)

        out = ollama_generate(cfg['llm']['model'], prompt, t_use, p_use)
        try:
            ja = json.loads(out)
        except Exception:
            ja = {"action":"noop","delta_r_suggestion": st.delta_r, "rho_adjust": 0.0, "notes":"parse_error"}

        # apply small rho adjust from model
        st.rho = float(np.clip(st.rho + float(ja.get('rho_adjust', 0.0)), 0.0, 1.0))

        # control
        ctl = apply_control(cfg, st, {'pressure': pres, 'tension': tens}, integrator)

        # track features for nemeton
        traj_feats.append([coh, fit, pres, tens, st.delta_r, st.tau_c, st.rho])
        traj_pressures.append(pres)

        # logs
        with jsonl.open('a', encoding='utf-8') as f:
            rec = {
                'step': step,
                'meas': {'coherence':coh,'fit':fit,'pressure':pres,'tension':tens},
                'state': {'rho':st.rho,'delta_r':st.delta_r,'tau_c':st.tau_c},
                'regime': reg,
                'lambda_tick': lam,
                'llm': ja,
                'control': ctl,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')

        with metrics_csv.open('a', encoding='utf-8', newline='') as f:
            f.write(f"{run_id},{step},{coh:.6f},{fit:.6f},{pres:.6f},{tens:.6f},{st.delta_r:.6f},{st.tau_c:.6f},{st.rho:.6f},{reg},{int(lam)}\n")

        # save sparse state
        if step % 10 == 0:
            (run_dir / f'state_{step:03d}.json').write_text(json.dumps({'rho':st.rho,'delta_r':st.delta_r,'tau_c':st.tau_c,'lambda_cooldown':st.lambda_cooldown}, indent=2), encoding='utf-8')

    # nemeton
    if args.nemeton:
        build_nemeton(run_dir, traj_feats, traj_pressures)

    # last state
    save_state(st)

    # finalize
    summary = {
        'pressure_mean': float(np.mean([r[2] for r in traj_feats])),
        'tension_mean': float(np.mean([r[3] for r in traj_feats])),
        'tau_c_min': float(np.min([r[5] for r in traj_feats])),
        'lambda_count': lambda_count
    }
    (run_dir / 'SUMMARY.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print("Run complete:", run_id)

if __name__ == '__main__':
    main()
```

### `src/lyra_router.py`
```python
import os, json, random
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
PROMPTS = ROOT / 'prompts'

CFG = json.loads((DATA / 'config.json').read_text(encoding='utf-8'))
MODEL = CFG['llm']['model']
ENDPT = CFG['llm']['endpoint']

try:
    STATE = json.loads((DATA / 'last_state.json').read_text(encoding='utf-8'))
except Exception:
    STATE = {"rho":0.7, "delta_r":0.35, "tau_c":0.25}

SYS = (PROMPTS / 'system_router.txt').read_text(encoding='utf-8') if (PROMPTS / 'system_router.txt').exists() else ''


def call_llm(prompt: str, temperature: float, top_p: float, seed: int):
    payload = {
        "model": MODEL,
        "prompt": SYS + "\n\n" + prompt,
        "options": {"temperature": temperature, "top_p": top_p, "seed": seed},
        "stream": False
    }
    r = requests.post(ENDPT, json=payload, timeout=120)
    r.raise_for_status()
    return r.json().get('response', '')


def pick_best(cands):
    # score = lexical diversity × structure bonus × length prior
    def score(txt: str):
        toks = [t for t in txt.split() if t.isalpha() or t.isdigit()]
        uniq = len(set(toks)) / (len(toks)+1e-6)
        struct = 1.15 if any(s in txt for s in ['\n- ', '\n1.', '\n2.']) else 1.0
        length = len(toks)
        length_prior = 1.0 - abs(length - 220) / 400.0  # favor ~200-250w
        return uniq * struct * max(0.2, length_prior)
    best = max(cands, key=lambda x: score(x))
    return best


def route(prompt: str, k: int = 3):
    # steering from state
    delta_r, tau_c = STATE.get('delta_r', 0.35), STATE.get('tau_c', 0.25)
    base_t, base_p = CFG['llm']['temperature_base'], CFG['llm']['top_p_base']

    if tau_c < 0.35 and 0.40 < delta_r < 0.70:
        temps = [base_t, min(1.0, base_t+0.1), min(1.0, base_t+0.2)]
        tops = [base_p, base_p, min(1.0, base_p+0.05)]
    elif tau_c > 0.9:
        temps = [max(0.2, base_t-0.3)]*k
        tops = [max(0.7, base_p-0.1)]*k
    else:
        temps = [base_t]*k
        tops = [base_p]*k

    seeds = [random.randint(1, 10_000_000) for _ in range(k)]
    cands = [call_llm(prompt, temps[i%k], tops[i%k], seeds[i%k]) for i in range(k)]
    return pick_best(cands)

if __name__ == '__main__':
    import sys
    q = sys.stdin.read() if not sys.argv[1:] else ' '.join(sys.argv[1:])
    print(route(q))
```

---

## 12) FAQ express
**Pourquoi ne pas « laisser dériver » si la cohérence monte ?**
> On vise une **zone de confort reproductible**. La cohérence peut monter par chance locale ; la pressure hors consigne finit par saturer (dérive). Le contrôle + anti‑windup capitalisent **sans perdre la main**.

**Pourquoi 30 pas ?**
> Suffisant pour voir le régime, court pour boucler vite. On pourra rallonger une fois stable.

**Et le GPU ?**
> Le framework tourne **CPU‑safe** ; l’usage GPU (RTX) dépend d’Ollama/cuBLAS/cuDNN. La baseline n’exige pas le GPU.

---

## Notes pratiques
- Si `requests` manque: `pip install requests`.
- Si `scikit-learn` n’est pas souhaité: remplacer PCA par une SVD maison (facile à intégrer au besoin).
- Les `.bat` utilisent PowerShell pour un timestamp **sans espaces**.
- `LYRA_NOTES` est archivé tel quel dans `RUNINFO.json`.

---

## Changelog (session)
- Baseline consolidée **B03 + P1P2**.
- Carte **Nemeton** (PNG + CSV + métriques) ajoutée.
- Logger unifié + `run_id` en première colonne de `metrics_log.csv`.
- Router minimal (k=3) prêt pour A/B.

