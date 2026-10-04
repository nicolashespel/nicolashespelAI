"""
Retriever BM25 pour le système RAG Wiki.

Ce module contient la classe BM25Retriever qui implémente la recherche
BM25 sur les pages du vault.
"""

import asyncio
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import re

from .base_retriever import BaseRetriever
from ..indexes import IndexManager
from ..storage import VaultManager


class BM25Retriever(BaseRetriever):
    """
    Retriever BM25 pour le système RAG Wiki.
    
    Ce retriever implémente l'algorithme BM25 pour la recherche textuelle
    dans les pages du vault.
    """
    
    def __init__(
        self,
        vault_path: Path,
        index_manager: IndexManager,
    ) -> None:
        """
        Initialiser le BM25Retriever.
        
        Args:
            vault_path: Chemin du vault.
            index_manager: Gestionnaire des index.
        """
        super().__init__(vault_path, index_manager)
        
        # Paramètres BM25
        self.k1 = 1.5
        self.b = 0.75
        
        # Index inversé
        self._inverted_index: Dict[str, Dict[str, int]] = defaultdict(dict)
        self._doc_lengths: Dict[str, int] = {}
        self._doc_counts: Dict[str, int] = defaultdict(int)
        self._total_docs = 0
        self._avg_doc_length = 0
        
        # Cache
        self._cache: Dict[str, List[Tuple[Path, float]]] = {}
        
        # Initialiser
        self.update_index()
    
    def update_index(self) -> None:
        """Mettre à jour l'index BM25."""
        # Obtenir toutes les pages
        vault_manager = VaultManager(self.vault_path)
        all_pages = vault_manager.get_all_pages()
        
        # Réinitialiser les structures
        self._inverted_index = defaultdict(dict)
        self._doc_lengths = {}
        self._doc_counts = defaultdict(int)
        self._total_docs = len(all_pages)
        
        # Calculer la longueur moyenne des documents
        total_length = 0
        for page_path in all_pages:
            content = vault_manager.read_page_content(page_path)
            if content:
                tokens = self._tokenize(content)
                doc_length = len(tokens)
                self._doc_lengths[str(page_path)] = doc_length
                total_length += doc_length
        
        self._avg_doc_length = total_length / self._total_docs if self._total_docs > 0 else 0
        
        # Construire l'index inversé
        for page_path in all_pages:
            content = vault_manager.read_page_content(page_path)
            if content:
                tokens = self._tokenize(content)
                term_frequencies = self._calculate_term_frequencies(tokens)
                
                for term, freq in term_frequencies.items():
                    self._inverted_index[term][str(page_path)] = freq
                    self._doc_counts[term] += 1
        
        self.initialize()
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenizer le texte.
        
        Args:
            text: Texte à tokenizer.
            
        Returns:
            Liste de tokens.
        """
        # Convertir en minuscules
        text = text.lower()
        
        # Supprimer les caractères spéciaux (sauf les alphanumériques et espaces)
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Tokenizer par espaces
        tokens = text.split()
        
        # Filtrer les tokens vides
        tokens = [token for token in tokens if token.strip()]
        
        return tokens
    
    def _calculate_term_frequencies(self, tokens: List[str]) -> Dict[str, int]:
        """
        Calculer les fréquences des termes.
        
        Args:
            tokens: Liste de tokens.
            
        Returns:
            Dictionnaire avec les fréquences.
        """
        frequencies = defaultdict(int)
        for token in tokens:
            frequencies[token] += 1
        return dict(frequencies)
    
    def _calculate_idf(self, term: str) -> float:
        """
        Calculer l'IDF (Inverse Document Frequency).
        
        Args:
            term: Terme.
            
        Returns:
            IDF.
        """
        if self._total_docs == 0:
            return 0.0
        
        doc_count = self._doc_counts.get(term, 0)
        if doc_count == 0:
            return 0.0
        
        return math.log((self._total_docs - doc_count + 0.5) / (doc_count + 0.5) + 1)
    
    def _calculate_bm25_score(
        self,
        query_terms: List[str],
        doc_path: str,
    ) -> float:
        """
        Calculer le score BM25 pour un document.
        
        Args:
            query_terms: Liste des termes de la requête.
            doc_path: Chemin du document.
            
        Returns:
            Score BM25.
        """
        score = 0.0
        doc_length = self._doc_lengths.get(doc_path, 0)
        
        for term in query_terms:
            if term not in self._inverted_index:
                continue
            
            if doc_path not in self._inverted_index[term]:
                continue
            
            # Fréquence du terme dans le document
            tf = self._inverted_index[term][doc_path]
            
            # IDF
            idf = self._calculate_idf(term)
            
            # Calculer la partie BM25
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self._avg_doc_length))
            
            if denominator > 0:
                score += idf * (numerator / denominator)
        
        return score
    
    async def search(
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
        # Vérifier le cache
        cache_key = f"{query}:{k}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Tokenizer la requête
        query_terms = self._tokenize(query)
        
        # Calculer les scores pour tous les documents
        scores: Dict[str, float] = {}
        for doc_path in self._doc_lengths.keys():
            scores[doc_path] = self._calculate_bm25_score(query_terms, doc_path)
        
        # Trier par score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Convertir en liste de tuples Path, float
        results = [(Path(doc_path), score) for doc_path, score in sorted_scores[:k]]
        
        # Mettre en cache
        self._cache[cache_key] = results
        
        return results
    
    def clear_cache(self) -> None:
        """Effacer le cache."""
        self._cache = {}
    
    def get_inverted_index_info(self) -> Dict[str, Any]:
        """
        Obtenir des informations sur l'index inversé.
        
        Returns:
            Dictionnaire avec les informations.
        """
        return {
            "total_terms": len(self._inverted_index),
            "total_documents": self._total_docs,
            "avg_doc_length": self._avg_doc_length,
        }
    
    def close(self) -> None:
        """Fermer les ressources du BM25Retriever."""
        self.clear_cache()
        self._initialized = False
