"""
Configuration du logging pour le système RAG Wiki.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


# Logger global
_logger: Optional[logging.Logger] = None


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> logging.Logger:
    """
    Configurer le logging.
    
    Args:
        level: Niveau de logging (DEBUG, INFO, WARNING, ERROR).
        log_file: Fichier de log (optionnel).
        format: Format des messages de log.
        
    Returns:
        Logger configuré.
    """
    global _logger
    
    # Convertir le niveau
    level = getattr(logging, level.upper(), logging.INFO)
    
    # Créer le logger
    logger = logging.getLogger("rag_wiki")
    logger.setLevel(level)
    
    # Supprimer les handlers existants
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Créer un formatter
    formatter = logging.Formatter(format)
    
    # Ajouter un handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Ajouter un handler fichier si spécifié
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    _logger = logger
    
    return logger


def get_logger() -> logging.Logger:
    """
    Obtenir le logger global.
    
    Returns:
        Logger.
    """
    global _logger
    
    if _logger is None:
        _logger = setup_logging()
    
    return _logger


def log_debug(message: str, *args, **kwargs) -> None:
    """Logger un message DEBUG."""
    get_logger().debug(message, *args, **kwargs)


def log_info(message: str, *args, **kwargs) -> None:
    """Logger un message INFO."""
    get_logger().info(message, *args, **kwargs)


def log_warning(message: str, *args, **kwargs) -> None:
    """Logger un message WARNING."""
    get_logger().warning(message, *args, **kwargs)


def log_error(message: str, *args, **kwargs) -> None:
    """Logger un message ERROR."""
    get_logger().error(message, *args, **kwargs)
