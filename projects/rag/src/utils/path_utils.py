"""
Utilitaires de chemins pour le système RAG Wiki.
"""

import re
from pathlib import Path
from typing import Optional
import unicodedata


def normalize_path(path: str) -> str:
    """
    Normaliser un chemin.
    
    Args:
        path: Chemin à normaliser.
        
    Returns:
        Chemin normalisé.
    """
    if not path:
        return ""
    
    # Convertir en Path pour normaliser
    path_obj = Path(path)
    
    # Normaliser chaque partie
    parts = []
    for part in path_obj.parts:
        if part:
            # Normaliser comme un nom
            normalized_part = normalize_name(part)
            parts.append(normalized_part)
    
    # Reconstruire le chemin
    normalized = Path(*parts)
    
    # Convertir en string
    return str(normalized)


def relative_to_vault(path: Path, vault_path: Path) -> Optional[Path]:
    """
    Convertir un chemin en chemin relatif au vault.
    
    Args:
        path: Chemin absolu.
        vault_path: Chemin du vault.
        
    Returns:
        Chemin relatif ou None si le chemin n'est pas dans le vault.
    """
    try:
        return path.relative_to(vault_path)
    except ValueError:
        return None


def is_within_vault(path: Path, vault_path: Path) -> bool:
    """
    Vérifier si un chemin est dans le vault.
    
    Args:
        path: Chemin à vérifier.
        vault_path: Chemin du vault.
        
    Returns:
        True si le chemin est dans le vault.
    """
    try:
        path.resolve().relative_to(vault_path.resolve())
        return True
    except ValueError:
        return False


def get_file_type(file_path: Path) -> str:
    """
    Obtenir le type d'un fichier à partir de son extension.
    
    Args:
        file_path: Chemin du fichier.
        
    Returns:
        Type du fichier.
    """
    suffix = file_path.suffix.lower()
    
    if suffix == ".pdf":
        return "pdf"
    elif suffix in [".html", ".htm"]:
        return "html"
    elif suffix == ".md":
        return "markdown"
    elif suffix == ".txt":
        return "text"
    else:
        return "unknown"


def get_page_type_from_path(page_path: Path) -> Optional[str]:
    """
    Déduire le type de page à partir du chemin.
    
    Args:
        page_path: Chemin de la page.
        
    Returns:
        Type de page ou None.
    """
    relative_path = Path(page_path)
    parts = relative_path.parts
    
    if len(parts) >= 2:
        if parts[-2] == "entities":
            return "entity"
        elif parts[-2] == "concepts":
            return "concept"
        elif parts[-2] == "sources":
            return "source"
        elif parts[-2] == "comparisons":
            return "comparison"
        elif parts[-2] == "synthesis":
            return "synthesis"
    
    if page_path.name == "index.md":
        return "index"
    elif page_path.name == "log.md":
        return "log"
    
    return None
