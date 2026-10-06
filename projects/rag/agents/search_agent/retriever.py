"""
Récupérateur hybride pour la recherche RAG.

Ce module combine:
- Recherche BM25 pour la correspondances exactes
- Recherche par embeddings pour la sémantique
- Fusion des résultats (RRF - Reciprocal Rank Fusion)
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Récupérateur hybride pour la recherche RAG.
    
    Fonctionnalités:
    - Recherche BM25 pour la correspondance textuelle
    - Recherche par embeddings pour la similarité sémantique
    - Fusion des résultats avec RRF
    - Filtrage par type de page et tags
    """
    
    def __init__(
        self,
        index_dir: Union[Path, str],
        use_bm25: bool = True,
        use_embeddings: bool = True,
        bm25_k1: float = 1.5,
        bm25_b: float = 0.75,
        embedding_dimension: int = 1024,
        bm25_top_k: int = 50,
        embedding_top_k: int = 10,
        rrf_k: int = 60,
    ) -> None:
        """
        Initialiser le récupérateur hybride.
        
        Args:
            index_dir: Dossier contenant les index.
            use_bm25: Utiliser BM25.
            use_embeddings: Utiliser les embeddings.
            bm25_k1: Paramètre k1 pour BM25.
            bm25_b: Paramètre b pour BM25.
            embedding_dimension: Dimension des embeddings.
            bm25_top_k: Nombre de résultats BM25.
            embedding_top_k: Nombre de résultats embeddings.
            rrf_k: Nombre de résultats RRF final.
        """
        self.index_dir = Path(index_dir) if isinstance(index_dir, str) else index_dir
        self.use_bm25 = use_bm25
        self.use_embeddings = use_embeddings
        self.bm25_k1 = bm25_k1
        self.bm25_b = bm25_b
        self.embedding_dimension = embedding_dimension
        self.bm25_top_k = bm25_top_k
        self.embedding_top_k = embedding_top_k
        self.rrf_k = rrf_k
        
        # Charger les index
        self._load_indexes()
    
    def _load_indexes(self) -> None:
        """Charger les index depuis les fichiers."""
        # Charger BM25
        self.bm25_index: Dict[str, Any] = {}
        bm25_path = self.index_dir / "bm25_index.pkl"
        if self.use_bm25 and bm25_path.exists():
            try:
                import pickle
                with open(bm25_path, "rb") as f:
                    self.bm25_index = pickle.load(f)
                logger.info("Index BM25 chargé")
            except Exception as e:
                logger.warning(f"Échec du chargement de l'index BM25: {e}")
        
        # Charger les embeddings
        self.embedding_index: Dict[str, List[float]] = {}
        embedding_path = self.index_dir / "embedding_index.pkl"
        if self.use_embeddings and embedding_path.exists():
            try:
                import pickle
                with open(embedding_path, "rb") as f:
                    self.embedding_index = pickle.load(f)
                logger.info("Index Embeddings chargé")
            except Exception as e:
                logger.warning(f"Échec du chargement de l'index Embeddings: {e}")
        
        # Charger les métadonnées
        self.metadata_index: Dict[str, Dict[str, Any]] = {}
        metadata_path = self.index_dir / "metadata_index.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    self.metadata_index = json.load(f)
                logger.info("Index Métadonnées chargé")
            except Exception as e:
                logger.warning(f"Échec du chargement de l'index Métadonnées: {e}")
    
    def search_bm25(
        self,
        query: str,
        top_k: Optional[int] = None,
        page_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rechercher dans l'index BM25.
        
        Args:
            query: Requête de recherche.
            top_k: Nombre de résultats (par défaut: bm25_top_k).
            page_types: Filtrer par types de pages.
            tags: Filtrer par tags.
            
        Returns:
            Liste de résultats avec scores.
        """
        if not self.use_bm25 or not self.bm25_index:
            return []
        
        top_k = top_k or self.bm25_top_k
        results = []
        
        # Implémentation simplifiée de BM25
        # Dans une implémentation complète, utiliser rank-bm25
        documents = self.bm25_index.get("documents", {})
        
        for doc_id, text in documents.items():
            # Filtrer par type de page
            if page_types:
                metadata = self.metadata_index.get(doc_id, {})
                doc_type = metadata.get("type", "")
                if doc_type not in page_types:
                    continue
            
            # Filtrer par tags
            if tags:
                metadata = self.metadata_index.get(doc_id, {})
                doc_tags = metadata.get("tags", [])
                if not any(tag in doc_tags for tag in tags):
                    continue
            
            # Calculer un score simple
            score = self._calculate_bm25_score(query, text)
            
            if score > 0:
                results.append({
                    "doc_id": doc_id,
                    "score": score,
                    "text": text,
                    "metadata": self.metadata_index.get(doc_id, {}),
                })
        
        # Trier par score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]
    
    def _calculate_bm25_score(self, query: str, text: str) -> float:
        """Calculer un score BM25 simplifié."""
        # Implémentation très simplifiée
        # Dans une implémentation complète, utiliser la formule BM25
        
        query_words = query.lower().split()
        text_words = text.lower().split()
        
        score = 0
        for q_word in query_words:
            if q_word in text_words:
                score += 1
        
        return score
    
    def search_embeddings(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        similarity_threshold: float = 0.7,
        page_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rechercher dans l'index par embeddings.
        
        Args:
            query_embedding: Embedding de la requête.
            top_k: Nombre de résultats (par défaut: embedding_top_k).
            similarity_threshold: Seuil de similarité.
            page_types: Filtrer par types de pages.
            tags: Filtrer par tags.
            
        Returns:
            Liste de résultats avec scores de similarité.
        """
        if not self.use_embeddings or not self.embedding_index:
            return []
        
        top_k = top_k or self.embedding_top_k
        
        # Normaliser l'embedding de la requête
        query_norm = np.linalg.norm(query_embedding)
        if query_norm > 0:
            query_embedding = [x / query_norm for x in query_embedding]
        
        results = []
        for doc_id, doc_embedding in self.embedding_index.items():
            # Filtrer par type de page
            if page_types:
                metadata = self.metadata_index.get(doc_id, {})
                doc_type = metadata.get("type", "")
                if doc_type not in page_types:
                    continue
            
            # Filtrer par tags
            if tags:
                metadata = self.metadata_index.get(doc_id, {})
                doc_tags = metadata.get("tags", [])
                if not any(tag in doc_tags for tag in tags):
                    continue
            
            # Calculer la similarité cosinus
            doc_norm = np.linalg.norm(doc_embedding)
            if doc_norm > 0:
                similarity = np.dot(query_embedding, [x / doc_norm for x in doc_embedding])
            else:
                similarity = 0.0
            
            if similarity >= similarity_threshold:
                results.append({
                    "doc_id": doc_id,
                    "similarity": float(similarity),
                    "embedding": doc_embedding,
                    "metadata": self.metadata_index.get(doc_id, {}),
                })
        
        # Trier par similarité
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return results[:top_k]
    
    async def get_query_embedding(
        self,
        query: str,
        api_key: Optional[str] = None,
        model: str = "mistral-embed",
    ) -> List[float]:
        """
        Obtenir l'embedding d'une requête.
        
        Args:
            query: Requête de recherche.
            api_key: Clé API Mistral.
            model: Modèle d'embedding.
            
        Returns:
            Embedding de la requête.
        """
        if not self.use_embeddings:
            return [0.0] * self.embedding_dimension
        
        # Utiliser l'API Mistral pour obtenir l'embedding
        import httpx
        
        api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not api_key:
            return [0.0] * self.embedding_dimension
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.mistral.ai/v1/embeddings",
                    json={
                        "model": model,
                        "input": query,
                    },
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )
                
                response.raise_for_status()
                result = response.json()
                
                embeddings = result.get("data", [])
                if embeddings:
                    return embeddings[0].get("embedding", [0.0] * self.embedding_dimension)
                
                return [0.0] * self.embedding_dimension
                
        except Exception as e:
            logger.warning(f"Échec de l'obtention de l'embedding: {e}")
            return [0.0] * self.embedding_dimension
    
    async def search_hybrid(
        self,
        query: str,
        top_k: Optional[int] = None,
        api_key: Optional[str] = None,
        use_bm25: Optional[bool] = None,
        use_embeddings: Optional[bool] = None,
        page_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Recherche hybride (BM25 + Embeddings).
        
        Args:
            query: Requête de recherche.
            top_k: Nombre de résultats (par défaut: rrf_k).
            api_key: Clé API Mistral pour l'embedding.
            use_bm25: Utiliser BM25.
            use_embeddings: Utiliser les embeddings.
            page_types: Filtrer par types de pages.
            tags: Filtrer par tags.
            
        Returns:
            Liste de résultats fusionnés.
        """
        top_k = top_k or self.rrf_k
        use_bm25 = use_bm25 if use_bm25 is not None else self.use_bm25
        use_embeddings = use_embeddings if use_embeddings is not None else self.use_embeddings
        
        results = []
        
        # Recherche BM25
        if use_bm25:
            bm25_results = self.search_bm25(query, top_k, page_types, tags)
            for i, result in enumerate(bm25_results):
                result["bm25_rank"] = i + 1
                result["embedding_rank"] = 0
                results.append(result)
        
        # Recherche par embeddings
        if use_embeddings:
            query_embedding = await self.get_query_embedding(query, api_key)
            embedding_results = self.search_embeddings(
                query_embedding, top_k, 0, page_types, tags
            )
            for i, result in enumerate(embedding_results):
                result["embedding_rank"] = i + 1
                if "bm25_rank" not in result:
                    result["bm25_rank"] = 0
                results.append(result)
        
        # Fusionner les résultats avec RRF
        if results:
            return self._reciprocal_rank_fusion(results, top_k)
        
        return []
    
    def _reciprocal_rank_fusion(
        self,
        results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Fusionner les résultats avec Reciprocal Rank Fusion (RRF).
        
        Args:
            results: Liste de tous les résultats.
            top_k: Nombre de résultats finaux.
            
        Returns:
            Liste de résultats fusionnés.
        """
        # Grouper par doc_id
        doc_scores: Dict[str, Dict[str, float]] = {}
        
        for result in results:
            doc_id = result["doc_id"]
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {"bm25": 0, "embedding": 0, "combined": 0}
            
            # Ajouter le score RRF
            if result.get("bm25_rank", 0) > 0:
                doc_scores[doc_id]["bm25"] += 1 / result["bm25_rank"]
            
            if result.get("embedding_rank", 0) > 0:
                doc_scores[doc_id]["embedding"] += 1 / result["embedding_rank"]
        
        # Calculer le score combiné
        for doc_id, scores in doc_scores.items():
            scores["combined"] = scores["bm25"] + scores["embedding"]
        
        # Trier par score combiné
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1]["combined"],
            reverse=True,
        )
        
        # Créer les résultats finaux
        final_results = []
        for doc_id, scores in sorted_docs[:top_k]:
            # Trouver les métadonnées
            metadata = self.metadata_index.get(doc_id, {})
            
            final_results.append({
                "doc_id": doc_id,
                "combined_score": scores["combined"],
                "bm25_score": scores["bm25"],
                "embedding_score": scores["embedding"],
                "metadata": metadata,
            })
        
        return final_results
    
    def search_index_only(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Recherche dans l'index uniquement (sans embeddings).
        
        Args:
            query: Requête de recherche.
            top_k: Nombre de résultats.
            
        Returns:
            Liste de résultats.
        """
        return self.search_bm25(query, top_k)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtenir les statistiques du récupérateur."""
        return {
            "bm25_enabled": self.use_bm25,
            "embeddings_enabled": self.use_embeddings,
            "bm25_documents": len(self.bm25_index.get("documents", {})) if self.bm25_index else 0,
            "embedding_documents": len(self.embedding_index),
            "metadata_documents": len(self.metadata_index),
            "bm25_top_k": self.bm25_top_k,
            "embedding_top_k": self.embedding_top_k,
            "rrf_k": self.rrf_k,
        }
