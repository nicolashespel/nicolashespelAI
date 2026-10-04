"""
Pipeline de requête pour le système RAG Wiki.

Ce module contient la classe QueryPipeline qui gère le processus complet
de requête sur le vault.
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..types import (
    QueryResult,
    Page,
)
from ..storage import VaultManager
from ..retrieval import RetrievalService
from ..indexes import IndexManager
from .config import WikiConfig
from .prompts import WIKI_LIBRARIAN_PROMPT


class QueryPipeline:
    """
    Pipeline de requête pour le système RAG Wiki.
    
    Ce pipeline gère le processus complet de requête :
    1. Compréhension de la requête
    2. Recherche en couches (index -> BM25 -> embeddings)
    3. Sélection des pages pertinentes
    4. Synthèse de la réponse
    5. Génération de la réponse avec citations
    """
    
    def __init__(
        self,
        vault_manager: VaultManager,
        retrieval_service: RetrievalService,
        config: WikiConfig,
    ) -> None:
        """
        Initialiser le pipeline de requête.
        
        Args:
            vault_manager: Gestionnaire du vault.
            retrieval_service: Service de récupération.
            config: Configuration du wiki.
        """
        self.vault_manager = vault_manager
        self.retrieval_service = retrieval_service
        self.config = config
    
    async def query(
        self,
        query_text: str,
        use_index: bool = True,
        use_bm25: bool = True,
        use_embeddings: bool = True,
    ) -> QueryResult:
        """
        Effectuer une requête sur le vault.
        
        Args:
            query_text: Texte de la requête.
            use_index: Utiliser la recherche dans l'index.
            use_bm25: Utiliser la recherche BM25.
            use_embeddings: Utiliser la recherche par embeddings.
            
        Returns:
            Résultat de la requête.
        """
        start_time = time.time()
        
        try:
            # Étape 1: Comprendre la requête
            query_info = self._analyze_query(query_text)
            
            # Étape 2: Recherche en couches
            relevant_pages = await self._layered_retrieval(
                query_text=query_text,
                query_info=query_info,
                use_index=use_index,
                use_bm25=use_bm25,
                use_embeddings=use_embeddings,
            )
            
            if not relevant_pages:
                return QueryResult(
                    success=True,
                    query=query_text,
                    answer="Aucune information trouvée dans le vault pour cette requête.",
                    cited_pages=[],
                    duration_seconds=time.time() - start_time,
                )
            
            # Étape 3: Synthétiser la réponse
            answer, cited_pages = await self._synthesize_answer(
                query_text=query_text,
                relevant_pages=relevant_pages,
            )
            
            return QueryResult(
                success=True,
                query=query_text,
                answer=answer,
                cited_pages=cited_pages,
                duration_seconds=time.time() - start_time,
            )
            
        except Exception as e:
            return QueryResult(
                success=False,
                query=query_text,
                answer="",
                duration_seconds=time.time() - start_time,
                error=str(e),
            )
    
    def _analyze_query(self, query_text: str) -> Dict[str, Any]:
        """
        Analyser la requête pour en extraire les informations clés.
        
        Args:
            query_text: Texte de la requête.
            
        Returns:
            Dictionnaire avec les informations d'analyse.
        """
        query_info = {
            "original_query": query_text,
            "normalized_query": query_text.lower().strip(),
            "keywords": self._extract_keywords(query_text),
            "query_type": self._determine_query_type(query_text),
            "intent": self._determine_intent(query_text),
        }
        
        return query_info
    
    def _extract_keywords(self, query_text: str) -> List[str]:
        """
        Extraire les mots-clés de la requête.
        
        Args:
            query_text: Texte de la requête.
            
        Returns:
            Liste de mots-clés.
        """
        import re
        
        # Supprimer les mots vides
        stop_words = {
            "le", "la", "les", "un", "une", "des", "de", "du", "de", "l", "d",
            "a", "an", "the", "is", "are", "was", "were", "been", "be",
            "to", "of", "and", "or", "in", "on", "at", "for", "with", "by",
            "what", "why", "when", "where", "who", "how", "which", "that",
            "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
        }
        
        # Tokenizer simple
        words = re.findall(r'\b\w+\b', query_text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return list(set(keywords))
    
    def _determine_query_type(self, query_text: str) -> str:
        """
        Déterminer le type de la requête.
        
        Args:
            query_text: Texte de la requête.
            
        Returns:
            Type de requête.
        """
        query_lower = query_text.lower()
        
        if any(word in query_lower for word in ["quoi", "qu'est-ce que", "what is", "define"]):
            return "definition"
        elif any(word in query_lower for word in ["pourquoi", "why", "raison"]):
            return "explanation"
        elif any(word in query_lower for word in ["comment", "how to", "comment faire"]):
            return "procedural"
        elif any(word in query_lower for word in ["quand", "when", "date"]):
            return "temporal"
        elif any(word in query_lower for word in ["qui", "who", "personne"]):
            return "entity"
        elif any(word in query_lower for word in ["comparer", "vs", "comparaison", "compare"]):
            return "comparison"
        elif any(word in query_lower for word in ["liste", "list", "tous", "all"]):
            return "listing"
        else:
            return "general"
    
    def _determine_intent(self, query_text: str) -> str:
        """
        Déterminer l'intention de la requête.
        
        Args:
            query_text: Texte de la requête.
            
        Returns:
            Intention de la requête.
        """
        query_lower = query_text.lower()
        
        if any(word in query_lower for word in ["apprendre", "comprendre", "learn", "understand"]):
            return "learning"
        elif any(word in query_lower for word in ["trouver", "find", "localiser"]):
            return "finding"
        elif any(word in query_lower for word in ["vérifier", "check", "confirmer"]):
            return "verification"
        elif any(word in query_lower for word in ["résumer", "summarize", "résumé"]):
            return "summarization"
        elif any(word in query_lower for word in ["analyser", "analyze", "analyse"]):
            return "analysis"
        else:
            return "general"
    
    async def _layered_retrieval(
        self,
        query_text: str,
        query_info: Dict[str, Any],
        use_index: bool,
        use_bm25: bool,
        use_embeddings: bool,
    ) -> List[Page]:
        """
        Effectuer une recherche en couches.
        
        Args:
            query_text: Texte de la requête.
            query_info: Informations d'analyse de la requête.
            use_index: Utiliser la recherche dans l'index.
            use_bm25: Utiliser la recherche BM25.
            use_embeddings: Utiliser la recherche par embeddings.
            
        Returns:
            Liste des pages pertinentes.
        """
        relevant_pages: List[Page] = []
        page_scores: Dict[str, float] = {}
        
        # Étape 1: Recherche dans l'index
        if use_index:
            index_results = self._search_index(query_info)
            for page_path, score in index_results:
                page_scores[str(page_path)] = score
        
        # Étape 2: Recherche BM25
        if use_bm25:
            bm25_results = await self.retrieval_service.bm25_search(
                query_text=query_text,
                k=self.config.bm25_k,
            )
            for page_path, score in bm25_results:
                if str(page_path) in page_scores:
                    page_scores[str(page_path)] += score * 0.8  # Poids pour BM25
                else:
                    page_scores[str(page_path)] = score * 0.8
        
        # Étape 3: Recherche par embeddings
        if use_embeddings:
            embedding_results = await self.retrieval_service.embedding_search(
                query_text=query_text,
                k=self.config.embedding_k,
            )
            for page_path, score in embedding_results:
                if str(page_path) in page_scores:
                    page_scores[str(page_path)] += score * 1.2  # Poids pour embeddings
                else:
                    page_scores[str(page_path)] = score * 1.2
        
        # Sélectionner les pages les mieux notées
        sorted_pages = sorted(page_scores.items(), key=lambda x: x[1], reverse=True)
        top_page_paths = [Path(path) for path, _ in sorted_pages[:self.config.rrf_k]]
        
        # Charger les pages
        for page_path in top_page_paths:
            page = self.vault_manager.get_page(page_path)
            if page:
                relevant_pages.append(page)
        
        return relevant_pages
    
    def _search_index(self, query_info: Dict[str, Any]) -> List[Tuple[Path, float]]:
        """
        Rechercher dans l'index.
        
        Args:
            query_info: Informations d'analyse de la requête.
            
        Returns:
            Liste de tuples (chemin, score).
        """
        results = []
        
        # Rechercher par mots-clés
        for keyword in query_info["keywords"]:
            # Rechercher dans l'index par tag
            pages_with_tag = self.vault_manager.get_pages_by_tag(keyword)
            for page_path in pages_with_tag:
                results.append((page_path, 1.0))
        
        # Rechercher par type
        if query_info["query_type"] == "entity":
            pages = self.vault_manager.get_pages_by_type("entity")
            for page_path in pages:
                results.append((page_path, 0.8))
        elif query_info["query_type"] == "definition":
            pages = self.vault_manager.get_pages_by_type("concept")
            for page_path in pages:
                results.append((page_path, 0.9))
        
        # Supprimer les doublons
        seen = set()
        unique_results = []
        for path, score in results:
            if str(path) not in seen:
                seen.add(str(path))
                unique_results.append((path, score))
        
        return unique_results
    
    async def _synthesize_answer(
        self,
        query_text: str,
        relevant_pages: List[Page],
    ) -> Tuple[str, List[str]]:
        """
        Synthétiser une réponse à partir des pages pertinentes.
        
        Args:
            query_text: Texte de la requête.
            relevant_pages: Pages pertinentes.
            
        Returns:
            Tuple avec (réponse, pages citées).
        """
        cited_pages = []
        
        # Simple synthesis pour l'instant
        # Dans une implémentation complète, cela utiliserait le LLM
        answer_parts = []
        
        for page in relevant_pages:
            # Extraire les informations pertinentes
            page_info = self._extract_relevant_info(page, query_text)
            if page_info:
                answer_parts.append(page_info)
                cited_pages.append(page.name)
        
        if not answer_parts:
            return "Aucune information pertinente trouvée.", []
        
        # Construire la réponse
        answer = "\n\n".join(answer_parts)
        
        # Ajouter les citations
        if cited_pages:
            answer += f"\n\n**Sources :**\n"
            for page_name in cited_pages:
                answer += f"- [[{page_name}]]\n"
        
        # Offrir de sauvegarder
        answer += "\n\n**Souhaitez-vous sauvegarder cette réponse comme une nouvelle page ?** (Oui/Non)"
        
        return answer, cited_pages
    
    def _extract_relevant_info(self, page: Page, query_text: str) -> Optional[str]:
        """
        Extraire les informations pertinentes d'une page.
        
        Args:
            page: Page à analyser.
            query_text: Texte de la requête.
            
        Returns:
            Informations pertinentes ou None.
        """
        # Simple extraction pour l'instant
        # Dans une implémentation complète, cela utiliserait une analyse sémantique
        
        query_lower = query_text.lower()
        
        # Vérifier si la page contient des mots-clés de la requête
        content_lower = page.description.lower()
        for keyword in query_lower.split():
            if len(keyword) > 3 and keyword in content_lower:
                return f"## {page.name}\n\n{page.description}"
        
        return None
    
    async def close(self) -> None:
        """Fermer les ressources du pipeline."""
        pass
