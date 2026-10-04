"""
Parser de base pour les sources.

Ce module contient la classe BaseParser qui définit l'interface
pour tous les parsers de sources.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional
import re


class BaseParser(ABC):
    """
    Parser de base pour les sources.
    
    Cette classe abstraite définit l'interface que tous les parsers de sources
    doivent implémenter.
    """
    
    @abstractmethod
    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parser une source.
        
        Args:
            file_path: Chemin vers la source à parser.
            
        Returns:
            Dictionnaire avec les données parsées.
        """
        pass
    
    def _clean_text(self, text: str) -> str:
        """
        Nettoyer le texte.
        
        Args:
            text: Texte à nettoyer.
            
        Returns:
            Texte nettoyé.
        """
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Normaliser les sauts de ligne
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Supprimer les espaces en début et fin
        text = text.strip()
        
        return text
    
    def _extract_metadata_from_content(self, content: str) -> Dict[str, Any]:
        """
        Extraire les métadonnées du contenu.
        
        Args:
            content: Contenu à analyser.
            
        Returns:
            Dictionnaire avec les métadonnées extraites.
        """
        metadata = {}
        
        # Extraire le titre (première ligne non vide)
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                metadata['title'] = line
                break
        
        # Extraire les auteurs (recherche de patterns courants)
        author_patterns = [
            r'Author[s]?:?\s*(.+)',
            r'By\s+(.+)',
            r'Written by\s+(.+)',
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                authors = match.group(1).strip()
                metadata['authors'] = [a.strip() for a in authors.split(',') if a.strip()]
                break
        
        # Extraire la date (recherche de patterns de date)
        date_patterns = [
            r'Date:\s*(\d{4}-\d{2}-\d{2})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                metadata['date'] = match.group(1).strip()
                break
        
        return metadata
    
    def _extract_summary(self, content: str, max_length: int = 500) -> str:
        """
        Extraire un résumé du contenu.
        
        Args:
            content: Contenu à résumer.
            max_length: Longueur maximale du résumé.
            
        Returns:
            Résumé extrait.
        """
        # Simple extraction des premiers paragraphes
        paragraphs = content.split('\n\n')
        summary_parts = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                summary_parts.append(paragraph)
                if len(' '.join(summary_parts)) > max_length:
                    break
        
        summary = ' '.join(summary_parts)
        
        # Tronquer si nécessaire
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary
