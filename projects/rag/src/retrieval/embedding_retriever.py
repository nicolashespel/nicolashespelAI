"""
Retriever par embeddings pour le système RAG Wiki.

Ce module contient la classe EmbeddingRetriever qui implémente la recherche
par embeddings sur les pages du vault.
"""

import asyncio
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json

from .base_retriever import BaseRetriever
from ..indexes import IndexManager
from ..storage import VaultManager


class EmbeddingRetriever(BaseRetriever):
    """
    Retriever par embeddings pour le système RAG Wiki.
    
    Ce retriever implémente la recherche par similarité sémantique
    en utilisant des embeddings de texte.
    """
    
    def __init__(
        self,
        vault_path: Path,
        index_manager: IndexManager,
    ) -> None:
        """
        Initialiser le EmbeddingRetriever.
        
        Args:
            vault_path: Chemin du vault.
            index_manager: Gestionnaire des index.
        """
        super().__init__(vault_path, index_manager)
        
        # Chemin du fichier d'embeddings
        self._embeddings_path = vault_path / "embeddings.json"
        
        # Embeddings
        self._embeddings: Dict[str, List[float]] = {}
        self._embedding_dim = 0
        
        # Cache
        self._cache: Dict[str, List[Tuple[Path, float]]] = {}
        
        # Initialiser
        self.update_index()
    
    def update_index(self) -> None:
        """Mettre à jour l'index des embeddings."""
        # Charger ou générer les embeddings
        self._load_or_generate_embeddings()
        
        self.initialize()
    
    def _load_or_generate_embeddings(self) -> None:
        """
        Charger ou générer les embeddings.
        """
        # Vérifier si le fichier d'embeddings existe
        if self._embeddings_path.exists():
            self._load_embeddings()
        else:
            self._generate_embeddings()
    
    def _load_embeddings(self) -> None:
        """
        Charger les embeddings depuis le fichier.
        """
        try:
            with open(self._embeddings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._embeddings = data.get("embeddings", {})
                self._embedding_dim = data.get("dimension", 0)
        except Exception as e:
            print(f"Erreur lors du chargement des embeddings: {e}")
            self._embeddings = {}
            self._embedding_dim = 0
    
    def _generate_embeddings(self) -> None:
        """
        Générer les embeddings pour toutes les pages.
        
        Note: Dans une implémentation complète, cela utiliserait un vrai
        modèle d'embedding. Ici, on génère des embeddings aléatoires pour
        l'exemple.
        """
        print("Génération des embeddings (cette opération peut prendre du temps)...")
        
        vault_manager = VaultManager(self.vault_path)
        all_pages = vault_manager.get_all_pages()
        
        self._embeddings = {}
        
        # Utiliser une dimension par défaut
        self._embedding_dim = 1536  # Dimension typique pour text-embedding-3-small
        
        for page_path in all_pages:
            content = vault_manager.read_page_content(page_path)
            if content:
                # Générer un embedding aléatoire (à remplacer par un vrai modèle)
                embedding = self._generate_random_embedding(self._embedding_dim)
                self._embeddings[str(page_path)] = embedding.tolist()
        
        # Sauvegarder les embeddings
        self._save_embeddings()
    
    def _generate_random_embedding(self, dim: int) -> np.ndarray:
        """
        Générer un embedding aléatoire.
        
        Args:
            dim: Dimension de l'embedding.
            
        Returns:
            Embedding aléatoire.
        """
        # Générer des valeurs aléatoires entre -1 et 1
        return np.random.uniform(-1, 1, dim)
    
    def _save_embeddings(self) -> None:
        """
        Sauvegarder les embeddings dans le fichier.
        """
        try:
            data = {
                "embeddings": self._embeddings,
                "dimension": self._embedding_dim,
                "generated": True,
            }
            
            with open(self._embeddings_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des embeddings: {e}")
    
    async def _generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Générer l'embedding pour une requête.
        
        Args:
            query: Requête.
            
        Returns:
            Embedding de la requête.
        """
        # Dans une implémentation complète, cela utiliserait un vrai modèle
        # Pour l'instant, on génère un embedding aléatoire
        return self._generate_random_embedding(self._embedding_dim)
    
    def _cosine_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
    ) -> float:
        """
        Calculer la similarité cosinus entre deux embeddings.
        
        Args:
            embedding1: Premier embedding.
            embedding2: Deuxième embedding.
            
        Returns:
            Similarité cosinus.
        """
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def search(
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
        # Vérifier le cache
        cache_key = f"{query}:{k}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Générer l'embedding de la requête
        query_embedding = await self._generate_query_embedding(query)
        
        # Calculer les similarités
        similarities: List[Tuple[str, float]] = []
        
        for doc_path, doc_embedding in self._embeddings.items():
            doc_embedding_array = np.array(doc_embedding)
            similarity = self._cosine_similarity(query_embedding, doc_embedding_array)
            similarities.append((doc_path, similarity))
        
        # Trier par similarité
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Convertir en liste de tuples Path, float
        results = [(Path(doc_path), similarity) for doc_path, similarity in similarities[:k]]
        
        # Mettre en cache
        self._cache[cache_key] = results
        
        return results
    
    def clear_cache(self) -> None:
        """Effacer le cache."""
        self._cache = {}
    
    def get_embedding_info(self) -> Dict[str, Any]:
        """
        Obtenir des informations sur les embeddings.
        
        Returns:
            Dictionnaire avec les informations.
        """
        return {
            "total_embeddings": len(self._embeddings),
            "dimension": self._embedding_dim,
            "embeddings_path": str(self._embeddings_path),
        }
    
    def regenerate_embeddings(self) -> None:
        """
        Régénérer tous les embeddings.
        """
        print("Régénération des embeddings...")
        self._generate_embeddings()
        print(f"Embeddings régénérés pour {len(self._embeddings)} pages.")
    
    def close(self) -> None:
        """Fermer les ressources du EmbeddingRetriever."""
        self.clear_cache()
        self._initialized = False
