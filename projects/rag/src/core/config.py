"""
Configuration centrale du système RAG Wiki.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WikiConfig(BaseModel):
    """Configuration principale du système RAG Wiki."""
    
    # Chemins
    vault_path: Path = Field(
        default=Path("vault"),
        description="Chemin vers le vault"
    )
    raw_path: Path = Field(
        default=Path("vault/raw"),
        description="Chemin vers le dossier raw"
    )
    wiki_path: Path = Field(
        default=Path("vault/wiki"),
        description="Chemin vers le dossier wiki"
    )
    
    # Configuration LLM
    llm_model: str = Field(
        default="mistral-large-latest",
        description="Modèle LLM à utiliser"
    )
    llm_api_key: Optional[str] = Field(
        default=None,
        description="Clé API pour le LLM"
    )
    llm_temperature: float = Field(
        default=0.7,
        description="Température du LLM"
    )
    llm_max_tokens: int = Field(
        default=4096,
        description="Nombre maximal de tokens"
    )
    
    # Configuration Embeddings
    embedding_model: str = Field(
        default="mistral-embed",
        description="Modèle d'embedding à utiliser"
    )
    embedding_api_key: Optional[str] = Field(
        default=None,
        description="Clé API pour les embeddings (utilise la même que LLM si None)"
    )
    embedding_dimension: int = Field(
        default=1024,
        description="Dimension des embeddings"
    )
    
    # Configuration Index
    use_bm25: bool = Field(
        default=True,
        description="Utiliser BM25 pour la recherche"
    )
    use_embeddings: bool = Field(
        default=True,
        description="Utiliser les embeddings pour la recherche"
    )
    bm25_k: int = Field(
        default=50,
        description="Nombre de résultats BM25"
    )
    embedding_k: int = Field(
        default=10,
        description="Nombre de résultats embeddings"
    )
    rrf_k: int = Field(
        default=20,
        description="Nombre de résultats RRF final"
    )
    
    # Configuration Ingestion
    max_source_size: int = Field(
        default=100000,
        description="Taille maximale des sources en caractères"
    )
    chunk_size: int = Field(
        default=2000,
        description="Taille des chunks pour le traitement"
    )
    chunk_overlap: int = Field(
        default=200,
        description="Overlap entre les chunks"
    )
    
    # Configuration Logging
    log_level: str = Field(
        default="INFO",
        description="Niveau de logging"
    )
    log_file: str = Field(
        default="vault/wiki/log.md",
        description="Fichier de log"
    )
    
    # Configuration Outils
    tool: str = Field(
        default="all",
        description="Outil LLM à configurer (all, claude, codex, cursor)"
    )
    
    # Configuration Vault
    topic: str = Field(
        default="Recherche",
        description="Sujet principal du vault"
    )
    
    @classmethod
    def from_env(cls) -> "WikiConfig":
        """Charger la configuration depuis les variables d'environnement."""
        return cls(
            vault_path=Path(os.getenv("WIKI_VAULT_PATH", "vault")),
            llm_model=os.getenv("WIKI_LLM_MODEL", "mistral-large-latest"),
            llm_api_key=os.getenv("WIKI_LLM_API_KEY"),
            llm_temperature=float(os.getenv("WIKI_LLM_TEMPERATURE", "0.7")),
            llm_max_tokens=int(os.getenv("WIKI_LLM_MAX_TOKENS", "4096")),
            embedding_model=os.getenv("WIKI_EMBEDDING_MODEL", "mistral-embed"),
            embedding_api_key=os.getenv("WIKI_EMBEDDING_API_KEY"),
            log_level=os.getenv("WIKI_LOG_LEVEL", "INFO"),
            tool=os.getenv("WIKI_TOOL", "all"),
            topic=os.getenv("WIKI_TOPIC", "Recherche"),
        )
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "WikiConfig":
        """Créer une configuration depuis un dictionnaire."""
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir la configuration en dictionnaire."""
        return self.model_dump(exclude_none=True)
    
    def save_to_file(self, path: Path) -> None:
        """Sauvegarder la configuration dans un fichier."""
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, path: Path) -> "WikiConfig":
        """Charger la configuration depuis un fichier."""
        import json
        with open(path, "r", encoding="utf-8") as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)


# Configuration par défaut
def get_default_config() -> WikiConfig:
    """Obtenir la configuration par défaut."""
    return WikiConfig()


# Configuration globale
_config: Optional[WikiConfig] = None


def set_config(config: WikiConfig) -> None:
    """Définir la configuration globale."""
    global _config
    _config = config


def get_config() -> WikiConfig:
    """Obtenir la configuration globale."""
    global _config
    if _config is None:
        _config = get_default_config()
    return _config


def reset_config() -> None:
    """Réinitialiser la configuration globale."""
    global _config
    _config = None
