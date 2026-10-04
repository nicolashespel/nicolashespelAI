"""
Utilitaires de dates pour le système RAG Wiki.
"""

from datetime import datetime
from typing import Optional
import re


def format_date(date: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Formater une date.
    
    Args:
        date: Date à formater.
        format: Format de sortie.
        
    Returns:
        Date formatée.
    """
    return date.strftime(format)


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parser une chaîne de date.
    
    Args:
        date_str: Chaîne de date à parser.
        
    Returns:
        Objet datetime ou None.
    """
    if not date_str:
        return None
    
    # Essayer différents formats
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%d %B %Y",
        "%B %d, %Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def parse_date_from_content(content: str) -> Optional[datetime]:
    """
    Parser une date depuis un contenu.
    
    Args:
        content: Contenu à analyser.
        
    Returns:
        Date trouvée ou None.
    """
    # Patterns de date
    patterns = [
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            date_str = match.group(1)
            date = parse_date(date_str)
            if date:
                return date
    
    return None


def get_current_timestamp() -> str:
    """
    Obtenir un timestamp actuel.
    
    Returns:
        Timestamp formaté.
    """
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")


def get_current_date() -> str:
    """
    Obtenir une date actuelle.
    
    Returns:
        Date formatée.
    """
    return datetime.now().strftime("%Y-%m-%d")
