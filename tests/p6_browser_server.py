"""Serveur réservé à la vérification navigateur, sans inférence réelle."""
from app.main import app, request_service
from tests.test_p6_context import ScriptedChat

request_service.chat_adapter = ScriptedChat()
request_service.voice_factory = lambda: (None, "factice")
