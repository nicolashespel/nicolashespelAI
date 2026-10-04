"""
Constructeur d'index pour le système RAG Wiki.

Ce module contient la classe IndexBuilder qui construit l'index
à partir des pages du vault.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import re

from ..storage import VaultManager
from ..types import IndexPage, Page


class IndexBuilder:
    """
    Constructeur d'index pour le système RAG Wiki.
    
    Cette classe construit l'index en analysant toutes les pages du vault
    et en extrayant les métadonnées nécessaires.
    """
    
    def __init__(self, vault_path: Path) -> None:
        """
        Initialiser l'IndexBuilder.
        
        Args:
            vault_path: Chemin du vault.
        """
        self.vault_path = vault_path
        self.vault_manager = VaultManager(vault_path)
    
    def build_index(self) -> IndexPage:
        """
        Construire l'index.
        
        Returns:
            Page d'index construite.
        """
        # Obtenir toutes les pages
        all_pages = self.vault_manager.get_all_pages()
        
        # Initialiser les structures
        pages_by_type: Dict[str, List[str]] = {}
        pages_by_tag: Dict[str, List[str]] = {}
        pages_by_date: Dict[str, List[str]] = {}
        
        # Statistiques
        statistics: Dict[str, Any] = {
            "total_pages": len(all_pages),
            "entities": 0,
            "concepts": 0,
            "sources": 0,
            "comparisons": 0,
            "syntheses": 0,
            "total_size": 0,
        }
        
        # Traiter chaque page
        for page_path in all_pages:
            page = self.vault_manager.get_page(page_path)
            if page is None:
                continue
            
            # Obtenir le nom de la page (sans extension)
            page_name = page_path.stem
            
            # Ajouter à pages_by_type
            page_type = page.type
            if page_type not in pages_by_type:
                pages_by_type[page_type] = []
            pages_by_type[page_type].append(page_name)
            
            # Mettre à jour les statistiques
            if page_type in statistics:
                statistics[page_type] += 1
            
            # Ajouter à pages_by_tag
            for tag in page.tags:
                if tag not in pages_by_tag:
                    pages_by_tag[tag] = []
                pages_by_tag[tag].append(page_name)
            
            # Ajouter à pages_by_date
            if hasattr(page, 'updated') and page.updated:
                date_str = page.updated.strftime('%Y-%m-%d')
                if date_str not in pages_by_date:
                    pages_by_date[date_str] = []
                pages_by_date[date_str].append(page_name)
            elif hasattr(page, 'created') and page.created:
                date_str = page.created.strftime('%Y-%m-%d')
                if date_str not in pages_by_date:
                    pages_by_date[date_str] = []
                pages_by_date[date_str].append(page_name)
            
            # Calculer la taille totale
            if page_path.exists():
                statistics["total_size"] += page_path.stat().st_size
        
        # Trier les listes
        for key in pages_by_type:
            pages_by_type[key].sort()
        for key in pages_by_tag:
            pages_by_tag[key].sort()
        for key in pages_by_date:
            pages_by_date[key].sort()
        
        # Créer la page d'index
        index_page = IndexPage(
            type="index",
            name="Vault Index",
            description="Catalogue complet du vault",
            generated=datetime.now(),
            version="1.0.0",
            statistics=statistics,
            pages_by_type=pages_by_type,
            pages_by_tag=pages_by_tag,
            pages_by_date=pages_by_date,
        )
        
        return index_page
    
    def _extract_page_type(self, page_path: Path) -> str:
        """
        Extraire le type de page à partir du chemin.
        
        Args:
            page_path: Chemin de la page.
            
        Returns:
            Type de page.
        """
        relative_path = page_path.relative_to(self.vault_path / "wiki")
        parts = relative_path.parts
        
        if len(parts) >= 2:
            if parts[0] == "entities":
                return "entity"
            elif parts[0] == "concepts":
                return "concept"
            elif parts[0] == "sources":
                return "source"
            elif parts[0] == "comparisons":
                return "comparison"
            elif parts[0] == "synthesis":
                return "synthesis"
        
        # Par défaut
        if page_path.name == "index.md":
            return "index"
        elif page_path.name == "log.md":
            return "log"
        
        return "unknown"
    
    def _extract_tags_from_content(self, content: str) -> List[str]:
        """
        Extraire les tags du contenu.
        
        Args:
            content: Contenu de la page.
            
        Returns:
            Liste de tags.
        """
        tags = []
        
        # Extraire du frontmatter
        frontmatter_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            tags_match = re.search(r'tags:\s*\[?(.*?)\]?', frontmatter, re.DOTALL)
            if tags_match:
                tags_str = tags_match.group(1)
                tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        
        return tags
    
    def close(self) -> None:
        """Fermer les ressources de l'IndexBuilder."""
        self.vault_manager.close()
