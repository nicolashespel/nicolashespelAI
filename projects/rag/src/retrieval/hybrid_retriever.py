"""
Retriever hybride pour le système RAG Wiki.

Ce module contient la classe HybridRetriever qui combine les approches
BM25 et embeddings pour une recherche hybride.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from .base_retriever import BaseRetriever
from .bm25_retriever import BM25Retriever
from .embedding_retriever import EmbeddingRetriever
from ..indexes import IndexManager


class HybridRetriever(BaseRetriever):
    """
    Retriever hybride pour le système RAG Wiki.
    
    Ce retriever combine les scores de BM25 et des embeddings en utilisant
    la méthode RRF (Reciprocal Rank Fusion) pour produire des résultats
    plus robustes.
    """
    
    def __init__(
        self,
        vault_path: Path,
        index_manager: IndexManager,
        bm25_retriever: BM25Retriever,
        embedding_retriever: EmbeddingRetriever,
    ) -> None:
        """
        Initialiser le HybridRetriever.
        
        Args:
            vault_path: Chemin du vault.
            index_manager: Gestionnaire des index.
            bm25_retriever: Retriever BM25.
            embedding_retriever: Retriever par embeddings.
        """
        super().__init__(vault_path, index_manager)
        
        self.bm25_retriever = bm25_retriever
        self.embedding_retriever = embedding_retriever
        
        # Paramètres RRF
        self.k = 60  # Constante RRF
        
        # Cache
        self._cache: Dict[str, List[Tuple[Path, float]]] = {}
        
        self.initialize()
    
    async def search(
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
        # Vérifier le cache
        cache_key = f"{query}:{k}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Effectuer les recherches parallèles
        bm25_task = asyncio.create_task(
            self.bm25_retriever.search(query, k=k)
        )
        embedding_task = asyncio.create_task(
            self.embedding_retriever.search(query, k=k)
        )
        
        # Attendre les résultats
        bm25_results, embedding_results = await asyncio.gather(
            bm25_task,
            embedding_task,
        )
        
        # Appliquer RRF
        rrf_results = self._apply_rrf(bm25_results, embedding_results, k)
        
        # Mettre en cache
        self._cache[cache_key] = rrf_results
        
        return rrf_results
    
    def _apply_rrf(
        self,
        results1: List[Tuple[Path, float]],
        results2: List[Tuple[Path, float]],
        k: int,
    ) -> List[Tuple[Path, float]]:
        """
        Appliquer la fusion RRF (Reciprocal Rank Fusion).
        
        Args:
            results1: Résultats de la première méthode.
            results2: Résultats de la deuxième méthode.
            k: Nombre de résultats finaux.
            
        Returns:
            Résultats fusionnés.
        """
        # Créer un dictionnaire pour accumuler les scores RRF
        rrf_scores: Dict[str, float] = {}
        
        # Appliquer RRF à chaque liste de résultats
        for rank, (path, _) in enumerate(results1, 1):
            rrf_score = 1.0 / (self.k + rank)
            rrf_scores[str(path)] = rrf_scores.get(str(path), 0.0) + rrf_score
        
        for rank, (path, _) in enumerate(results2, 1):
            rrf_score = 1.0 / (self.k + rank)
            rrf_scores[str(path)] = rrf_scores.get(str(path), 0.0) + rrf_score
        
        # Trier par score RRF
        sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Convertir en liste de tuples Path, float
        results = [(Path(path), score) for path, score in sorted_rrf[:k]]
        
        return results
    
    def _normalize_scores(
        self,
        results: List[Tuple[Path, float]],
    ) -> List[Tuple[Path, float]]:
        """
        Normaliser les scores entre 0 et 1.
        
        Args:
            results: Résultats avec scores.
            
        Returns:
            Résultats avec scores normalisés.
        """
        if not results:
            return results
        
        # Trouver le score max
        max_score = max(score for _, score in results)
        
        if max_score == 0:
            return [(path, 0.0) for path, _ in results]
        
        # Normaliser
        normalized = [(path, score / max_score) for path, score in results]
        
        return normalized
    
    def clear_cache(self) -> None:
        """Effacer le cache."""
        self._cache = {}
    
    def get_rrf_info(self) -> Dict[str, Any]:
        """
        Obtenir des informations sur le RRF.
        
        Returns:
            Dictionnaire avec les informations.
        """
        return {
            "k": self.k,
            "cache_size": len(self._cache),
        }
    
    def close(self) -> None:
        """Fermer les ressources du HybridRetriever."""
        self.clear_cache()
        self._initialized = False
