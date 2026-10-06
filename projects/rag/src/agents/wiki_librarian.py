"""
Agent Wiki Librarian pour le système RAG Wiki.

Utilise mistral-embed pour les embeddings et Mistral API pour les requêtes.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import numpy as np

from ..core.config import WikiConfig
from ..core.wiki_engine import WikiEngine
from ..retrieval import RetrievalService, HybridRetriever
from ..storage import VaultManager
from ..utils.path_utils import get_file_type
from .base_agent import BaseAgent


logger = logging.getLogger(__name__)


class WikiLibrarianAgent(BaseAgent):
    """
    Agent Wiki Librarian pour le système RAG Wiki.
    
    Cet agent est responsable des requêtes :
    - Recherche dans l'index et les pages
    - Synthèse des réponses avec citations
    - Sauvegarde des réponses utiles
    - Utilisation de mistral-embed pour les embeddings
    """
    
    def __init__(
        self,
        vault_path: Path,
        config: Optional[WikiConfig] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """
        Initialiser l'agent Wiki Librarian.
        
        Args:
            vault_path: Chemin du vault.
            config: Configuration du wiki.
            api_key: Clé API Mistral (optionnel).
        """
        super().__init__(
            name="WikiLibrarian",
            role="Recherche et synthèse dans le vault",
            vault_manager=VaultManager(vault_path),
            config=config or WikiConfig(vault_path=vault_path),
        )
        
        self.vault_path = vault_path
        self.api_key = api_key or (config.api_key if config else None)
        self.wiki_engine = WikiEngine(config=self.config, vault_path=vault_path)
        self.retrieval_service = RetrievalService(vault_path)
        
        # Charger la configuration Mistral
        self.mistral_config = self._load_mistral_config()
        
        # Configuration des embeddings
        self.embedding_model = self.mistral_config.get("embeddings", {}).get("model", "mistral-embed")
        self.embedding_dimension = self.mistral_config.get("embeddings", {}).get("dimension", 1024)
        
        # Configuration LLM
        self.llm_model = self.mistral_config.get("agents", {}).get("WikiLibrarianAgent", {}).get(
            "llm_model", "mistral-large-latest"
        )
        self.temperature = self.mistral_config.get("agents", {}).get("WikiLibrarianAgent", {}).get(
            "temperature", 0.4
        )
        self.max_tokens = self.mistral_config.get("agents", {}).get("WikiLibrarianAgent", {}).get(
            "max_tokens", 4096
        )
        
        # Client HTTP pour Mistral API
        self.api_base_url = self.mistral_config.get("global", {}).get(
            "api_base_url", "https://api.mistral.ai/v1"
        )
        self.client = httpx.AsyncClient(
            base_url=self.api_base_url,
            timeout=120,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        )
    
    def _load_mistral_config(self) -> Dict[str, Any]:
        """Charger la configuration Mistral."""
        config_path = self.vault_path / "configs" / "mistral_config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return {
                "embeddings": {"model": "mistral-embed", "dimension": 1024},
                "agents": {"WikiLibrarianAgent": {"llm_model": "mistral-large-latest"}},
                "global": {"api_base_url": "https://api.mistral.ai/v1"},
            }
    
    async def execute(
        self,
        query: str,
        top_k: int = 5,
        save_answer: bool = True,
        use_hybrid: bool = True,
    ) -> Dict[str, Any]:
        """
        Exécuter une requête.
        
        Args:
            query: Requête à traiter.
            top_k: Nombre de résultats à retourner.
            save_answer: Si True, sauvegarder la réponse utile.
            use_hybrid: Si True, utiliser la recherche hybride (BM25 + embeddings).
            
        Returns:
            Rapport de requête.
        """
        start_time = datetime.now()
        report: Dict[str, Any] = {
            "query": query,
            "success": False,
            "answer": "",
            "sources": [],
            "citations": [],
            "confidence": 0.0,
            "duration_seconds": 0,
            "error": None,
        }
        
        try:
            # Étape 1: Recherche
            results = await self._search(query, top_k=top_k, use_hybrid=use_hybrid)
            report["sources"] = results.get("sources", [])
            
            # Étape 2: Synthèse
            answer, citations, confidence = await self._synthesize(
                query, results.get("context", "")
            )
            report["answer"] = answer
            report["citations"] = citations
            report["confidence"] = confidence
            
            # Étape 3: Sauvegarde si utile
            if save_answer and self._is_useful_answer(answer, confidence):
                await self._save_answer(query, answer, citations, confidence)
            
            report["success"] = True
            report["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            
            return report
            
        except Exception as e:
            report["error"] = str(e)
            report["success"] = False
            report["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            logger.error(f"Erreur requête: {str(e)}", exc_info=True)
            return report
    
    async def _search(
        self,
        query: str,
        top_k: int = 5,
        use_hybrid: bool = True,
    ) -> Dict[str, Any]:
        """
        Rechercher dans le vault.
        
        Args:
            query: Requête de recherche.
            top_k: Nombre de résultats.
            use_hybrid: Si True, utiliser la recherche hybride.
            
        Returns:
            Résultats de recherche.
        """
        if use_hybrid:
            # Recherche hybride (BM25 + embeddings)
            hybrid_retriever = HybridRetriever(self.vault_path)
            results = await hybrid_retriever.retrieve(query, top_k=top_k)
            
            # Formater les résultats
            context = "\n\n".join([
                f"--- Source: {r.get('path', 'inconnu')} (score: {r.get('score', 0):.2f})\n{r.get('content', '')}"
                for r in results
            ])
            
            return {
                "context": context,
                "sources": [
                    {
                        "path": r.get("path"),
                        "score": r.get("score"),
                        "content": r.get("content", "")[:200] + "...",
                    }
                    for r in results
                ],
            }
        else:
            # Recherche simple (BM25 seulement)
            bm25_results = self.retrieval_service.bm25_search(query, top_k=top_k)
            context = "\n\n".join([
                f"--- Source: {r.get('path', 'inconnu')} (score: {r.get('score', 0):.2f})\n{r.get('content', '')}"
                for r in bm25_results
            ])
            
            return {
                "context": context,
                "sources": [
                    {
                        "path": r.get("path"),
                        "score": r.get("score"),
                        "content": r.get("content", "")[:200] + "...",
                    }
                    for r in bm25_results
                ],
            }
    
    async def _synthesize(
        self,
        query: str,
        context: str,
    ) -> Tuple[str, List[str], float]:
        """
        Synthétiser une réponse à partir du contexte.
        
        Args:
            query: Requête originale.
            context: Contexte récupéré de la recherche.
            
        Returns:
            Tuple avec (réponse, citations, confiance).
        """
        try:
            # Préparer le prompt
            prompt = f"""
Tu es un assistant expert en analyse de documents techniques (IA, SEO, développement web).
Réponds à la question suivante en te basant UNIQUEMENT sur le contexte fourni.

**Question**: {query}

**Contexte**:
{context}

**Instructions**:
1. Si le contexte ne contient pas assez d'informations pour répondre, dis "Je n'ai pas assez d'informations dans mes documents pour répondre à cette question."
2. Sinon, fournis une réponse complète et structurée.
3. Cite TOUJOURS tes sources en utilisant le format [source:chemin/vers/fichier.md, §paragraphe].
4. Si plusieurs sources sont utilisées, liste-les toutes.
5. Sois précis et technique.

**Réponse**:
"""
            
            # Appeler Mistral API
            payload = {
                "model": self.llm_model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "top_p": 0.9,
            }
            
            response = await self.client.post(
                "/chat/completions",
                json=payload,
            )
            
            if response.status_code != 200:
                logger.error(f"Erreur API Mistral: {response.status_code} - {response.text}")
                return "Erreur lors de la synthèse.", [], 0.0
            
            result = response.json()
            answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Extraire les citations (format [source:...])
            citations = self._extract_citations(answer)
            
            # Calculer la confiance (basée sur le nombre de sources)
            confidence = min(1.0, len(citations) * 0.2 + 0.5) if citations else 0.3
            
            return answer, citations, confidence
            
        except Exception as e:
            logger.error(f"Erreur synthèse: {str(e)}", exc_info=True)
            return f"Erreur: {str(e)}", [], 0.0
    
    def _extract_citations(self, text: str) -> List[str]:
        """Extraire les citations du texte."""
        import re
        citations = re.findall(r'\[source:[^\]]+\]', text)
        return [c[8:-1] for c in citations]  # Supprimer [source: et ]
    
    def _is_useful_answer(self, answer: str, confidence: float) -> bool:
        """Déterminer si une réponse est utile à sauvegarder."""
        # Heuristiques pour déterminer l'utilité
        if confidence < 0.6:
            return False
        if len(answer) < 100:  # Réponse trop courte
            return False
        if "je n'ai pas assez d'informations" in answer.lower():
            return False
        if "erreur" in answer.lower():
            return False
        return True
    
    async def _save_answer(
        self,
        query: str,
        answer: str,
        citations: List[str],
        confidence: float,
    ) -> None:
        """Sauvegarder une réponse utile dans le vault."""
        try:
            # Créer un nom de fichier basé sur la requête
            from ..utils.text_utils import normalize_name
            file_name = normalize_name(query[:50]) + ".md"
            save_path = self.vault_path / "wiki" / "synthesis" / file_name
            
            # Contenu de la page
            content = f"""---
type: synthesis
title: "{query}"
generated: true
confidence: {confidence:.2f}
sources: {citations}
---

# Réponse à: {query}

{answer}

---
*Généré automatiquement le {datetime.now().isoformat()}*
"""
            
            # Sauvegarder
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Mettre à jour l'index
            await self.wiki_engine.update_index()
            
            logger.info(f"Réponse sauvegardée: {save_path}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde réponse: {str(e)}", exc_info=True)
    
    async def get_embeddings(
        self,
        text: str,
    ) -> List[float]:
        """
        Générer des embeddings pour un texte via mistral-embed.
        
        Args:
            text: Texte à embedder.
            
        Returns:
            Liste de floats (embedding).
        """
        try:
            payload = {
                "model": self.embedding_model,
                "inputs": [text],
            }
            
            response = await self.client.post(
                "/embeddings",
                json=payload,
            )
            
            if response.status_code != 200:
                logger.error(f"Erreur embeddings: {response.status_code} - {response.text}")
                return []
            
            result = response.json()
            embeddings = result.get("data", [{}])[0].get("embedding", [])
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Erreur embeddings: {str(e)}", exc_info=True)
            return []
    
    async def close(self) -> None:
        """Fermer les ressources."""
        await self.client.aclose()
        self.wiki_engine.close()
        self.vault_manager.close()
