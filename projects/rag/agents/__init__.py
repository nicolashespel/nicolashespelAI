"""
Module Agents - Système complet d'agents pour RAG Wiki avec Mistral.

Ce module contient les 4 agents principaux pour OpenWebUI:
1. CleanupAgent - Nettoyage des documents avec Mistral OCR
2. IngestionAgent - Ingestion dans le RAG avec Mistral Embed
3. SearchAgent - Recherche optimisée dans le RAG
4. HealthAgent - Vérification de la santé du système

Utilisation:
    from agents.cleanup_agent import CleanupAgent
    from agents.ingestion_agent import IngestionAgent
    from agents.search_agent import SearchAgent
    from agents.health_agent import HealthAgent
"""

from .cleanup_agent.agent import CleanupAgent
from .ingestion_agent.agent import IngestionAgent
from .search_agent.agent import SearchAgent
from .health_agent.agent import HealthAgent

__all__ = [
    "CleanupAgent",
    "IngestionAgent", 
    "SearchAgent",
    "HealthAgent",
]
