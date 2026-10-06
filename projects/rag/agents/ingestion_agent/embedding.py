"""
Génération d'embeddings avec Mistral Embed.

Ce module gère la création d'embeddings pour:
- Les chunks de texte
- Les documents complets
- La recherche sémantique
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx
import numpy as np

logger = logging.getLogger(__name__)


class TextEmbedder:
    """
    Générateur d'embeddings via Mistral Embed API.
    
    Fonctionnalités:
    - Génération d'embeddings pour du texte
    - Batch processing pour les chunks
    - Normalisation des embeddings
    - Cache local optionnel
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base_url: str = "https://api.mistral.ai/v1",
        model: str = "mistral-embed",
        dimension: int = 1024,
        batch_size: int = 32,
        timeout: float = 120.0,
        max_retries: int = 3,
    ) -> None:
        """
        Initialiser le générateur d'embeddings.
        
        Args:
            api_key: Clé API Mistral.
            api_base_url: URL de base de l'API.
            model: Modèle d'embedding.
            dimension: Dimension des embeddings.
            batch_size: Taille des batches.
            timeout: Timeout en secondes.
            max_retries: Nombre de tentatives maximales.
        """
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Clé API Mistral requise. "
                "Définissez MISTRAL_API_KEY ou passez api_key."
            )
        
        self.api_base_url = api_base_url.rstrip("/")
        self.model = model
        self.dimension = dimension
        self.batch_size = batch_size
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Endpoint
        self.api_endpoint = "/embeddings"
        
        # Client HTTP
        self.client = httpx.AsyncClient(
            base_url=self.api_base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        
        # Cache local (optionnel)
        self.cache: Dict[str, List[float]] = {}
        self.use_cache = True
    
    async def _make_request(
        self,
        payload: Dict[str, Any],
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """Effectuer une requête à l'API Embeddings avec gestion des erreurs."""
        try:
            response = await self.client.post(
                self.api_endpoint,
                json=payload,
            )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and retry_count < self.max_retries:
                # Rate limiting - attendre et réessayer
                await asyncio.sleep(1)
                return await self._make_request(payload, retry_count + 1)
            
            logger.error(f"Erreur API Embeddings: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la requête Embeddings: {e}")
            raise
    
    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """Normaliser un embedding."""
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return [x / norm for x in embedding]
        return embedding
    
    async def embed_text(
        self,
        text: str,
        normalize: bool = True,
    ) -> List[float]:
        """
        Générer un embedding pour un texte.
        
        Args:
            text: Texte à embedder.
            normalize: Normaliser l'embedding.
            
        Returns:
            Embedding sous forme de liste de floats.
        """
        # Vérifier le cache
        if self.use_cache and text in self.cache:
            return self.cache[text]
        
        # Préparer le payload
        payload = {
            "model": self.model,
            "input": text,
        }
        
        try:
            result = await self._make_request(payload)
            
            # Extraire l'embedding
            embeddings = result.get("data", [])
            if not embeddings:
                raise ValueError("Aucun embedding retourné")
            
            embedding = embeddings[0].get("embedding", [])
            
            # Normaliser si nécessaire
            if normalize:
                embedding = self._normalize_embedding(embedding)
            
            # Mettre en cache
            if self.use_cache:
                self.cache[text] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"Échec de l'embedding pour le texte: {e}")
            # Retourner un embedding zéro en cas d'erreur
            return [0.0] * self.dimension
    
    async def embed_batch(
        self,
        texts: List[str],
        normalize: bool = True,
    ) -> List[List[float]]:
        """
        Générer des embeddings pour un batch de textes.
        
        Args:
            texts: Liste de textes à embedder.
            normalize: Normaliser les embeddings.
            
        Returns:
            Liste d'embeddings.
        """
        if not texts:
            return []
        
        # Diviser en batches
        embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            # Préparer le payload
            payload = {
                "model": self.model,
                "input": batch,
            }
            
            try:
                result = await self._make_request(payload)
                
                # Extraire les embeddings
                batch_embeddings = result.get("data", [])
                
                for item in batch_embeddings:
                    embedding = item.get("embedding", [])
                    
                    # Normaliser si nécessaire
                    if normalize:
                        embedding = self._normalize_embedding(embedding)
                    
                    embeddings.append(embedding)
                
                # Mettre en cache
                if self.use_cache:
                    for text, embedding in zip(batch, embeddings[-len(batch):]):
                        self.cache[text] = embedding
                        
            except Exception as e:
                logger.error(f"Échec de l'embedding pour le batch {i}: {e}")
                # Ajouter des embeddings zéro pour les textes manquants
                for _ in batch:
                    embeddings.append([0.0] * self.dimension)
        
        return embeddings
    
    async def embed_chunks(
        self,
        chunks: List[Dict[str, Any]],
        text_key: str = "text",
        normalize: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Générer des embeddings pour une liste de chunks.
        
        Args:
            chunks: Liste de chunks (dictionnaires avec clé 'text').
            text_key: Clé pour accéder au texte dans les chunks.
            normalize: Normaliser les embeddings.
            
        Returns:
            Liste de chunks avec embeddings ajoutés.
        """
        if not chunks:
            return chunks
        
        # Extraire les textes
        texts = [chunk.get(text_key, "") for chunk in chunks]
        
        # Générer les embeddings
        embeddings = await self.embed_batch(texts, normalize)
        
        # Ajouter les embeddings aux chunks
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i]
            chunk["embedding_dimension"] = len(embeddings[i])
        
        return chunks
    
    async def embed_file(
        self,
        file_path: Union[Path, str],
        text_key: str = "text",
        normalize: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Générer des embeddings pour un fichier.
        
        Args:
            file_path: Chemin du fichier.
            text_key: Clé pour accéder au texte.
            normalize: Normaliser les embeddings.
            
        Returns:
            Liste de chunks avec embeddings.
        """
        file_path = Path(file_path)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
            
            if isinstance(content, list):
                return await self.embed_chunks(content, text_key, normalize)
            else:
                # Supposer que c'est un seul chunk
                return await self.embed_chunks([content], text_key, normalize)
                
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de {file_path}: {e}")
            return []
    
    def clear_cache(self) -> None:
        """Effacer le cache."""
        self.cache = {}
    
    async def close(self) -> None:
        """Fermer le client HTTP."""
        await self.client.aclose()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.run(self.close())
