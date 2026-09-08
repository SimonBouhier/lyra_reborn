"""Frontière Ollama du dialogue. Aucun téléchargement ni changement de version."""
from urllib.parse import urlsplit
import json
import urllib.request
import urllib.error

from app.dialogue import validate_profile


class BackendCompatibilityError(RuntimeError):
    pass


class OllamaChatAdapter:
    name = "ollama-chat-v1"
    # Contrat inspecté dans ce tag ; élargissement après contrôles dédiés.
    supported_runtimes = {"0.33.3"}

    @staticmethod
    def _json(base, path, payload=None, timeout=5):
        url = urlsplit(base)
        if url.scheme != "http" or url.hostname not in ("127.0.0.1", "localhost", "::1") or url.username:
            raise BackendCompatibilityError("Le profil P6 actuel accepte uniquement un serveur local HTTP.")
        body = None if payload is None else json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        request = urllib.request.Request(base.rstrip("/") + path, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1000]
            raise BackendCompatibilityError(f"Ollama HTTP {exc.code} : {detail}") from exc
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise BackendCompatibilityError("Réponse Ollama indisponible ou illisible.") from exc

    def freeze(self, client):
        base = client.base_url
        version = self._json(base, "/api/version")["version"]
        if version not in self.supported_runtimes:
            raise BackendCompatibilityError(f"Ollama {version} n'est pas qualifié pour ce contrat de dialogue. Aucune mise à jour automatique.")
        tags = self._json(base, "/api/tags")["models"]
        match = next((r for r in tags if r["name"] == client.model), None)
        if not match:
            raise BackendCompatibilityError("Le modèle exact demandé n'est pas présent ; aucune substitution.")
        return {"adapter": self.name, "model": client.model, "digest": match["digest"],
                "runtime": version, "base_url": base, "timeout": client.timeout}

    def chat(self, engine, messages, profile):
        validate_profile(profile)
        if engine["adapter"] != self.name:
            raise BackendCompatibilityError("Adaptateur du profil inconnu.")
        base = engine["base_url"]
        version = self._json(base, "/api/version")["version"]
        tags = self._json(base, "/api/tags")["models"]
        match = next((r for r in tags if r["name"] == engine["model"]), None)
        if version != engine["runtime"] or version not in self.supported_runtimes or not match or match["digest"] != engine["digest"]:
            raise BackendCompatibilityError("La version d'Ollama ou l'identité du modèle a changé. Ce profil doit être requalifié ; aucun calcul lancé.")
        payload = {"model": engine["model"], "messages": messages, "stream": False,
                   "options": profile["options"], "think": profile["think"],
                   "truncate": False, "shift": False}
        data = self._json(base, "/api/chat", payload, engine["timeout"])
        message = data.get("message") or {}
        if not data.get("done") or message.get("role") != "assistant" or not isinstance(message.get("content"), str) or not message["content"].strip():
            raise BackendCompatibilityError("Le modèle n'a pas fourni de réponse finale exploitable.")
        return {"text": message["content"], "finish_reason": data.get("done_reason"),
                "usage": {"prompt_tokens": data.get("prompt_eval_count"), "output_tokens": data.get("eval_count")}}
