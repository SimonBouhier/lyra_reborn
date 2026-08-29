"""Faux Ollama déterministe pour les vérifications hors-ligne du runner V10.

Ce n'est PAS un générateur crédible et ne prétend produire aucune évidence
d'évaluation : il rend des sorties fonction des options reçues, exactement
comme `core.llm.EchoClient`, pour prouver que le harnais transporte, attribue
et dé-aveugle correctement. Aucune de ses réponses n'entre dans un verdict.

Le « producteur » encode `num_predict` dans son texte (`np=<n>`) ; le « juge »
lit ce marqueur dans les deux candidats du pack et préfère le plus élevé. La
chaîne complète — knobs -> options -> payload -> pack -> jugement -> mapping
scellé -> preset gagnant — est donc observable de bout en bout sans Ollama.
"""
from __future__ import annotations

import json
import re
from typing import Any

import requests

from eval.p7_v10 import JUDGE
from eval.p7_v10_producer import PRODUCERS

NP_MARKER = re.compile(r"np=(\d+)")

_TURN1 = "Identifie le noyau du contenu"
_TURN2 = "Soumets l'analyse précédente"
_TURN3 = "Rends la décision éditoriale finale"

_RATIONALE = (
    "The source states a bounded factual claim; the available evidence supports "
    "an audit rather than amplification, because the decisive quantities are "
    "reported without an independent comparison. Marker np={np}."
)
_WHY = (
    "This passage carries the claim under review and bounds what can be "
    "concluded from it. Marker np={np}."
)
_UNCERTAINTY = (
    "The source supplies no independent replication and no effect size, so the "
    "magnitude of the reported effect stays unresolved."
)
_NEXT_STEP = (
    "Verify the reported quantity against an independent source before treating "
    "it as established."
)


def decision_payload(np: int) -> dict[str, Any]:
    """Décision conforme au contrat producteur gelé, sans espace parasite."""
    return {
        "decision": "AUDIT",
        "rationale": _RATIONALE.format(np=np),
        "evidence": [{"source_span_id": "S001", "why": _WHY.format(np=np)}],
        "uncertainty": _UNCERTAINTY,
        "next_step": _NEXT_STEP,
    }


class FakeResponse:
    def __init__(self, status_code: int, body: dict[str, Any]):
        self.status_code = status_code
        self._body = body
        self.content = json.dumps(body, ensure_ascii=False).encode("utf-8")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self) -> dict[str, Any]:
        return self._body


class FakeOllama:
    """Serveur Ollama simulé : catalogue, résidence GPU, génération."""

    def __init__(
        self,
        *,
        version: str = "0.32.15",
        producer_failures: tuple[str, ...] = (),
        judge_failures: tuple[int, ...] = (),
        judge_preference: str | None = None,
    ):
        self.version = version
        self.catalog = {spec.model: spec.digest for spec in PRODUCERS}
        self.catalog[JUDGE.model] = JUDGE.digest
        self.sizes = {name: 4_000_000_000 + index for index, name in enumerate(self.catalog)}
        self.loaded: dict[str, bool] = {}
        self.generate_calls: list[dict[str, Any]] = []
        self.residency_calls: list[dict[str, Any]] = []
        self.producer_failures = set(producer_failures)
        self.judge_failures = set(judge_failures)
        self.judge_preference = judge_preference
        self.judge_call_count = 0
        self.last_request: bytes = b""

    # --- catalogue et résidence -------------------------------------------
    def get(self, url: str, timeout: Any = None) -> FakeResponse:
        if url.endswith("/api/version"):
            return FakeResponse(200, {"version": self.version})
        if url.endswith("/api/tags"):
            return FakeResponse(
                200,
                {
                    "models": [
                        {"name": name, "digest": digest}
                        for name, digest in sorted(self.catalog.items())
                    ]
                },
            )
        if url.endswith("/api/ps"):
            return FakeResponse(
                200,
                {
                    "models": [
                        {
                            "name": name,
                            "digest": self.catalog[name],
                            "size": self.sizes[name],
                            "size_vram": self.sizes[name],
                            "context_length": 32768,
                        }
                        for name in sorted(self.loaded)
                        if self.loaded[name]
                    ]
                },
            )
        raise AssertionError(f"unexpected GET {url}")

    # --- génération --------------------------------------------------------
    def post(
        self,
        url: str,
        data: bytes | None = None,
        headers: Any = None,
        timeout: Any = None,
        **kwargs: Any,
    ) -> FakeResponse:
        if not url.endswith("/api/generate"):
            raise AssertionError(f"unexpected POST {url}")
        self.last_request = data
        payload = json.loads(data)
        model = payload["model"]
        prompt = payload.get("prompt", "")
        if prompt == "":
            keep_alive = payload.get("keep_alive")
            self.loaded[model] = keep_alive != 0
            self.residency_calls.append({"model": model, "keep_alive": keep_alive})
            return FakeResponse(200, {"response": "", "done_reason": "load"})
        if not self.loaded.get(model):
            raise AssertionError(f"{model} generated while not resident")
        if model == JUDGE.model:
            return self._judge(payload, prompt)
        return self._producer(payload, prompt, model)

    def _producer(self, payload: dict[str, Any], prompt: str, model: str) -> FakeResponse:
        options = payload.get("options", {})
        np = int(options.get("num_predict", 0))
        self.generate_calls.append({"model": model, "options": dict(options)})
        if model in self.producer_failures:
            return FakeResponse(500, {"error": "simulated producer outage"})
        if _TURN3 in prompt:
            text = json.dumps(decision_payload(np), ensure_ascii=False)
        elif _TURN2 in prompt:
            text = f"Objection to the previous analysis, grounded in SOURCE. np={np}"
        elif _TURN1 in prompt:
            text = f"Core of the content, its testable claims and unknowns. np={np}"
        else:
            raise AssertionError("unexpected producer prompt")
        return FakeResponse(
            200,
            {
                "response": text,
                "done_reason": "stop",
                "eval_count": max(1, np // 8),
                "prompt_eval_count": len(prompt) // 4,
                "total_duration": 1_000_000,
            },
        )

    def _judge(self, payload: dict[str, Any], prompt: str) -> FakeResponse:
        self.judge_call_count += 1
        if self.judge_call_count in self.judge_failures:
            return FakeResponse(200, {"response": "not json", "done_reason": "stop"})
        pack = json.loads(
            prompt.split("<EVIDENCE_PACK_JSON>\n", 1)[1].split("\n</EVIDENCE_PACK_JSON>", 1)[0]
        )
        span = pack["source"]["segments"][0]["source_span_id"]
        preference = self.judge_preference or self._preference(pack)
        verdict = {
            "preference": preference,
            "criteria": {
                name: preference
                for name in (
                    "fidelity",
                    "uncertainty",
                    "salience",
                    "contradiction",
                    "utility",
                    "economy",
                )
            },
            "source_span_ids": [span],
            "turn_refs": ["A.T1", "B.T1"],
        }
        return FakeResponse(
            200,
            {
                "response": json.dumps(verdict, ensure_ascii=False),
                "thinking": "",
                "done_reason": "stop",
                "eval_count": 64,
            },
        )

    @staticmethod
    def _preference(pack: dict[str, Any]) -> str:
        """Préfère le candidat au plus grand `num_predict` observé.

        Le marqueur est cherché sur les trois tours : au jeu tenu le premier
        tour est commun aux deux candidats, donc seuls les tours 2 et 3 les
        distinguent.
        """
        markers = []
        for candidate in pack["candidates"]:
            found = [
                int(match.group(1))
                for turn in candidate["turns"]
                for match in NP_MARKER.finditer(turn["output"])
            ]
            markers.append(max(found) if found else 0)
        if markers[0] == markers[1]:
            return "TIE"
        return "A" if markers[0] > markers[1] else "B"


def install(monkeypatch, fake: FakeOllama) -> FakeOllama:
    """Branche le faux serveur sur `requests`.

    Tous les modules du harnais font `import requests` et appellent
    `requests.post` / `requests.get` : remplacer les deux attributs du module
    partagé suffit, et garantit qu'aucun chemin d'appel n'échappe au faux.
    """
    monkeypatch.setattr(requests, "post", fake.post, raising=True)
    monkeypatch.setattr(requests, "get", fake.get, raising=True)
    return fake
