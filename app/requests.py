"""Cycle des demandes P6, dans un serveur et un registre uniques."""
import re
import threading
import uuid

from app.journal import RequestConflict, SQLiteJournalStore
from app.session import SessionBook, SessionBusyError, format_path_reply
from app.storage import SessionStorageError
from core.llm import EchoClient, OllamaClient


def identifier(value):
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value) is None:
        raise ValueError("Identifiant invalide.")
    return value


class RecordingClient:
    """Observe l'appel exact avant de déléguer ; n'est jamais un moteur de repli."""
    def __init__(self, client, observe):
        self.client, self.observe = client, observe
        self.model = getattr(client, "model", "inconnu")

    def generate(self, prompt, options=None, response_format=None):
        self.observe(prompt, options, response_format)
        return self.client.generate(prompt, options, response_format=response_format)


class RequestService:
    def __init__(self, book: SessionBook, store: SQLiteJournalStore, *, voice_factory, chat_adapter=None):
        self.book, self.store, self.voice_factory = book, store, voice_factory
        self._started = False
        self._startup_lock = threading.Lock()
        if chat_adapter is None:
            from app.chat_backend import OllamaChatAdapter
            chat_adapter = OllamaChatAdapter()
        self.chat_adapter = chat_adapter

    def start(self):
        with self._startup_lock:
            if not self._started:
                self.store.recover_interrupted()
                self._started = True

    def get(self, request_id):
        identifier(request_id)
        self.start()
        row = self.store.get(request_id)
        if row["statut"] == "en_cours":
            # Une erreur disque peut avoir empêché de consigner la fin d'un
            # calcul. Réparer seulement si aucun calcul vivant ne détient l'ID.
            try:
                with self.book.exclusive("demande/" + request_id):
                    row = self.store.get(request_id)
                    if row["statut"] == "en_cours":
                        self.store.fail(request_id, len(row["tentatives"]), {
                            "phase": "interruption",
                            "message": "Le calcul n'est plus actif et aucun résultat n'est validé.",
                        }, status="interrompu")
                        row = self.store.get(request_id)
            except SessionBusyError:
                pass
        return row

    def accept(self, request_id, intent):
        identifier(request_id)
        if (not isinstance(intent, dict) or set(intent) != {"texte", "session", "voix"}
                or not isinstance(intent["texte"], str) or not intent["texte"].strip()
                or len(intent["texte"]) > 100_000 or type(intent["voix"]) is not bool):
            raise ValueError("Demande invalide (texte non vide, maximum 100 000 caractères).")
        if intent["session"] is not None:
            identifier(intent["session"])
        self.start()
        try:
            row = self.get(request_id)
        except KeyError:
            row = None
        if row is not None:
            if row["intention"] != intent:
                raise RequestConflict("Cet identifiant désigne une autre demande.")
            return row
        with self.book.exclusive("demande/" + request_id):
            sid = intent["session"] or uuid.uuid4().hex
            with self.book.exclusive(sid):
                new = intent["session"] is None
                conv = self.book.create(session_id=sid) if new else self.book.require(sid)
                try:
                    return self.store.accept(request_id, intent, conv.to_state())
                except Exception:
                    if new:
                        self.book.rollback(sid, None)
                    raise

    def run(self, request_id, *, retry_id=None):
        identifier(request_id)
        if retry_id is not None:
            identifier(retry_id)
            if retry_id == "initial":
                raise ValueError("Identifiant de relance réservé.")
        row = self.get(request_id)
        if row["statut"] in ("termine", "en_cours"):
            return row
        if row["statut"] in ("echoue", "interrompu") and retry_id is None:
            return row
        try:
            with self.book.exclusive("demande/" + request_id):
                with self.book.exclusive(row["session"]):
                    # Une tentative peut avoir fini entre l'observation rapide
                    # et la réservation. Relire avant de choisir sa configuration.
                    row = self.store.get(request_id)
                    attempt = self.store.begin(request_id, retry_id)
                    if attempt is None:
                        return self.store.get(request_id)
                    return self._calculate(row, attempt)
        except SessionBusyError:
            # Une répétition pendant le calcul observe le statut durable.
            return self.store.get(request_id)

    @staticmethod
    def _configuration(client, label):
        config = {"backend_label": label, "model": getattr(client, "model", label),
                  "kind": "ollama" if isinstance(client, OllamaClient) else
                          "echo" if isinstance(client, EchoClient) else "custom"}
        if isinstance(client, OllamaClient):
            config.update(base_url=client.base_url, timeout=client.timeout, think=client.think)
        return config

    def _restore_configuration(self, config):
        label = config["backend_label"]
        if config["kind"] == "ollama":
            client = OllamaClient(model=config["model"], base_url=config["base_url"],
                                  timeout=config["timeout"], think=False)
            # None est un choix enregistré, pas une nouvelle lecture de l'env.
            client.think = config["think"]
            return client, label
        if config["kind"] == "echo":
            return EchoClient(model=config["model"]), label
        return self.book._backend_resolver(label)

    def _calculate(self, row, attempt):
        rid, sid = row["demande"], row["session"]
        previous, phase, dialogue_active = None, "restauration", False
        try:
            previous = self.store.load(sid)
            conv = self.book.require(sid)
            from app.dialogue import DialogueConversation
            if isinstance(conv, DialogueConversation):
                dialogue_active = True
                return self._calculate_dialogue(row, attempt, conv, previous)
            previous_execution = next((a["execution"] for a in reversed(row["tentatives"])
                                       if a["execution"] is not None), None)
            phase = "configuration"
            if previous_execution is not None:
                client, label = self._restore_configuration(previous_execution["client"])
                conv.use_backend(client, label)
            elif row["intention"]["voix"]:
                client, label = self.voice_factory()
                conv.use_backend(client, label)
            else:
                inherited = self.store.previous_execution(sid, row["position"])
                if inherited is not None:
                    client, label = self._restore_configuration(inherited["client"])
                    conv.use_backend(client, label)
            real_client, label = conv.llm, conv.backend_label

            def observe(prompt, options, response_format):
                nonlocal phase
                phase = "conservation_contexte"
                self.store.record_execution(rid, attempt, {
                    "policy": "p6_controle_graphe_v1", "prompt": prompt,
                    "options": options, "response_format": response_format,
                    "client": self._configuration(real_client, label),
                    "session": sid, "tours_avant": conv.turns,
                    "normalisation": "strip du texte soumis ; graphe de la session éventuellement préfixé",
                    "historique_conversationnel_injecte": False,
                })
                phase = "calcul_du_tour"

            conv.use_backend(RecordingClient(real_client, observe), label)
            try:
                rec = conv.turn(row["texte"])
            finally:
                conv.use_backend(real_client, label)
            text = format_path_reply(rec) if isinstance(real_client, EchoClient) else (rec.output or "").strip()
            if not text:
                raise RuntimeError("réponse vide")
            response = {
                "session": sid, "reponse": text, "boutons": rec.knobs_used,
                "boutons_suivants": rec.knobs_next, "options": rec.options,
                "module": rec.modulated, "graphe": rec.graph, "memoire": rec.ecology,
                "concepts": rec.concepts, "nemeton": rec.nemeton, "moteur": label,
            }
            phase = "publication"
            self.store.complete(rid, attempt, conv.to_state(), response)
        except Exception as exc:
            if dialogue_active:
                raise  # le parcours dialogue possède sa publication et sa reprise
            if phase == "publication":
                # Une exception après commit ne permet pas d'annuler un résultat
                # déjà durable. Relire sa décision avant de décider d'un échec.
                try:
                    durable = self.store.get(rid)
                except SessionStorageError:
                    self.book.rollback(sid, None)
                    raise SessionStorageError("Issue de publication inconnue ; relire la demande.") from exc
                if durable["statut"] == "termine":
                    self.book.rollback(sid, None)
                    return durable
            error = {"phase": phase, "type": type(exc).__name__,
                     "message": f"La tentative a échoué pendant : {phase}. Une relance explicite est nécessaire."}
            try:
                self.book.rollback(sid, previous)
            except Exception as rollback_error:
                error["rollback"] = type(rollback_error).__name__
                error["message"] += " L'état en mémoire doit être restauré depuis le journal."
            self.store.fail(rid, attempt, error)
        return self.store.get(rid)

    def _calculate_dialogue(self, row, attempt, conv, previous):
        from app.context import assemble_context
        rid, sid, phase = row["demande"], row["session"], "contexte"
        try:
            context = assemble_context(self.store.context_source(rid), conv.profile)
            phase = "compatibilite"
            engine = next((a["execution"]["client"] for a in reversed(row["tentatives"])
                           if a["execution"] and a["execution"].get("client")), conv.engine)
            if engine is None and row["intention"]["voix"]:
                client, _ = self.voice_factory()
                if isinstance(client, EchoClient):
                    raise RuntimeError("La voix réelle est désactivée dans la configuration ; aucun modèle substitué.")
                engine = self.chat_adapter.freeze(client)
            execution = {"policy": conv.profile["id"], "profile": conv.profile,
                         "context": context, "client": engine, "session": sid}
            self.store.record_execution(rid, attempt, execution)
            phase = "generation_conversationnelle"
            if engine is None:
                result = {"text": "Contexte préparé et enregistré. Aucun modèle n'a été appelé. Utilise « Demander une voix » pour une réponse conversationnelle.",
                          "usage": {}, "finish_reason": "demonstration"}
            else:
                result = self.chat_adapter.chat(engine, context["messages"], conv.profile)
            execution["result"] = {"usage": result["usage"], "finish_reason": result["finish_reason"]}
            self.store.record_execution(rid, attempt, execution)
            conv.engine = engine
            if engine:
                conv.backend_label = engine["model"]
            conv.turns += 1
            response = {"session": sid, "reponse": result["text"], "profil": conv.profile,
                        "moteur": conv.backend_label, "context": context, "usage": result["usage"],
                        "finish_reason": result["finish_reason"], "demonstration": engine is None}
            phase = "publication"
            self.store.complete(rid, attempt, conv.to_state(), response)
        except Exception as exc:
            if phase == "publication":
                try:
                    durable = self.store.get(rid)
                except SessionStorageError:
                    self.book.rollback(sid, None)
                    raise
                if durable["statut"] == "termine":
                    self.book.rollback(sid, None)
                    return durable
            self.book.rollback(sid, previous)
            self.store.fail(rid, attempt, {"phase": phase, "type": type(exc).__name__,
                "message": str(exc) if isinstance(exc, (ValueError, RuntimeError)) else "Tentative interrompue. Relance explicite nécessaire."})
        return self.store.get(rid)
