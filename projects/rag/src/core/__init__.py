"""
Module Core - Moteur principal du système RAG Wiki.
"""

from .wiki_engine import WikiEngine
from .ingest_pipeline import IngestPipeline
from .query_pipeline import QueryPipeline
from .lint_pipeline import LintPipeline
from .prompts import INGEST_SYSTEM_PROMPT, QUERY_SYSTEM_PROMPT, LINT_SYSTEM_PROMPT
from .config import WikiConfig

__all__ = [
    "WikiEngine",
    "IngestPipeline",
    "QueryPipeline",
    "LintPipeline",
    "INGEST_SYSTEM_PROMPT",
    "QUERY_SYSTEM_PROMPT",
    "LINT_SYSTEM_PROMPT",
    "WikiConfig",
]
