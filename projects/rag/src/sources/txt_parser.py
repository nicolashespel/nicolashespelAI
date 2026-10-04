"""
Parser pour les fichiers texte brut.

Ce module contient la classe TextParser qui parse les fichiers .txt.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict

from .base_parser import BaseParser


class TextParser(BaseParser):
    """
    Parser pour les fichiers texte brut.
    """
    
    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parser un fichier texte.
        
        Args:
            file_path: Chemin vers le fichier texte.
            
        Returns:
            Dictionnaire avec les données parsées.
        """
        try:
            # Lire le fichier
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Nettoyer le contenu
            clean_content = self._clean_text(content)
            
            # Extraire les métadonnées
            metadata = self._extract_metadata_from_content(clean_content)
            
            # Extraire le résumé
            summary = self._extract_summary(clean_content)
            
            # Retourner les données parsées
            return {
                'type': 'text',
                'content': clean_content,
                'title': metadata.get('title', file_path.stem),
                'authors': metadata.get('authors', []),
                'date': metadata.get('date'),
                'summary': summary,
                'url': None,
                'doi': None,
            }
            
        except Exception as e:
            return {
                'type': 'text',
                'content': '',
                'title': file_path.stem,
                'authors': [],
                'date': None,
                'summary': '',
                'url': None,
                'doi': None,
                'error': str(e),
            }
