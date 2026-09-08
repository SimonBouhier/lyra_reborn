"""État du profil conversationnel, indépendant du contrôleur et du graphe."""
from copy import deepcopy
import math
import time
import uuid


def default_profile():
    return {"id": "conversation_reference_v1", "version": 1,
            "max_input_characters": 16000, "recent_pairs": 30,
            "options": {"num_ctx": 8192, "num_predict": 1024, "temperature": 0.3,
                        "top_p": 0.9, "repeat_penalty": 1.0}, "think": False}


def validate_profile(profile):
    if (not isinstance(profile, dict) or set(profile) != set(default_profile())
            or profile["id"] != "conversation_reference_v1" or profile["version"] != 1
            or type(profile["think"]) is not bool
            or type(profile["max_input_characters"]) is not int
            or not 512 <= profile["max_input_characters"] <= 100000
            or type(profile["recent_pairs"]) is not int or not 0 <= profile["recent_pairs"] <= 100):
        raise ValueError("profil conversationnel invalide")
    opts = profile["options"]
    if not isinstance(opts, dict) or set(opts) != set(default_profile()["options"]):
        raise ValueError("options du profil incomplètes")
    for name in ("num_ctx", "num_predict"):
        if type(opts[name]) is not int or opts[name] <= 0:
            raise ValueError("budget invalide")
    if opts["num_predict"] >= opts["num_ctx"] or opts["num_ctx"] > 131072:
        raise ValueError("budget incohérent")
    for name, low, high in (("temperature", 0, 2), ("top_p", 0, 1), ("repeat_penalty", 0.1, 2)):
        if type(opts[name]) not in (int, float) or not math.isfinite(opts[name]) or not low <= opts[name] <= high:
            raise ValueError("option hors bornes")


class DialogueConversation:
    def __init__(self, llm=None, session_id=None, refractory_ms=0, backend_label=None):
        self.id = session_id or uuid.uuid4().hex
        self.created = time.time()
        self.turns = 0
        self.profile = default_profile()
        self.engine = None
        self.backend_label = "conversation sans modèle"

    def to_state(self):
        return {"schema_version": 2, "id": self.id, "created": self.created,
                "turns": self.turns, "backend_label": self.backend_label,
                "profile": deepcopy(self.profile), "engine": deepcopy(self.engine)}

    @classmethod
    def from_state(cls, state):
        if not isinstance(state, dict) or set(state) != {"schema_version", "id", "created", "turns", "backend_label", "profile", "engine"}:
            raise ValueError("état conversationnel incomplet")
        if state["schema_version"] != 2 or not isinstance(state["id"], str) or not state["id"]:
            raise ValueError("identité conversationnelle invalide")
        if (type(state["turns"]) is not int or state["turns"] < 0
                or type(state["created"]) not in (float, int) or not math.isfinite(state["created"]) or state["created"] <= 0
                or not isinstance(state["backend_label"], str) or not state["backend_label"]):
            raise ValueError("métadonnées conversationnelles invalides")
        validate_profile(state["profile"])
        engine = state["engine"]
        if engine is not None:
            if (not isinstance(engine, dict) or not all(isinstance(engine.get(k), str) and engine[k]
                    for k in ("adapter", "model", "digest", "runtime")) or engine["model"] != state["backend_label"]):
                raise ValueError("contrat moteur invalide")
        conv = cls(session_id=state["id"])
        conv.created, conv.turns = state["created"], state["turns"]
        conv.profile, conv.engine = deepcopy(state["profile"]), deepcopy(engine)
        conv.backend_label = state["backend_label"]
        return conv

    def snapshot(self):
        return {"id": self.id, "tours": self.turns, "profil": deepcopy(self.profile),
                "moteur": self.backend_label, "engine": deepcopy(self.engine)}
