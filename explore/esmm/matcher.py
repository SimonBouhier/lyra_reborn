"""Matcher sémantique pour le consensus ESMM : cosinus mxbai ≥ τ_obj.

τ_obj = 0.78 — **calibré le 2026-07-18** sur 8 paires observées en génération
réelle (gemma3/mistral/llama3.1 sur « fractale ») :
- équivalentes : 0.843 (figure↔forme géométrique), 0.819 (motif récurrent↔
  répétition d'un motif), 0.744 (auto-similarité↔autosimilarité — rattrapée
  lexicalement par match_key, pas par le seuil) ;
- distinctes : 0.726 (figure géométrique↔mathématiques — LE cas piège), 0.570,
  0.545, 0.534 (sierpinski↔mandelbrot : deux fractales différentes, correctement
  séparées).
Choix CONSERVATEUR (précision d'abord) : un faux rapprochement corrompt le
graphe, une fusion ratée ne coûte qu'un peu de consensus. À recalibrer sur
campagne plus large (échantillon n=8 : petit, daté, assumé).
"""
from __future__ import annotations

from core.embeddings import OllamaEmbedder


class SemanticMatcher:
    def __init__(self, embedder: OllamaEmbedder | None = None, threshold: float = 0.78):
        self.embedder = embedder or OllamaEmbedder()
        self.threshold = threshold

    def __call__(self, a: str, b: str) -> bool:
        return self.embedder.similarity(a, b) >= self.threshold
