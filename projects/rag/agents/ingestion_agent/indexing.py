"""
Indexation du contenu pour le système RAG.

Ce module gère:
- La création des index BM25
- La gestion des embeddings
- La recherche hybride
- La mise à jour des index
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

logger = logging.getLogger(__name__)


class ContentIndexer:
    """
    Indexeur de contenu pour le système RAG.
    
    Fonctionnalités:
    - Indexation BM25 pour la recherche textuelle
    - Indexation par embeddings pour la recherche sémantique
    - Recherche hybride (BM25 + Embeddings)
    - Mise à jour incrémentale des index
    """
    
    def __init__(
        self,
        index_dir: Union[Path, str],
        use_bm25: bool = True,
        use_embeddings: bool = True,
        bm25_k1: float = 1.5,
        bm25_b: float = 0.75,
        embedding_dimension: int = 1024,
    ) -> None:
        """
        Initialiser l'indexeur de contenu.
        
        Args:
            index_dir: Dossier pour stocker les index.
            use_bm25: Utiliser BM25.
            use_embeddings: Utiliser les embeddings.
            bm25_k1: Paramètre k1 pour BM25.
            bm25_b: Paramètre b pour BM25.
            embedding_dimension: Dimension des embeddings.
        """
        self.index_dir = Path(index_dir) if isinstance(index_dir, str) else index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.use_bm25 = use_bm25
        self.use_embeddings = use_embeddings
        self.bm25_k1 = bm25_k1
        self.bm25_b = bm25_b
        self.embedding_dimension = embedding_dimension
        
        # Chemins des index
        self.bm25_index_path = self.index_dir / "bm25_index.pkl"
        self.embedding_index_path = self.index_dir / "embedding_index.pkl"
        self.metadata_index_path = self.index_dir / "metadata_index.json"
        
        # Index en mémoire
        self.bm25_index: Any = None
        self.embedding_index: Dict[str, List[float]] = {}
        self.metadata_index: Dict[str, Dict[str, Any]] = {}
        
        # Charger les index existants
        self._load_indexes()
    
    def _load_indexes(self) -> None:
        """Charger les index depuis les fichiers."""
        # Charger BM25
        if self.use_bm25 and self.bm25_index_path.exists():
            try:
                with open(self.bm25_index_path, "rb") as f:
                    self.bm25_index = pickle.load(f)
                logger.info("Index BM25 chargé")
            except Exception as e:
                logger.warning(f"Échec du chargement de l'index BM25: {e}")
        
        # Charger les embeddings
        if self.use_embeddings and self.embedding_index_path.exists():
            try:
                with open(self.embedding_index_path, "rb") as f:
                    self.embedding_index = pickle.load(f)
                logger.info("Index Embeddings chargé")
            except Exception as e:
                logger.warning(f"Échec du chargement de l'index Embeddings: {e}")
        
        # Charger les métadonnées
        if self.metadata_index_path.exists():
            try:
                with open(self.metadata_index_path, "r", encoding="utf-8") as f:
                    self.metadata_index = json.load(f)
                logger.info("Index Métadonnées chargé")
            except Exception as e:
                logger.warning(f"Échec du chargement de l'index Métadonnées: {e}")
    
    def _save_indexes(self) -> None:
        """Sauvegarder les index dans les fichiers."""
        # Sauvegarder BM25
        if self.use_bm25 and self.bm25_index:
            try:
                with open(self.bm25_index_path, "wb") as f:
                    pickle.dump(self.bm25_index, f)
                logger.info("Index BM25 sauvegardé")
            except Exception as e:
                logger.warning(f"Échec de la sauvegarde de l'index BM25: {e}")
        
        # Sauvegarder les embeddings
        if self.use_embeddings and self.embedding_index:
            try:
                with open(self.embedding_index_path, "wb") as f:
                    pickle.dump(self.embedding_index, f)
                logger.info("Index Embeddings sauvegardé")
            except Exception as e:
                logger.warning(f"Échec de la sauvegarde de l'index Embeddings: {e}")
        
        # Sauvegarder les métadonnées
        if self.metadata_index:
            try:
                with open(self.metadata_index_path, "w", encoding="utf-8") as f:
                    json.dump(self.metadata_index, f, indent=2, ensure_ascii=False)
                logger.info("Index Métadonnées sauvegardé")
            except Exception as e:
                logger.warning(f"Échec de la sauvegarde de l'index Métadonnées: {e}")
    
    def add_document(
        self,
        doc_id: str,
        text: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Ajouter un document à l'index.
        
        Args:
            doc_id: Identifiant unique du document.
            text: Texte du document.
            embedding: Embedding du document.
            metadata: Métadonnées du document.
        """
        # Ajouter à BM25
        if self.use_bm25:
            self._add_to_bm25(doc_id, text)
        
        # Ajouter aux embeddings
        if self.use_embeddings and embedding:
            self.embedding_index[doc_id] = embedding
        
        # Ajouter aux métadonnées
        if metadata:
            self.metadata_index[doc_id] = metadata
        else:
            self.metadata_index[doc_id] = {}
        
        # Sauvegarder les index
        self._save_indexes()
        
        logger.info(f"Document ajouté: {doc_id}")
    
    def _add_to_bm25(self, doc_id: str, text: str) -> None:
        """Ajouter un document à l'index BM25."""
        # Implémentation simplifiée de BM25
        # (Dans une implémentation complète, utiliser rank-bm25)
        
        if self.bm25_index is None:
            # Initialiser l'index
            self.bm25_index = {
                "documents": {},
                "term_frequencies": {},
                "document_frequencies": {},
                "average_document_length": 0,
                "total_documents": 0,
            }
        
        # Stocker le document
        self.bm25_index["documents"][doc_id] = text
        self.bm25_index["total_documents"] += 1
        
        # Calculer les fréquences de termes (simplifié)
        # Dans une implémentation complète, utiliser la formule BM25
    
    def add_batch(
        self,
        documents: List[Dict[str, Any]],
        doc_id_key: str = "id",
        text_key: str = "text",
        embedding_key: str = "embedding",
        metadata_key: str = "metadata",
    ) -> None:
        """
        Ajouter un batch de documents à l'index.
        
        Args:
            documents: Liste de documents.
            doc_id_key: Clé pour l'ID du document.
            text_key: Clé pour le texte.
            embedding_key: Clé pour l'embedding.
            metadata_key: Clé pour les métadonnées.
        """
        for doc in documents:
            doc_id = doc.get(doc_id_key)
            text = doc.get(text_key, "")
            embedding = doc.get(embedding_key)
            metadata = doc.get(metadata_key, {})
            
            self.add_document(doc_id, text, embedding, metadata)
        
        logger.info(f"Batch ajouté: {len(documents)} documents")
    
    def search_bm25(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Rechercher dans l'index BM25.
        
        Args:
            query: Requête de recherche.
            top_k: Nombre de résultats.
            
        Returns:
            Liste de résultats avec scores.
        """
        if not self.use_bm25 or self.bm25_index is None:
            return []
        
        # Implémentation simplifiée
        # Dans une implémentation complète, utiliser rank-bm25
        
        results = []
        for doc_id, text in self.bm25_index.get("documents", {}).items():
            # Calculer un score simple (présence de mots)
            score = 0
            query_words = query.lower().split()
            text_words = text.lower().split()
            
            for q_word in query_words:
                if q_word in text_words:
                    score += 1
            
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
    
    def search_embeddings(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        similarity_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Rechercher dans l'index par embeddings.
        
        Args:
            query_embedding: Embedding de la requête.
            top_k: Nombre de résultats.
            similarity_threshold: Seuil de similarité.
            
        Returns:
            Liste de résultats avec scores de similarité.
        """
        if not self.use_embeddings or not self.embedding_index:
            return []
        
        # Normaliser l'embedding de la requête
        query_norm = np.linalg.norm(query_embedding)
        if query_norm > 0:
            query_embedding = [x / query_norm for x in query_embedding]
        
        results = []
        for doc_id, doc_embedding in self.embedding_index.items():
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
    
    def search_hybrid(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 10,
        bm25_weight: float = 0.5,
        embedding_weight: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Recherche hybride (BM25 + Embeddings).
        
        Args:
            query: Requête de recherche.
            query_embedding: Embedding de la requête.
            top_k: Nombre de résultats.
            bm25_weight: Poids de BM25.
            embedding_weight: Poids des embeddings.
            
        Returns:
            Liste de résultats fusionnés.
        """
        results = []
        
        # Recherche BM25
        if self.use_bm25:
            bm25_results = self.search_bm25(query, top_k)
            for result in bm25_results:
                result["bm25_score"] = result.get("score", 0)
                result["embedding_score"] = 0
                results.append(result)
        
        # Recherche par embeddings
        if self.use_embeddings and query_embedding:
            embedding_results = self.search_embeddings(query_embedding, top_k)
            for result in embedding_results:
                result["embedding_score"] = result.get("similarity", 0)
                result["bm25_score"] = 0
                results.append(result)
        
        # Fusionner les résultats (RRF - Reciprocal Rank Fusion)
        if results:
            # Grouper par doc_id
            doc_scores: Dict[str, Dict[str, float]] = {}
            for result in results:
                doc_id = result["doc_id"]
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {"bm25": 0, "embedding": 0, "combined": 0}
                
                doc_scores[doc_id]["bm25"] += result.get("bm25_score", 0)
                doc_scores[doc_id]["embedding"] += result.get("embedding_score", 0)
            
            # Calculer le score combiné
            for doc_id, scores in doc_scores.items():
                combined = (
                    bm25_weight * scores["bm25"] +
                    embedding_weight * scores["embedding"]
                )
                scores["combined"] = combined
            
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
        
        return []
    
    def remove_document(self, doc_id: str) -> bool:
        """
        Supprimer un document de l'index.
        
        Args:
            doc_id: Identifiant du document.
            
        Returns:
            True si la suppression a réussi.
        """
        removed = False
        
        if self.use_bm25 and self.bm25_index and doc_id in self.bm25_index.get("documents", {}):
            del self.bm25_index["documents"][doc_id]
            self.bm25_index["total_documents"] -= 1
            removed = True
        
        if self.use_embeddings and doc_id in self.embedding_index:
            del self.embedding_index[doc_id]
            removed = True
        
        if doc_id in self.metadata_index:
            del self.metadata_index[doc_id]
            removed = True
        
        if removed:
            self._save_indexes()
            logger.info(f"Document supprimé: {doc_id}")
        
        return removed
    
    def clear_index(self) -> None:
        """Effacer tous les index."""
        self.bm25_index = None
        self.embedding_index = {}
        self.metadata_index = {}
        
        # Supprimer les fichiers
        for path in [
            self.bm25_index_path,
            self.embedding_index_path,
            self.metadata_index_path,
        ]:
            if path.exists():
                path.unlink()
        
        logger.info("Tous les index ont été effacés")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtenir les statistiques de l'index."""
        return {
            "bm25_enabled": self.use_bm25,
            "embeddings_enabled": self.use_embeddings,
            "total_documents": len(self.metadata_index),
            "bm25_documents": len(self.bm25_index.get("documents", {})) if self.bm25_index else 0,
            "embedding_documents": len(self.embedding_index),
            "embedding_dimension": self.embedding_dimension,
            "bm25_k1": self.bm25_k1,
            "bm25_b": self.bm25_b,
        }
