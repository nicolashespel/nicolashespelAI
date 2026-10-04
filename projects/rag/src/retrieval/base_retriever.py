"""
Classe de base pour les retrievers.

Ce module contient la classe BaseRetriever qui définit l'interface
pour tous les retrievers.
"""

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..indexes import IndexManager


class BaseRetriever(ABC):
    """
    Classe de base pour les retrievers.
    
    Cette classe abstraite définit l'interface que tous les retrievers doivent implémenter.
    """
    
    def __init__(
        self,
        vault_path: Path,
        index_manager: IndexManager,
    ) -> None:
        """
        Initialiser le BaseRetriever.
        
        Args:
            vault_path: Chemin du vault.
            index_manager: Gestionnaire des index.
        """
        self.vault_path = vault_path
        self.index_manager = index_manager
        self._initialized = False
    
    @abstractmethod
    async def search(
        self,
        query: str,
        k: int = 10,
    ) -> List[Tuple[Path, float]]:
        """
        Effectuer une recherche.
        
        Args:
            query: Requête de recherche.
            k: Nombre de résultats.
            
        Returns:
            Liste de tuples (chemin, score).
        """
        pass
    
    @abstractmethod
    def update_index(self) -> None:
        """Mettre à jour l'index."""
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """Effacer le cache."""
        pass
    
    def is_initialized(self) -> bool:
        """
        Vérifier si le retriever est initialisé.
        
        Returns:
            True si initialisé.
        """
        return self._initialized
    
    def initialize(self) -> None:
        """
        Initialiser le retriever.
        """
        self._initialized = True
    
    def close(self) -> None:
        """Fermer les ressources du retriever."""
        self._initialized = False
