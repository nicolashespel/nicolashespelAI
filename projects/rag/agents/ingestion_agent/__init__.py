"""
Ingestion Agent - Intègre les documents nettoyés dans le système RAG.

Cet agent utilise:
- Mistral Large pour comprendre et structurer
- Mistral Embed pour générer les embeddings
- BM25 et recherche hybride pour l'indexation
"""

from .chunking import TextChunker
from .embedding import TextEmbedder
from .indexing import ContentIndexer
from .agent import IngestionAgent

__all__ = [
    "TextChunker",
    "TextEmbedder",
    "ContentIndexer",
    "IngestionAgent",
]
