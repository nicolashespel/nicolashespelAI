"""
Module OpenWebUI - Configuration et intégration pour OpenWebUI.

Ce module fournit:
- Configuration des 4 agents pour OpenWebUI
- Scripts de setup automatique
- Documentation complète
"""

from .setup import OpenWebUISetup
from .config import OpenWebUIConfig

__all__ = [
    "OpenWebUISetup",
    "OpenWebUIConfig",
]
