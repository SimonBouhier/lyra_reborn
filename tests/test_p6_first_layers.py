"""P6 premières couches : un tour traverse contrôle + mémoire.

Échoue bruyamment si le graphe reste vide ou si un prompt vide est avalé.
"""
import pytest

from app.harvest import harvest_concepts
from app.session import LyraConversation
from core.llm import EchoClient


def test_harvest_is_bounded_not_one_node_per_word():
    concepts = harvest_concepts(
        "Explique la récursivité et les fractales dans un langage simple pour moi"
    )
    assert "récursivité" in concepts or "recursivite" in concepts or "fractales" in concepts
    assert "explique" not in concepts
    assert len(concepts) <= 5


def test_empty_prompt_is_rejected():
    conv = LyraConversation(llm=EchoClient(), refractory_ms=0)
    with pytest.raises(ValueError, match="vide"):
        conv.turn("   ")


def test_chat_turn_modulates_and_fills_graph():
    conv = LyraConversation(llm=EchoClient(), refractory_ms=0)
    rec = conv.turn("Explique la récursivité et les fractales")
    assert rec.output  # EchoClient rend une trace, pas du vide
    assert rec.options  # les boutons ont produit des options réelles
    assert rec.modulated is True
    assert rec.graph["nodes"] >= 1
    assert rec.concepts
    snap = conv.snapshot()
    assert snap["tours"] == 1
    assert snap["graphe"]["nodes"] == rec.graph["nodes"]
    assert snap["cas"] == 1


def test_second_turn_injects_nemeton_and_grows_memory():
    conv = LyraConversation(llm=EchoClient(), refractory_ms=0)
    conv.turn("Explique la récursivité et les fractales")
    rec = conv.turn("Relie maintenant récursivité et mémoire")
    assert rec.graph["nodes"] >= 2
    assert "NEMETON" in rec.nemeton
    assert conv.ecology.counts()["pouponniere"] + conv.ecology.counts()["oubli"] + conv.ecology.counts()["compost"] == 2
