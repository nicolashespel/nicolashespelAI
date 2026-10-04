"""
Classe de base pour les agents du système RAG Wiki.

Ce module contient la classe BaseAgent qui définit l'interface
de base pour tous les agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path

from ..core.config import WikiConfig
from ..storage import VaultManager
from ..core.prompts import WIKI_INGESTOR_PROMPT, WIKI_LIBRARIAN_PROMPT, WIKI_LINTER_PROMPT


class BaseAgent(ABC):
    """
    Classe de base pour les agents du système RAG Wiki.
    
    Cette classe abstraite définit l'interface que tous les agents doivent implémenter.
    """
    
    def __init__(
        self,
        name: str,
        role: str,
        vault_manager: VaultManager,
        config: WikiConfig,
    ) -> None:
        """
        Initialiser le BaseAgent.
        
        Args:
            name: Nom de l'agent.
            role: Rôle de l'agent.
            vault_manager: Gestionnaire du vault.
            config: Configuration du wiki.
        """
        self.name = name
        self.role = role
        self.vault_manager = vault_manager
        self.config = config
        
        # Définir le prompt système
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """
        Obtenir le prompt système pour l'agent.
        
        Returns:
            Prompt système.
        """
        prompt_map = {
            "wiki_ingestor": WIKI_INGESTOR_PROMPT,
            "wiki_librarian": WIKI_LIBRARIAN_PROMPT,
            "wiki_linter": WIKI_LINTER_PROMPT,
        }
        
        return prompt_map.get(self.name.lower(), "")
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """
        Exécuter la tâche principale de l'agent.
        
        Args:
            *args: Arguments positionnels.
            **kwargs: Arguments nommés.
            
        Returns:
            Résultat de l'exécution.
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        Obtenir les informations sur l'agent.
        
        Returns:
            Dictionnaire avec les informations.
        """
        return {
            "name": self.name,
            "role": self.role,
            "vault_path": str(self.vault_manager.vault_path),
        }
    
    def close(self) -> None:
        """Fermer les ressources de l'agent."""
        pass
