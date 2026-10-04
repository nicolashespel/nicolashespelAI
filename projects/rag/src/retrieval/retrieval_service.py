"""
Service de récupération pour le système RAG Wiki.

Ce module contient la classe RetrievalService qui orchestrer les différents
mécanismes de récupération (BM25, embeddings, hybride).
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .base_retriever import BaseRetriever
from .bm25_retriever import BM25Retriever
from .embedding_retriever import EmbeddingRetriever
from .hybrid_retriever import HybridRetriever
from ..indexes import IndexManager
from ..core.config import WikiConfig, get_config


class RetrievalService:
    """
    Service de récupération pour le système RAG Wiki.
    
    Ce service orchestrer les différents mécanismes de récupération et fournit
    une interface unifiée pour la recherche dans le vault.
    """
    
    def __init__(
        self,
        vault_path: Path,
        index_manager: IndexManager,
        config: Optional[WikiConfig] = None,
    ) -> None:
        """
        Initialiser le RetrievalService.
        
        Args:
            vault_path: Chemin du vault.
            index_manager: Gestionnaire des index.
            config: Configuration du wiki.
        """
        self.vault_path = vault_path
        self.index_manager = index_manager
        self.config = config or get_config()
        
        # Initialiser les retrievers
        self.bm25_retriever = BM25Retriever(vault_path, index_manager)
        self.embedding_retriever = EmbeddingRetriever(vault_path, index_manager)
        self.hybrid_retriever = HybridRetriever(
            vault_path, index_manager, self.bm25_retriever, self.embedding_retriever
        )
    
    async def search(
        self,
        query: str,
        use_index: bool = True,
        use_bm25: bool = True,
        use_embeddings: bool = True,
        k: int = 10,
    ) -> List[Tuple[Path, float]]:
        """
        Effectuer une recherche.
        
        Args:
            query: Requête de recherche.
            use_index: Utiliser la recherche dans l'index.
            use_bm25: Utiliser BM25.
            use_embeddings: Utiliser les embeddings.
            k: Nombre de résultats.
            
        Returns:
            Liste de tuples (chemin, score).
        """
        results: List[Tuple[Path, float]] = []
        
        # Recherche dans l'index
        if use_index:
            index_results = self._search_index(query)
            results.extend(index_results)
        
        # Recherche BM25
        if use_bm25:
            bm25_results = await self.bm25_retriever.search(query, k=self.config.bm25_k)
            results.extend(bm25_results)
        
        # Recherche par embeddings
        if use_embeddings:
            embedding_results = await self.embedding_retriever.search(query, k=self.config.embedding_k)
            results.extend(embedding_results)
        
        # Fusionner et trier les résultats
        if results:
            # Supprimer les doublons
            seen = {}
            for path, score in results:
                if str(path) in seen:
                    seen[str(path)] = max(seen[str(path)], score)
                else:
                    seen[str(path)] = score
            
            # Convertir en liste et trier
            results = [(Path(k), v) for k, v in seen.items()]
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Limiter à k résultats
            results = results[:k]
        
        return results
    
    async def bm25_search(
        self,
        query: str,
        k: int = 10,
    ) -> List[Tuple[Path, float]]:
        """
        Effectuer une recherche BM25.
        
        Args:
            query: Requête de recherche.
            k: Nombre de résultats.
            
        Returns:
            Liste de tuples (chemin, score).
        """
        return await self.bm25_retriever.search(query, k=k)
    
    async def embedding_search(
        self,
        query: str,
        k: int = 10,
    ) -> List[Tuple[Path, float]]:
        """
        Effectuer une recherche par embeddings.
        
        Args:
            query: Requête de recherche.
            k: Nombre de résultats.
            
        Returns:
            Liste de tuples (chemin, score).
        """
        return await self.embedding_retriever.search(query, k=k)
    
    async def hybrid_search(
        self,
        query: str,
        k: int = 10,
    ) -> List[Tuple[Path, float]]:
        """
        Effectuer une recherche hybride.
        
        Args:
            query: Requête de recherche.
            k: Nombre de résultats.
            
        Returns:
            Liste de tuples (chemin, score).
        """
        return await self.hybrid_retriever.search(query, k=k)
    
    def _search_index(self, query: str) -> List[Tuple[Path, float]]:
        """
        Rechercher dans l'index.
        
        Args:
            query: Requête de recherche.
            
        Returns:
            Liste de tuples (chemin, score).
        """
        # Implémentation basique pour l'instant
        # Dans une implémentation complète, cela utiliserait l'index structuré
        
        results = []
        
        # Obtenir l'index
        index = self.index_manager.get_index()
        if index is None:
            return results
        
        # Rechercher dans les pages par tag
        if hasattr(index, "pages_by_tag"):
            for tag, pages in index.pages_by_tag.items():
                if query.lower() in tag.lower():
                    for page_path in pages:
                        results.append((Path(page_path), 1.0))
        
        # Rechercher dans les pages par type
        if hasattr(index, "pages_by_type"):
            for page_type, pages in index.pages_by_type.items():
                if query.lower() in page_type.lower():
                    for page_path in pages:
                        results.append((Path(page_path), 0.8))
        
        return results
    
    def get_retriever(self, retriever_type: str) -> Optional[BaseRetriever]:
        """
        Obtenir un retriever spécifique.
        
        Args:
            retriever_type: Type de retriever (bm25, embedding, hybrid).
            
        Returns:
            Retriever ou None.
        """
        retriever_map = {
            "bm25": self.bm25_retriever,
            "embedding": self.embedding_retriever,
            "hybrid": self.hybrid_retriever,
        }
        
        return retriever_map.get(retriever_type)
    
    def update_indexes(self) -> None:
        """Mettre à jour tous les index."""
        self.bm25_retriever.update_index()
        self.embedding_retriever.update_index()
    
    def clear_cache(self) -> None:
        """Effacer le cache des retrievers."""
        self.bm25_retriever.clear_cache()
        self.embedding_retriever.clear_cache()
    
    def close(self) -> None:
        """Fermer les ressources du RetrievalService."""
        self.bm25_retriever.close()
        self.embedding_retriever.close()
        self.hybrid_retriever.close()
