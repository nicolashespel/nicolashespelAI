"""
Gestionnaire de fichiers pour le système RAG Wiki.

Ce module contient la classe FileManager qui gère les opérations de base
sur les fichiers (lecture, écriture, suppression).
"""

import os
from pathlib import Path
from typing import Optional, BinaryIO, TextIO


class FileManager:
    """
    Gestionnaire de fichiers pour le système RAG Wiki.
    
    Cette classe fournit une interface simple pour les opérations sur les fichiers,
    avec une gestion des erreurs et des chemins.
    """
    
    def __init__(self, base_path: Path) -> None:
        """
        Initialiser le FileManager.
        
        Args:
            base_path: Chemin de base pour les opérations.
        """
        self.base_path = base_path
        
        # Créer le dossier de base s'il n'existe pas
        base_path.mkdir(parents=True, exist_ok=True)
    
    def read_file(self, file_path: Path, mode: str = "r", encoding: str = "utf-8") -> Optional[str]:
        """
        Lire un fichier.
        
        Args:
            file_path: Chemin du fichier.
            mode: Mode d'ouverture.
            encoding: Encodage du fichier.
            
        Returns:
            Contenu du fichier ou None.
        """
        try:
            # Résoudre le chemin relatif à la base
            full_path = self._resolve_path(file_path)
            
            # Vérifier que le fichier existe
            if not full_path.exists():
                return None
            
            # Vérifier que le fichier est dans le base_path
            if not self._is_within_base(full_path):
                raise ValueError(f"Fichier en dehors de la base: {full_path}")
            
            # Lire le fichier
            with open(full_path, mode, encoding=encoding) as f:
                return f.read()
                
        except Exception as e:
            print(f"Erreur lors de la lecture de {file_path}: {e}")
            return None
    
    def read_binary(self, file_path: Path) -> Optional[bytes]:
        """
        Lire un fichier binaire.
        
        Args:
            file_path: Chemin du fichier.
            
        Returns:
            Contenu binaire ou None.
        """
        try:
            full_path = self._resolve_path(file_path)
            
            if not full_path.exists():
                return None
            
            if not self._is_within_base(full_path):
                raise ValueError(f"Fichier en dehors de la base: {full_path}")
            
            with open(full_path, "rb") as f:
                return f.read()
                
        except Exception as e:
            print(f"Erreur lors de la lecture binaire de {file_path}: {e}")
            return None
    
    def write_file(
        self,
        file_path: Path,
        content: str,
        mode: str = "w",
        encoding: str = "utf-8",
    ) -> bool:
        """
        Écrire dans un fichier.
        
        Args:
            file_path: Chemin du fichier.
            content: Contenu à écrire.
            mode: Mode d'ouverture.
            encoding: Encodage du fichier.
            
        Returns:
            True si l'écriture a réussi.
        """
        try:
            full_path = self._resolve_path(file_path)
            
            # Vérifier que le fichier est dans le base_path
            if not self._is_within_base(full_path):
                raise ValueError(f"Fichier en dehors de la base: {full_path}")
            
            # Créer les dossiers parents si nécessaire
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Écrire le fichier
            with open(full_path, mode, encoding=encoding) as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'écriture de {file_path}: {e}")
            return False
    
    def write_binary(self, file_path: Path, content: bytes) -> bool:
        """
        Écrire dans un fichier binaire.
        
        Args:
            file_path: Chemin du fichier.
            content: Contenu binaire à écrire.
            
        Returns:
            True si l'écriture a réussi.
        """
        try:
            full_path = self._resolve_path(file_path)
            
            if not self._is_within_base(full_path):
                raise ValueError(f"Fichier en dehors de la base: {full_path}")
            
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, "wb") as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'écriture binaire de {file_path}: {e}")
            return False
    
    def delete_file(self, file_path: Path) -> bool:
        """
        Supprimer un fichier.
        
        Args:
            file_path: Chemin du fichier.
            
        Returns:
            True si la suppression a réussi.
        """
        try:
            full_path = self._resolve_path(file_path)
            
            if not full_path.exists():
                return False
            
            if not self._is_within_base(full_path):
                raise ValueError(f"Fichier en dehors de la base: {full_path}")
            
            full_path.unlink()
            return True
            
        except Exception as e:
            print(f"Erreur lors de la suppression de {file_path}: {e}")
            return False
    
    def file_exists(self, file_path: Path) -> bool:
        """
        Vérifier si un fichier existe.
        
        Args:
            file_path: Chemin du fichier.
            
        Returns:
            True si le fichier existe.
        """
        try:
            full_path = self._resolve_path(file_path)
            return full_path.exists() and self._is_within_base(full_path)
        except Exception:
            return False
    
    def get_file_size(self, file_path: Path) -> int:
        """
        Obtenir la taille d'un fichier.
        
        Args:
            file_path: Chemin du fichier.
            
        Returns:
            Taille en octets.
        """
        try:
            full_path = self._resolve_path(file_path)
            if full_path.exists() and self._is_within_base(full_path):
                return full_path.stat().st_size
            return 0
        except Exception:
            return 0
    
    def list_files(self, directory: Path, pattern: str = "*") -> List[Path]:
        """
        Lister les fichiers dans un dossier.
        
        Args:
            directory: Chemin du dossier.
            pattern: Pattern de filtrage.
            
        Returns:
            Liste des chemins de fichiers.
        """
        try:
            full_dir = self._resolve_path(directory)
            
            if not self._is_within_base(full_dir):
                raise ValueError(f"Dossier en dehors de la base: {full_dir}")
            
            files = []
            for file in full_dir.glob(pattern):
                if file.is_file():
                    files.append(file)
            
            return files
            
        except Exception as e:
            print(f"Erreur lors de la liste des fichiers dans {directory}: {e}")
            return []
    
    def list_dirs(self, directory: Path) -> List[Path]:
        """
        Lister les dossiers dans un dossier.
        
        Args:
            directory: Chemin du dossier.
            
        Returns:
            Liste des chemins de dossiers.
        """
        try:
            full_dir = self._resolve_path(directory)
            
            if not self._is_within_base(full_dir):
                raise ValueError(f"Dossier en dehors de la base: {full_dir}")
            
            dirs = []
            for item in full_dir.iterdir():
                if item.is_dir():
                    dirs.append(item)
            
            return dirs
            
        except Exception as e:
            print(f"Erreur lors de la liste des dossiers dans {directory}: {e}")
            return []
    
    def _resolve_path(self, path: Path) -> Path:
        """
        Résoudre un chemin relatif à la base.
        
        Args:
            path: Chemin à résoudre.
            
        Returns:
            Chemin absolu résolu.
        """
        if path.is_absolute():
            return path
        else:
            return self.base_path / path
    
    def _is_within_base(self, path: Path) -> bool:
        """
        Vérifier si un chemin est dans la base.
        
        Args:
            path: Chemin à vérifier.
            
        Returns:
            True si le chemin est dans la base.
        """
        try:
            path.resolve().relative_to(self.base_path.resolve())
            return True
        except ValueError:
            return False
    
    def close(self) -> None:
        """Fermer les ressources du FileManager."""
        pass
