"""
Tests unitaires pour la configuration.
"""

import pytest
import os
from pathlib import Path
import sys

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.config import WikiConfig, get_config, set_config, get_default_config


class TestWikiConfig:
    """Tests pour WikiConfig."""
    
    def test_default_config(self):
        """Tester la configuration par défaut."""
        config = get_default_config()
        
        assert config.vault_path == Path("vault")
        assert config.raw_path == Path("vault/raw")
        assert config.wiki_path == Path("vault/wiki")
        assert config.llm_model == "claude-3-5-sonnet-20241022"
        assert config.llm_temperature == 0.7
        assert config.llm_max_tokens == 4096
        assert config.embedding_model == "text-embedding-3-small"
        assert config.embedding_dimension == 1536
        assert config.use_bm25 is True
        assert config.use_embeddings is True
        assert config.bm25_k == 50
        assert config.embedding_k == 10
        assert config.rrf_k == 20
        assert config.max_source_size == 100000
        assert config.chunk_size == 2000
        assert config.chunk_overlap == 200
        assert config.log_level == "INFO"
        assert config.tool == "all"
        assert config.topic == "Recherche"
    
    def test_from_dict(self):
        """Tester la création depuis un dictionnaire."""
        config_dict = {
            "vault_path": Path("/custom/vault"),
            "llm_model": "gpt-4",
            "llm_temperature": 0.5,
            "topic": "Custom Topic",
        }
        
        config = WikiConfig.from_dict(config_dict)
        
        assert config.vault_path == Path("/custom/vault")
        assert config.llm_model == "gpt-4"
        assert config.llm_temperature == 0.5
        assert config.topic == "Custom Topic"
        # Les valeurs non spécifiées doivent être les valeurs par défaut
        assert config.llm_max_tokens == 4096
    
    def test_to_dict(self):
        """Tester la conversion en dictionnaire."""
        config = WikiConfig(
            vault_path=Path("/test/vault"),
            llm_model="test-model",
            topic="Test",
        )
        
        config_dict = config.to_dict()
        
        assert config_dict["vault_path"] == "/test/vault"
        assert config_dict["llm_model"] == "test-model"
        assert config_dict["topic"] == "Test"
        # Les valeurs par défaut ne doivent pas être incluses
        assert "raw_path" not in config_dict
    
    def test_save_and_load(self, tmp_path):
        """Tester la sauvegarde et le chargement."""
        config = WikiConfig(
            vault_path=Path(tmp_path) / "vault",
            llm_model="test-model",
            topic="Test",
        )
        
        config_path = tmp_path / "config.json"
        config.save_to_file(config_path)
        
        loaded_config = WikiConfig.load_from_file(config_path)
        
        assert loaded_config.vault_path == Path(tmp_path) / "vault"
        assert loaded_config.llm_model == "test-model"
        assert loaded_config.topic == "Test"


class TestGlobalConfig:
    """Tests pour la configuration globale."""
    
    def test_get_and_set_config(self):
        """Tester get_config et set_config."""
        # Réinitialiser
        set_config(None)
        
        # Obtenir la configuration par défaut
        config = get_config()
        assert config.vault_path == Path("vault")
        
        # Définir une nouvelle configuration
        new_config = WikiConfig(
            vault_path=Path("/custom/vault"),
            topic="Custom",
        )
        set_config(new_config)
        
        # Obtenir la nouvelle configuration
        config = get_config()
        assert config.vault_path == Path("/custom/vault")
        assert config.topic == "Custom"
        
        # Réinitialiser
        set_config(None)
    
    def test_reset_config(self):
        """Tester reset_config."""
        # Définir une configuration
        config = WikiConfig(
            vault_path=Path("/test/vault"),
            topic="Test",
        )
        set_config(config)
        
        # Réinitialiser
        reset_config()
        
        # Obtenir la configuration par défaut
        config = get_config()
        assert config.vault_path == Path("vault")
