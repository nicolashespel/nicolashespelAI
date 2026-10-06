"""
Search Agent - Recherche optimisée dans le système RAG.

Cet agent utilise:
- Recherche hybride (BM25 + Mistral Embed)
- Reclassement avec Mistral Small
- Synthèse avec Mistral Large
- Citations automatiques
"""

from .retriever import HybridRetriever
from .reranker import ResultReranker
from .synthesizer import ResponseSynthesizer
from .agent import SearchAgent

__all__ = [
    "HybridRetriever",
    "ResultReranker",
    "ResponseSynthesizer",
    "SearchAgent",
]
