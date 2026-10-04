"""
Parser pour les fichiers HTML.

Ce module contient la classe HTMLParser qui parse les fichiers .html.
"""

import asyncio
import re
from pathlib import Path
from typing import Any, Dict
from bs4 import BeautifulSoup

from .base_parser import BaseParser


class HTMLParser(BaseParser):
    """
    Parser pour les fichiers HTML.
    """
    
    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parser un fichier HTML.
        
        Args:
            file_path: Chemin vers le fichier HTML.
            
        Returns:
            Dictionnaire avec les données parsées.
        """
        try:
            # Lire le fichier
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parser avec BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extraire le titre
            title = soup.title.string if soup.title else file_path.stem
            
            # Extraire les métadonnées
            metadata = self._extract_html_metadata(soup)
            
            # Extraire le contenu principal
            main_content = self._extract_main_content(soup)
            
            # Nettoyer le contenu
            clean_content = self._clean_text(main_content)
            
            # Extraire le résumé
            summary = self._extract_summary(clean_content)
            
            # Retourner les données parsées
            return {
                'type': 'html',
                'content': clean_content,
                'title': metadata.get('title', title),
                'authors': metadata.get('authors', []),
                'date': metadata.get('date'),
                'summary': summary,
                'url': metadata.get('url'),
                'doi': metadata.get('doi'),
            }
            
        except Exception as e:
            # Essayer sans BeautifulSoup
            try:
                # Extraire le texte brut
                text = re.sub(r'<[^>]+>', ' ', html_content)
                clean_text = self._clean_text(text)
                
                return {
                    'type': 'html',
                    'content': clean_text,
                    'title': file_path.stem,
                    'authors': [],
                    'date': None,
                    'summary': self._extract_summary(clean_text),
                    'url': None,
                    'doi': None,
                    'error': f"BeautifulSoup non disponible: {str(e)}",
                }
            except Exception:
                return {
                    'type': 'html',
                    'content': '',
                    'title': file_path.stem,
                    'authors': [],
                    'date': None,
                    'summary': '',
                    'url': None,
                    'doi': None,
                    'error': str(e),
                }
    
    def _extract_html_metadata(self, soup) -> Dict[str, Any]:
        """
        Extraire les métadonnées d'une page HTML.
        
        Args:
            soup: Objet BeautifulSoup.
            
        Returns:
            Dictionnaire avec les métadonnées.
        """
        metadata = {}
        
        # Extraire le titre
        if soup.title:
            metadata['title'] = soup.title.string
        
        # Extraire les méta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            if tag.get('name') or tag.get('property'):
                name = tag.get('name') or tag.get('property')
                content = tag.get('content')
                if name and content:
                    metadata[name.lower()] = content
        
        # Extraire les auteurs
        author_patterns = [
            r'Author[s]?:?\s*(.+)',
            r'By\s+(.+)',
            r'Written by\s+(.+)',
        ]
        
        text_content = soup.get_text()
        for pattern in author_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                authors = match.group(1).strip()
                metadata['authors'] = [a.strip() for a in authors.split(',') if a.strip()]
                break
        
        # Extraire la date
        date_patterns = [
            r'Date:\s*(\d{4}-\d{2}-\d{2})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text_content)
            if match:
                metadata['date'] = match.group(1).strip()
                break
        
        return metadata
    
    def _extract_main_content(self, soup) -> str:
        """
        Extraire le contenu principal d'une page HTML.
        
        Args:
            soup: Objet BeautifulSoup.
            
        Returns:
            Contenu principal.
        """
        # Essayer de trouver l'article ou le contenu principal
        article = soup.find('article')
        if article:
            return article.get_text()
        
        # Essayer main
        main = soup.find('main')
        if main:
            return main.get_text()
        
        # Essayer body
        body = soup.find('body')
        if body:
            return body.get_text()
        
        # Retourner tout le texte
        return soup.get_text()
