"""
Utilitaires texte pour le système RAG Wiki.
"""

import re
from typing import List, Optional
import unicodedata


def normalize_name(name: str) -> str:
    """
    Normaliser un nom pour l'utiliser comme identifiant.
    
    Args:
        name: Nom à normaliser.
        
    Returns:
        Nom normalisé.
    """
    if not name:
        return ""
    
    # Supprimer les accents
    normalized = unicodedata.normalize('NFKD', name)
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    
    # Convertir en minuscules
    normalized = normalized.lower()
    
    # Remplacer les caractères spéciaux par des underscores
    normalized = re.sub(r'[^\w\s-]', '_', normalized)
    
    # Remplacer les espaces et tirets par des underscores
    normalized = re.sub(r'[\s-]+', '_', normalized)
    
    # Supprimer les underscores en début et fin
    normalized = normalized.strip('_')
    
    return normalized


def clean_text(text: str) -> str:
    """
    Nettoyer un texte.
    
    Args:
        text: Texte à nettoyer.
        
    Returns:
        Texte nettoyé.
    """
    if not text:
        return ""
    
    # Supprimer les caractères de contrôle
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Normaliser les espaces
    text = re.sub(r'\s+', ' ', text)
    
    # Normaliser les sauts de ligne
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Supprimer les espaces en début et fin
    text = text.strip()
    
    return text


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extraire les mots-clés d'un texte.
    
    Args:
        text: Texte à analyser.
        min_length: Longueur minimale des mots-clés.
        
    Returns:
        Liste de mots-clés.
    """
    if not text:
        return []
    
    # Mots vides à exclure
    stop_words = {
        "le", "la", "les", "un", "une", "des", "de", "du", "de", "l", "d",
        "a", "an", "the", "is", "are", "was", "were", "been", "be",
        "to", "of", "and", "or", "in", "on", "at", "for", "with", "by",
        "what", "why", "when", "where", "who", "how", "which", "that",
        "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
        "as", "it", "its", "their", "them", "then", "than", "there", "here",
        "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
        "no", "nor", "not", "only", "own", "same", "so", "too", "very",
    }
    
    # Tokenizer
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filtrer
    keywords = [
        word for word in words 
        if len(word) >= min_length and word not in stop_words
    ]
    
    return list(set(keywords))


def truncate_text(text: str, max_length: int) -> str:
    """
    Tronquer un texte.
    
    Args:
        text: Texte à tronquer.
        max_length: Longueur maximale.
        
    Returns:
        Texte tronqué.
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."


def similarity(text1: str, text2: str) -> float:
    """
    Calculer la similarité entre deux textes (simple implémentation).
    
    Args:
        text1: Premier texte.
        text2: Deuxième texte.
        
    Returns:
        Score de similarité entre 0 et 1.
    """
    if not text1 or not text2:
        return 0.0
    
    # Tokenizer
    tokens1 = set(clean_text(text1).lower().split())
    tokens2 = set(clean_text(text2).lower().split())
    
    # Similarité de Jaccard
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    
    if union == 0:
        return 0.0
    
    return intersection / union
