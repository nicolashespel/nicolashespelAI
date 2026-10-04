"""
Parser pour les fichiers Markdown.

Ce module contient la classe MarkdownParser qui parse les fichiers .md.
"""

import asyncio
import re
from pathlib import Path
from typing import Any, Dict
import yaml

from .base_parser import BaseParser


class MarkdownParser(BaseParser):
    """
    Parser pour les fichiers Markdown.
    """
    
    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parser un fichier Markdown.
        
        Args:
            file_path: Chemin vers le fichier Markdown.
            
        Returns:
            Dictionnaire avec les données parsées.
        """
        try:
            # Lire le fichier
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Nettoyer le contenu
            clean_content = self._clean_text(content)
            
            # Extraire le frontmatter si présent
            frontmatter = self._extract_frontmatter(clean_content)
            
            # Extraire le contenu principal (sans frontmatter)
            main_content = self._extract_main_content(clean_content)
            
            # Extraire les métadonnées
            if frontmatter:
                metadata = frontmatter
            else:
                metadata = self._extract_metadata_from_content(main_content)
            
            # Extraire le résumé
            summary = self._extract_summary(main_content)
            
            # Retourner les données parsées
            return {
                'type': 'markdown',
                'content': main_content,
                'title': metadata.get('title', file_path.stem),
                'authors': metadata.get('authors', []),
                'date': metadata.get('date'),
                'summary': summary,
                'url': metadata.get('url'),
                'doi': metadata.get('doi'),
            }
            
        except Exception as e:
            return {
                'type': 'markdown',
                'content': '',
                'title': file_path.stem,
                'authors': [],
                'date': None,
                'summary': '',
                'url': None,
                'doi': None,
                'error': str(e),
            }
    
    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """
        Extraire le frontmatter YAML.
        
        Args:
            content: Contenu du fichier.
            
        Returns:
            Dictionnaire avec le frontmatter ou vide.
        """
        # Pattern pour le frontmatter
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            try:
                frontmatter_str = match.group(1)
                return yaml.safe_load(frontmatter_str)
            except Exception:
                return {}
        
        return {}
    
    def _extract_main_content(self, content: str) -> str:
        """
        Extraire le contenu principal (sans frontmatter).
        
        Args:
            content: Contenu du fichier.
            
        Returns:
            Contenu principal.
        """
        # Pattern pour le frontmatter
        pattern = r'^---\s*\n.*?\n---\s*\n'
        main_content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        # Nettoyer
        main_content = main_content.strip()
        
        return main_content
