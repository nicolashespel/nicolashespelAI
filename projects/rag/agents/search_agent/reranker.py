"""
Reclassement des résultats avec Mistral Small.

Ce module utilise Mistral Small pour:
- Reclasser les résultats de recherche
- Évaluer la pertinence de chaque résultat
- Sélectionner les meilleurs résultats
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class ResultReranker:
    """
    Reclasseur de résultats utilisant Mistral Small.
    
    Fonctionnalités:
    - Évaluation de la pertinence de chaque résultat
    - Reclassement basé sur la pertinence
    - Sélection des meilleurs résultats
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base_url: str = "https://api.mistral.ai/v1",
        model: str = "mistral-small-latest",
        temperature: float = 0.1,
        max_tokens: int = 1024,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """
        Initialiser le reclasseur.
        
        Args:
            api_key: Clé API Mistral.
            api_base_url: URL de base de l'API.
            model: Modèle pour le reclassement.
            temperature: Température du modèle.
            max_tokens: Nombre maximal de tokens.
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
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Client HTTP
        self.client = httpx.AsyncClient(
            base_url=self.api_base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        
        # Prompt pour l'évaluation de pertinence
        self.rerank_prompt = """
Tu es un évaluateur de pertinence pour un système de recherche RAG.
Ta tâche est d'évaluer la pertinence d'un document par rapport à une requête.

## Instructions

1. **Analyse la requête** : Comprends ce que l'utilisateur cherche.
2. **Analyse le document** : Lis attentivement le contenu du document.
3. **Évalue la pertinence** : Détermine si le document répond à la requête.
4. **Donne un score** : Donne un score de pertinence entre 0 et 100.
   - 0-20 : Non pertinent
   - 21-40 : Peu pertinent
   - 41-60 : Assez pertinent
   - 61-80 : Très pertinent
   - 81-100 : Extrêmement pertinent

## Format de la réponse

Réponds UNIQUEMENT avec un nombre entre 0 et 100, suivi d'une explication EN UNE SEULE LIGNE.

Exemple:
75 - Le document explique le mécanisme d'attention mais pas en détail
100 - Le document répond parfaitement à la question sur les transformers
0 - Le document ne contient aucune information pertinente

## Requête: {query}

## Document:
{document}

Score:
"""
    
    def _get_api_key(self) -> str:
        """Obtenir la clé API."""
        return self.api_key or os.getenv("MISTRAL_API_KEY", "")
    
    async def _make_request(
        self,
        messages: List[Dict[str, Any]],
        retry_count: int = 0,
    ) -> str:
        """Effectuer une requête à l'API."""
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "stream": False,
                },
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extraire le contenu
            choices = result.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            
            return ""
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and retry_count < self.max_retries:
                await asyncio.sleep(1)
                return await self._make_request(messages, retry_count + 1)
            
            logger.error(f"Erreur API: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la requête: {e}")
            raise
    
    async def evaluate_relevance(
        self,
        query: str,
        document: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Évaluer la pertinence d'un document par rapport à une requête.
        
        Args:
            query: Requête de recherche.
            document: Contenu du document.
            metadata: Métadonnées du document.
            
        Returns:
            Résultat de l'évaluation avec score et explication.
        """
        # Préparer le prompt
        prompt = self.rerank_prompt.format(
            query=query,
            document=document[:4000]  # Limiter à 4000 caractères
        )
        
        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]
        
        try:
            response = await self._make_request(messages)
            
            # Parser la réponse (format: "score - explication")
            if "-" in response:
                parts = response.split("-", 1)
                score_str = parts[0].strip()
                explanation = parts[1].strip()
                
                try:
                    score = int(score_str)
                except ValueError:
                    score = 0
            else:
                score = 0
                explanation = response
            
            return {
                "score": min(max(score, 0), 100),  # Clamper entre 0 et 100
                "explanation": explanation,
                "query": query,
                "document_preview": document[:200] + "...",
            }
            
        except Exception as e:
            logger.error(f"Échec de l'évaluation: {e}")
            return {
                "score": 0,
                "explanation": f"Erreur: {e}",
                "query": query,
                "document_preview": document[:200] + "...",
            }
    
    async def rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Reclasser une liste de résultats.
        
        Args:
            query: Requête de recherche.
            results: Liste de résultats à reclasser.
            top_k: Nombre de résultats à retourner.
            
        Returns:
            Liste de résultats reclassés.
        """
        if not results:
            return []
        
        # Évaluer la pertinence de chaque résultat
        tasks = [
            self.evaluate_relevance(
                query,
                result.get("text", "") or result.get("content", ""),
                result.get("metadata", {}),
            )
            for result in results
        ]
        
        evaluations = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Ajouter les scores aux résultats
        for i, result in enumerate(results):
            if i < len(evaluations) and isinstance(evaluations[i], dict):
                result["rerank_score"] = evaluations[i].get("score", 0)
                result["rerank_explanation"] = evaluations[i].get("explanation", "")
            else:
                result["rerank_score"] = 0
                result["rerank_explanation"] = "Erreur d'évaluation"
        
        # Trier par score de reclassement
        results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        
        return results[:top_k]
    
    async def batch_rerank(
        self,
        queries: List[str],
        documents: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Évaluer la pertinence en batch.
        
        Args:
            queries: Liste de requêtes.
            documents: Liste de documents.
            
        Returns:
            Liste de résultats d'évaluation.
        """
        if len(queries) != len(documents):
            raise ValueError("Le nombre de requêtes et de documents doit être identique")
        
        tasks = [
            self.evaluate_relevance(query, doc)
            for query, doc in zip(queries, documents)
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def close(self) -> None:
        """Fermer le client HTTP."""
        await self.client.aclose()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.run(self.close())
