"""
Processeur de nettoyage pour les documents textuels.

Ce module nettoie et structure le texte extrait par OCR ou provenant
d'autres sources.
"""

import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class CleanupProcessor:
    """
    Processeur pour nettoyer et structurer le texte.
    
    Fonctionnalités:
    - Suppression des en-têtes et pieds de page
    - Suppression des numéros de page
    - Suppression du texte boilerplate
    - Normalisation du texte
    - Détection de la langue
    - Structuration en sections
    """
    
    def __init__(
        self,
        remove_headers: bool = True,
        remove_footers: bool = True,
        remove_page_numbers: bool = True,
        remove_boilerplate: bool = True,
        normalize_text: bool = True,
        detect_language: bool = True,
        min_text_length: int = 50,
    ) -> None:
        """
        Initialiser le processeur de nettoyage.
        
        Args:
            remove_headers: Supprimer les en-têtes.
            remove_footers: Supprimer les pieds de page.
            remove_page_numbers: Supprimer les numéros de page.
            remove_boilerplate: Supprimer le texte boilerplate.
            normalize_text: Normaliser le texte.
            detect_language: Détecter la langue.
            min_text_length: Longueur minimale du texte.
        """
        self.remove_headers = remove_headers
        self.remove_footers = remove_footers
        self.remove_page_numbers = remove_page_numbers
        self.remove_boilerplate = remove_boilerplate
        self.normalize_text = normalize_text
        self.detect_language = detect_language
        self.min_text_length = min_text_length
        
        # Patterns pour le nettoyage
        self.page_number_patterns = [
            r'\n\s*\d+\s*\n',  # Numéro de page seul
            r'\n\s*Page \d+\s*\n',  # "Page X"
            r'\n\s*\d+\s*of\s*\d+\s*\n',  # "X of Y"
            r'\bPage \d+ of \d+\b',  # "Page X of Y"
        ]
        
        self.header_patterns = [
            r'^\s*Confidential\s*$',
            r'^\s*Internal Use Only\s*$',
            r'^\s*Do Not Distribute\s*$',
        ]
        
        self.footer_patterns = [
            r'^\s*All rights reserved\s*$',
            r'^\s*© \d{4}\s*$',
            r'^\s*\d{4} .+\s*$',
        ]
        
        # Mots vides à supprimer
        self.boilerplate_phrases = [
            "This document is",
            "This page is",
            "The information contained",
            "All rights reserved",
            "Confidential and proprietary",
            "For internal use only",
        ]
    
    def _remove_page_numbers(self, text: str) -> str:
        """Supprimer les numéros de page."""
        for pattern in self.page_number_patterns:
            text = re.sub(pattern, "\n", text, flags=re.IGNORECASE | re.MULTILINE)
        return text
    
    def _remove_headers(self, text: str) -> str:
        """Supprimer les en-têtes."""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_lower = line.lower().strip()
            is_header = any(
                re.match(pattern, line_lower, re.IGNORECASE)
                for pattern in self.header_patterns
            )
            
            if not is_header:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _remove_footers(self, text: str) -> str:
        """Supprimer les pieds de page."""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_lower = line.lower().strip()
            is_footer = any(
                re.match(pattern, line_lower, re.IGNORECASE)
                for pattern in self.footer_patterns
            )
            
            if not is_footer:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _remove_boilerplate(self, text: str) -> str:
        """Supprimer le texte boilerplate."""
        for phrase in self.boilerplate_phrases:
            text = re.sub(
                re.escape(phrase),
                "",
                text,
                flags=re.IGNORECASE
            )
        return text
    
    def _normalize_text(self, text: str) -> str:
        """Normaliser le texte."""
        # Supprimer les espaces multiples
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Supprimer les lignes vides multiples
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Nettoyer les espaces en début/fin de ligne
        text = '\n'.join(line.strip() for line in text.split('\n'))
        
        # Supprimer les espaces avant la ponctuation
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        
        # Supprimer les espaces après la ponctuation d'ouverture
        text = re.sub(r'([(\[{])\s+', r'\1', text)
        
        return text
    
    def _detect_language(self, text: str) -> str:
        """Détecter la langue du texte (simplifié)."""
        # Mots indicateurs pour le français
        french_words = [
            "le", "la", "les", "de", "des", "un", "une", "et", "est", "en",
            "à", "au", "du", "pour", "par", "sur", "avec", "sans", "dans",
        ]
        
        # Mots indicateurs pour l'anglais
        english_words = [
            "the", "a", "an", "and", "is", "in", "on", "at", "to", "of",
            "for", "with", "without", "this", "that", "it", "are", "was",
        ]
        
        text_lower = text.lower()
        
        # Compter les mots français
        french_count = sum(text_lower.count(word) for word in french_words)
        
        # Compter les mots anglais
        english_count = sum(text_lower.count(word) for word in english_words)
        
        if french_count > english_count:
            return "fr"
        elif english_count > french_count:
            return "en"
        else:
            return "unknown"
    
    def _clean_section(self, text: str) -> str:
        """Nettoyer une section de texte."""
        # Appliquer tous les nettoyages
        if self.remove_page_numbers:
            text = self._remove_page_numbers(text)
        
        if self.remove_headers:
            text = self._remove_headers(text)
        
        if self.remove_footers:
            text = self._remove_footers(text)
        
        if self.remove_boilerplate:
            text = self._remove_boilerplate(text)
        
        if self.normalize_text:
            text = self._normalize_text(text)
        
        return text
    
    def _split_into_sections(self, text: str) -> List[Dict[str, Any]]:
        """Diviser le texte en sections."""
        # Diviser par les titres (lignes commençant par #)
        lines = text.split('\n')
        sections = []
        current_section = {"title": "", "content": []}
        
        for line in lines:
            line = line.strip()
            
            # Vérifier si c'est un titre
            if line.startswith('#'):
                # Sauvegarder la section précédente
                if current_section["content"]:
                    current_section["content"] = '\n'.join(current_section["content"])
                    sections.append(current_section)
                
                # Nouvelle section
                title_level = len(line.split()[0]) if line.split() else 0
                title = line.lstrip('#').strip()
                current_section = {
                    "title": title,
                    "level": title_level,
                    "content": [],
                }
            elif line:
                current_section["content"].append(line)
        
        # Ajouter la dernière section
        if current_section["content"]:
            current_section["content"] = '\n'.join(current_section["content"])
            sections.append(current_section)
        
        return sections
    
    def clean_text(
        self,
        text: str,
        input_path: Optional[Union[Path, str]] = None,
    ) -> Dict[str, Any]:
        """
        Nettoyer le texte.
        
        Args:
            text: Texte à nettoyer.
            input_path: Chemin du fichier source (pour logging).
            
        Returns:
            Résultat du nettoyage avec texte nettoyé et métadonnées.
        """
        if not text or len(text.strip()) < self.min_text_length:
            return {
                "success": False,
                "error": "Texte trop court ou vide",
                "original_length": len(text),
            }
        
        original_length = len(text)
        original_lines = len(text.split('\n'))
        
        logger.info(f"Nettoyage: {original_length} caractères, {original_lines} lignes")
        
        # Nettoyer le texte
        cleaned_text = self._clean_section(text)
        
        # Détecter la langue
        language = "unknown"
        if self.detect_language:
            language = self._detect_language(cleaned_text)
        
        # Diviser en sections
        sections = self._split_into_sections(cleaned_text)
        
        # Calculer les statistiques
        cleaned_length = len(cleaned_text)
        cleaned_lines = len(cleaned_text.split('\n'))
        
        result = {
            "success": True,
            "original_length": original_length,
            "cleaned_length": cleaned_length,
            "original_lines": original_lines,
            "cleaned_lines": cleaned_lines,
            "language": language,
            "sections": sections,
            "text": cleaned_text,
            "statistics": {
                "characters_removed": original_length - cleaned_length,
                "lines_removed": original_lines - cleaned_lines,
                "compression_ratio": cleaned_length / original_length if original_length > 0 else 0,
            },
        }
        
        logger.info(
            f"Nettoyage terminé: {cleaned_length} caractères, "
            f"{len(sections)} sections, langue: {language}"
        )
        
        return result
    
    def clean_file(
        self,
        file_path: Union[Path, str],
    ) -> Dict[str, Any]:
        """
        Nettoyer un fichier texte.
        
        Args:
            file_path: Chemin du fichier à nettoyer.
            
        Returns:
            Résultat du nettoyage.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                "success": False,
                "error": f"Fichier non trouvé: {file_path}",
            }
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            return self.clean_text(text, file_path)
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file": str(file_path),
            }
