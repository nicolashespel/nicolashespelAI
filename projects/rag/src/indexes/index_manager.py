"""
Gestionnaire des index pour le système RAG Wiki.

Ce module contient la classe IndexManager qui gère tous les index
du vault.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..storage import VaultManager
from ..types import IndexPage
from .index_builder import IndexBuilder


class IndexManager:
    """
    Gestionnaire des index pour le système RAG Wiki.
    
    Cette classe gère la construction, la mise à jour et l'accès
    à tous les index du vault.
    """
    
    def __init__(self, vault_path: Path) -> None:
        """
        Initialiser l'IndexManager.
        
        Args:
            vault_path: Chemin du vault.
        """
        self.vault_path = vault_path
        self.vault_manager = VaultManager(vault_path)
        self.index_builder = IndexBuilder(vault_path)
        
        # Chemin du fichier d'index
        self._index_path = vault_path / "wiki" / "index.md"
        
        # Index en mémoire
        self._index: Optional[IndexPage] = None
    
    def initialize_index(self) -> None:
        """
        Initialiser l'index.
        """
        # Construire l'index
        self.update_index()
    
    def update_index(self) -> None:
        """
        Mettre à jour l'index.
        """
        # Construire l'index
        index_page = self.index_builder.build_index()
        
        # Sauvegarder l'index
        self._save_index(index_page)
        
        # Charger en mémoire
        self._index = index_page
    
    def _save_index(self, index_page: IndexPage) -> None:
        """
        Sauvegarder l'index.
        
        Args:
            index_page: Page d'index.
        """
        # Convertir en markdown
        content = self._index_page_to_markdown(index_page)
        
        # Sauvegarder
        self.vault_manager.save_page(self._index_path, content)
    
    def _index_page_to_markdown(self, index_page: IndexPage) -> str:
        """
        Convertir une page d'index en markdown.
        
        Args:
            index_page: Page d'index.
            
        Returns:
            Contenu markdown.
        """
        # Générer le frontmatter
        frontmatter_lines = [
            "---",
            f"type: {index_page.type}",
            f"name: {index_page.name}",
            f"description: {index_page.description}",
            f"generated: {index_page.generated.isoformat()}",
            f"version: {index_page.version}",
            "---",
        ]
        
        # Générer le contenu
        content_lines = [
            f"# {index_page.name}",
            "",
            "## Statistiques",
            f"- **Total pages :** {index_page.statistics.get('total_pages', 0)}",
            f"- **Entités :** {index_page.statistics.get('entities', 0)}",
            f"- **Concepts :** {index_page.statistics.get('concepts', 0)}",
            f"- **Sources :** {index_page.statistics.get('sources', 0)}",
            f"- **Comparaisons :** {index_page.statistics.get('comparisons', 0)}",
            f"- **Synthèses :** {index_page.statistics.get('syntheses', 0)}",
            f"- **Dernière mise à jour :** {index_page.generated.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Par Type",
        ]
        
        # Pages par type
        for page_type, pages in index_page.pages_by_type.items():
            content_lines.append(f"### {page_type.capitalize()} ({len(pages)})")
            for page in pages:
                content_lines.append(f"- [[{page}]]")
            content_lines.append("")
        
        # Pages par tag
        if index_page.pages_by_tag:
            content_lines.append("## Par Tag")
            for tag, pages in sorted(index_page.pages_by_tag.items()):
                content_lines.append(f"### {tag} ({len(pages)})")
                for page in pages:
                    content_lines.append(f"- [[{page}]]")
                content_lines.append("")
        
        # Pages par date
        if index_page.pages_by_date:
            content_lines.append("## Par Date")
            for date, pages in sorted(index_page.pages_by_date.items(), reverse=True):
                content_lines.append(f"### {date} ({len(pages)})")
                for page in pages:
                    content_lines.append(f"- [[{page}]]")
                content_lines.append("")
        
        content_lines.append("## Recherche")
        content_lines.append("Utilisez les commandes `/wiki-query` ou `/wiki-search` pour trouver du contenu.")
        
        return "\n".join(frontmatter_lines + content_lines)
    
    def get_index(self) -> Optional[IndexPage]:
        """
        Obtenir l'index.
        
        Returns:
            Page d'index ou None.
        """
        # Charger depuis la mémoire
        if self._index:
            return self._index
        
        # Charger depuis le fichier
        self._index = self.vault_manager.get_page(self._index_path)
        if self._index and isinstance(self._index, IndexPage):
            return self._index
        
        # Construire un nouvel index si le fichier n'existe pas
        self.update_index()
        return self._index
    
    def search_in_index(self, query: str) -> List[str]:
        """
        Rechercher dans l'index.
        
        Args:
            query: Requête de recherche.
            
        Returns:
            Liste de pages correspondantes.
        """
        index = self.get_index()
        if index is None:
            return []
        
        results = []
        
        # Rechercher dans les tags
        query_lower = query.lower()
        for tag, pages in index.pages_by_tag.items():
            if query_lower in tag.lower():
                results.extend(pages)
        
        # Rechercher dans les types
        for page_type, pages in index.pages_by_type.items():
            if query_lower in page_type.lower():
                results.extend(pages)
        
        # Rechercher dans les noms de pages
        for page_type, pages in index.pages_by_type.items():
            for page in pages:
                if query_lower in page.lower():
                    results.append(page)
        
        return list(set(results))
    
    def add_page_to_index(self, page_path: Path) -> None:
        """
        Ajouter une page à l'index.
        
        Args:
            page_path: Chemin de la page.
        """
        # Mettre à jour l'index
        self.update_index()
    
    def remove_page_from_index(self, page_path: Path) -> None:
        """
        Supprimer une page de l'index.
        
        Args:
            page_path: Chemin de la page.
        """
        # Mettre à jour l'index
        self.update_index()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtenir les statistiques de l'index.
        
        Returns:
            Dictionnaire avec les statistiques.
        """
        index = self.get_index()
        if index is None:
            return {}
        
        return index.statistics
    
    def close(self) -> None:
        """Fermer les ressources de l'IndexManager."""
        self.vault_manager.close()
        self.index_builder.close()
