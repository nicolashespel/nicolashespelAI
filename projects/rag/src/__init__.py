"""
RAG Wiki - Système de Connaissance Compounding

Ce package contient l'implémentation principale du système RAG Wiki.
"""

__version__ = "0.1.0"
__author__ = "Nicolas Hespel"
__description__ = "Système de gestion de connaissances compounding pour LLM"

from .core import WikiEngine
from .agents import (
    BaseAgent,
    OpenWebUIAgent,
    PreprocessingAgent,
    WikiIngestorAgent,
    WikiLibrarianAgent,
    WikiLinterAgent,
)
from .types import *

__all__ = [
    "WikiEngine",
    "BaseAgent",
    "OpenWebUIAgent",
    "PreprocessingAgent",
    "WikiIngestorAgent",
    "WikiLibrarianAgent",
    "WikiLinterAgent",
] + __all__ if hasattr(__import__(".types", fromlist=["__all__"]), "__all__") else []
