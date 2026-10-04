"""
Gestionnaire Git pour le système RAG Wiki.

Ce module contient la classe GitManager qui gère les opérations Git
optionnelles pour le vault.
"""

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class GitManager:
    """
    Gestionnaire Git pour le système RAG Wiki.
    
    Cette classe fournit une interface pour les opérations Git optionnelles,
    permettant de versionner le vault et de faire des commits atomiques.
    """
    
    def __init__(self, vault_path: Path) -> None:
        """
        Initialiser le GitManager.
        
        Args:
            vault_path: Chemin du vault.
        """
        self.vault_path = vault_path
        self._git_available = self._check_git_available()
        self._is_repo = self._check_is_git_repo()
    
    def _check_git_available(self) -> bool:
        """
        Vérifier si Git est disponible.
        
        Returns:
            True si Git est disponible.
        """
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_is_git_repo(self) -> bool:
        """
        Vérifier si le vault est un dépôt Git.
        
        Returns:
            True si c'est un dépôt Git.
        """
        if not self._git_available:
            return False
        
        git_dir = self.vault_path / ".git"
        return git_dir.exists()
    
    def initialize_repo(self) -> bool:
        """
        Initialiser un dépôt Git dans le vault.
        
        Returns:
            True si l'initialisation a réussi.
        """
        if not self._git_available:
            return False
        
        if self._is_repo:
            return True
        
        try:
            subprocess.run(
                ["git", "init"],
                cwd=self.vault_path,
                capture_output=True,
                text=True,
            )
            
            # Créer un .gitignore
            gitignore_content = """# Ignorer les fichiers temporaires
*.tmp
*.temp

# Ignorer les fichiers de cache
.cache/

# Ignorer les fichiers d'environnement
.env
.env.*

# Ignorer les fichiers de log (optionnel)
*.log
"""
            self._write_gitignore(gitignore_content)
            
            # Premier commit
            self.add_all()
            self.commit("Initial commit")
            
            self._is_repo = True
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'initialisation Git: {e}")
            return False
    
    def _write_gitignore(self, content: str) -> None:
        """
        Écrire le fichier .gitignore.
        
        Args:
            content: Contenu du .gitignore.
        """
        gitignore_path = self.vault_path / ".gitignore"
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    def add_file(self, file_path: Path) -> bool:
        """
        Ajouter un fichier à l'index Git.
        
        Args:
            file_path: Chemin du fichier.
            
        Returns:
            True si l'ajout a réussi.
        """
        if not self._git_available or not self._is_repo:
            return False
        
        try:
            # Convertir en chemin relatif
            relative_path = file_path.relative_to(self.vault_path)
            
            result = subprocess.run(
                ["git", "add", str(relative_path)],
                cwd=self.vault_path,
                capture_output=True,
                text=True,
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Erreur lors de l'ajout de {file_path}: {e}")
            return False
    
    def add_all(self) -> bool:
        """
        Ajouter tous les fichiers à l'index Git.
        
        Returns:
            True si l'ajout a réussi.
        """
        if not self._git_available or not self._is_repo:
            return False
        
        try:
            result = subprocess.run(
                ["git", "add", "."],
                cwd=self.vault_path,
                capture_output=True,
                text=True,
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Erreur lors de l'ajout de tous les fichiers: {e}")
            return False
    
    def commit(self, message: str) -> bool:
        """
        Faire un commit Git.
        
        Args:
            message: Message de commit.
            
        Returns:
            True si le commit a réussi.
        """
        if not self._git_available or not self._is_repo:
            return False
        
        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.vault_path,
                capture_output=True,
                text=True,
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Erreur lors du commit: {e}")
            return False
    
    def commit_all(self, message: str) -> bool:
        """
        Ajouter tous les fichiers et faire un commit.
        
        Args:
            message: Message de commit.
            
        Returns:
            True si l'opération a réussi.
        """
        if not self.add_all():
            return False
        
        return self.commit(message)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtenir le statut Git.
        
        Returns:
            Dictionnaire avec le statut.
        """
        if not self._git_available or not self._is_repo:
            return {"status": "not_a_repo", "modified": [], "untracked": []}
        
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.vault_path,
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                return {"status": "error", "modified": [], "untracked": []}
            
            lines = result.stdout.strip().split('\n')
            modified = []
            untracked = []
            
            for line in lines:
                if line.startswith("M"):
                    modified.append(line[3:])
                elif line.startswith("??"):
                    untracked.append(line[3:])
            
            return {
                "status": "ok",
                "modified": modified,
                "untracked": untracked,
            }
            
        except Exception as e:
            print(f"Erreur lors de la récupération du statut Git: {e}")
            return {"status": "error", "modified": [], "untracked": []}
    
    def get_log(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtenir l'historique des commits.
        
        Args:
            limit: Nombre maximal de commits.
            
        Returns:
            Liste des commits.
        """
        if not self._git_available or not self._is_repo:
            return []
        
        try:
            result = subprocess.run(
                ["git", "log", f"--max-count={limit}", "--pretty=format:%H|%an|%ad|%s"],
                cwd=self.vault_path,
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                return []
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        commits.append({
                            "hash": parts[0],
                            "author": parts[1],
                            "date": parts[2],
                            "message": parts[3],
                        })
            
            return commits
            
        except Exception as e:
            print(f"Erreur lors de la récupération du log Git: {e}")
            return []
    
    def checkout_branch(self, branch_name: str) -> bool:
        """
        Changer de branche.
        
        Args:
            branch_name: Nom de la branche.
            
        Returns:
            True si le changement a réussi.
        """
        if not self._git_available or not self._is_repo:
            return False
        
        try:
            result = subprocess.run(
                ["git", "checkout", branch_name],
                cwd=self.vault_path,
                capture_output=True,
                text=True,
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Erreur lors du checkout de la branche {branch_name}: {e}")
            return False
    
    def create_branch(self, branch_name: str) -> bool:
        """
        Créer une nouvelle branche.
        
        Args:
            branch_name: Nom de la branche.
            
        Returns:
            True si la création a réussi.
        """
        if not self._git_available or not self._is_repo:
            return False
        
        try:
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.vault_path,
                capture_output=True,
                text=True,
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Erreur lors de la création de la branche {branch_name}: {e}")
            return False
    
    def push(self, remote: str = "origin", branch: str = "main") -> bool:
        """
        Pousser vers un dépôt distant.
        
        Args:
            remote: Nom du dépôt distant.
            branch: Nom de la branche.
            
        Returns:
            True si le push a réussi.
        """
        if not self._git_available or not self._is_repo:
            return False
        
        try:
            result = subprocess.run(
                ["git", "push", remote, branch],
                cwd=self.vault_path,
                capture_output=True,
                text=True,
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Erreur lors du push vers {remote}/{branch}: {e}")
            return False
    
    def pull(self, remote: str = "origin", branch: str = "main") -> bool:
        """
        Tirer depuis un dépôt distant.
        
        Args:
            remote: Nom du dépôt distant.
            branch: Nom de la branche.
            
        Returns:
            True si le pull a réussi.
        """
        if not self._git_available or not self._is_repo:
            return False
        
        try:
            result = subprocess.run(
                ["git", "pull", remote, branch],
                cwd=self.vault_path,
                capture_output=True,
                text=True,
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Erreur lors du pull depuis {remote}/{branch}: {e}")
            return False
    
    def is_git_available(self) -> bool:
        """
        Vérifier si Git est disponible.
        
        Returns:
            True si Git est disponible.
        """
        return self._git_available
    
    def is_git_repo(self) -> bool:
        """
        Vérifier si le vault est un dépôt Git.
        
        Returns:
            True si c'est un dépôt Git.
        """
        return self._is_repo
    
    def close(self) -> None:
        """Fermer les ressources du GitManager."""
        pass
