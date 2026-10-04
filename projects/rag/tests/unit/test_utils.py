"""
Tests unitaires pour les utilitaires.
"""

import pytest
from pathlib import Path
import sys

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.text_utils import normalize_name
from utils.path_utils import normalize_path


class TestTextUtils:
    """Tests pour les utilitaires texte."""
    
    def test_normalize_name_basic(self):
        """Tester la normalisation de noms basiques."""
        assert normalize_name("Test Name") == "test_name"
        assert normalize_name("test name") == "test_name"
        assert normalize_name("TEST NAME") == "test_name"
    
    def test_normalize_name_special_chars(self):
        """Tester la normalisation avec caractères spéciaux."""
        assert normalize_name("Test-Name") == "test_name"
        assert normalize_name("Test.Name") == "test_name"
        assert normalize_name("Test Name!") == "test_name"
        assert normalize_name("Test@Name") == "test_name"
    
    def test_normalize_name_accents(self):
        """Tester la normalisation avec accents."""
        assert normalize_name("Andréj Karpathy") == "andrej_karpathy"
        assert normalize_name("Café") == "cafe"
        assert normalize_name("Naïve") == "naive"
    
    def test_normalize_name_multiple_spaces(self):
        """Tester la normalisation avec espaces multiples."""
        assert normalize_name("Test   Name") == "test_name"
        assert normalize_name("  Test Name  ") == "test_name"
    
    def test_normalize_name_empty(self):
        """Tester la normalisation de chaîne vide."""
        assert normalize_name("") == ""
        assert normalize_name("   ") == ""


class TestPathUtils:
    """Tests pour les utilitaires de chemins."""
    
    def test_normalize_path_basic(self):
        """Tester la normalisation de chemins basiques."""
        assert normalize_path("Test/Path") == "test/path"
        assert normalize_path("TEST/PATH") == "test/path"
        assert normalize_path("test/path") == "test/path"
    
    def test_normalize_path_with_extension(self):
        """Tester la normalisation avec extension."""
        assert normalize_path("Test/File.md") == "test/file.md"
        assert normalize_path("TEST/FILE.PDF") == "test/file.pdf"
    
    def test_normalize_path_special_chars(self):
        """Tester la normalisation avec caractères spéciaux."""
        assert normalize_path("Test-File_Name.md") == "test_file_name.md"
        assert normalize_path("Test File (1).md") == "test_file_1.md"
    
    def test_normalize_path_accents(self):
        """Tester la normalisation avec accents."""
        assert normalize_path("Documents/Andréj.md") == "documents/andrej.md"
        assert normalize_path("Café/Menu.md") == "cafe/menu.md"
