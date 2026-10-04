"""
Parser pour les fichiers PDF.

Ce module contient la classe PDFParser qui parse les fichiers .pdf.
"""

import asyncio
import re
from pathlib import Path
from typing import Any, Dict

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

from .base_parser import BaseParser


class PDFParser(BaseParser):
    """
    Parser pour les fichiers PDF.
    """
    
    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parser un fichier PDF.
        
        Args:
            file_path: Chemin vers le fichier PDF.
            
        Returns:
            Dictionnaire avec les données parsées.
        """
        if HAS_PYPDF:
            return await self._parse_with_pypdf(file_path)
        else:
            return await self._parse_without_pypdf(file_path)
    
    async def _parse_with_pypdf(self, file_path: Path) -> Dict[str, Any]:
        """
        Parser avec PyPDF.
        
        Args:
            file_path: Chemin vers le fichier PDF.
            
        Returns:
            Dictionnaire avec les données parsées.
        """
        try:
            # Lire le PDF
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
            
            # Extraire le texte
            text_content = "\n".join([page.extract_text() for page in reader.pages])
            
            # Nettoyer le contenu
            clean_content = self._clean_text(text_content)
            
            # Extraire les métadonnées
            metadata = self._extract_pdf_metadata(reader)
            
            # Extraire le résumé
            summary = self._extract_summary(clean_content)
            
            # Retourner les données parsées
            return {
                'type': 'pdf',
                'content': clean_content,
                'title': metadata.get('title', file_path.stem),
                'authors': metadata.get('authors', []),
                'date': metadata.get('date'),
                'summary': summary,
                'url': metadata.get('url'),
                'doi': metadata.get('doi'),
            }
            
        except Exception as e:
            return {
                'type': 'pdf',
                'content': '',
                'title': file_path.stem,
                'authors': [],
                'date': None,
                'summary': '',
                'url': None,
                'doi': None,
                'error': str(e),
            }
    
    async def _parse_without_pypdf(self, file_path: Path) -> Dict[str, Any]:
        """
        Parser sans PyPDF (extraction basique).
        
        Args:
            file_path: Chemin vers le fichier PDF.
            
        Returns:
            Dictionnaire avec les données parsées.
        """
        try:
            # Lire le fichier en mode binaire
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Essayer d'extraire du texte brut
            text = content.decode('utf-8', errors='ignore')
            
            # Extraire les parties lisibles
            readable_parts = re.findall(r'[\x20-\x7E]{50,}', text)
            clean_content = ' '.join(readable_parts)
            
            # Nettoyer
            clean_content = self._clean_text(clean_content)
            
            # Extraire le résumé
            summary = self._extract_summary(clean_content)
            
            # Retourner les données parsées
            return {
                'type': 'pdf',
                'content': clean_content,
                'title': file_path.stem,
                'authors': [],
                'date': None,
                'summary': summary,
                'url': None,
                'doi': None,
                'error': 'PyPDF non disponible, extraction basique utilisée',
            }
            
        except Exception as e:
            return {
                'type': 'pdf',
                'content': '',
                'title': file_path.stem,
                'authors': [],
                'date': None,
                'summary': '',
                'url': None,
                'doi': None,
                'error': str(e),
            }
    
    def _extract_pdf_metadata(self, reader) -> Dict[str, Any]:
        """
        Extraire les métadonnées d'un PDF.
        
        Args:
            reader: PdfReader.
            
        Returns:
            Dictionnaire avec les métadonnées.
        """
        metadata = {}
        
        # Extraire les métadonnées du document
        doc_info = reader.metadata
        
        if doc_info:
            if doc_info.get('/Title'):
                metadata['title'] = doc_info['/Title']
            if doc_info.get('/Author'):
                metadata['authors'] = [doc_info['/Author']]
            if doc_info.get('/CreationDate'):
                metadata['date'] = doc_info['/CreationDate'].strftime('%Y-%m-%d')
        
        return metadata
