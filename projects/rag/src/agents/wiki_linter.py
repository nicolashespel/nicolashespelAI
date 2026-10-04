"""
Agent Wiki Linter pour le système RAG Wiki.

Cet agent effectue le linting complet du vault.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import WikiConfig
from ..core.wiki_engine import WikiEngine
from ..storage import VaultManager
from .base_agent import BaseAgent


class WikiLinterAgent(BaseAgent):
    """
    Agent Wiki Linter pour le système RAG Wiki.
    
    Cet agent est responsable du linting du vault :
    - Vérifications mécaniques
    - Vérifications sémantiques
    - Vérifications de santé
    - Génération de rapports
    """
    
    def __init__(
        self,
        vault_path: Path,
        config: Optional[WikiConfig] = None,
    ) -> None:
        """
        Initialiser l'agent Wiki Linter.
        
        Args:
            vault_path: Chemin du vault.
            config: Configuration du wiki.
        """
        super().__init__(
            name="WikiLinter",
            role="Vérification et maintenance du vault",
            vault_manager=VaultManager(vault_path),
            config=config or WikiConfig(vault_path=vault_path),
        )
        
        self.wiki_engine = WikiEngine(config=self.config, vault_path=vault_path)
    
    async def execute(
        self,
        check_mechanical: bool = True,
        check_semantic: bool = True,
        check_health: bool = True,
        generate_report: bool = True,
    ) -> Dict[str, Any]:
        """
        Exécuter le linting du vault.
        
        Args:
            check_mechanical: Vérifier les aspects mécaniques.
            check_semantic: Vérifier les aspects sémantiques.
            check_health: Vérifier la santé globale.
            generate_report: Générer un rapport détaillé.
            
        Returns:
            Rapport de linting.
        """
        report: Dict[str, Any] = {
            "check_mechanical": check_mechanical,
            "check_semantic": check_semantic,
            "check_health": check_health,
            "result": {},
            "report": "",
            "success": False,
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            # Effectuer le linting
            result = await self.wiki_engine.lint(
                check_mechanical=check_mechanical,
                check_semantic=check_semantic,
                check_health=check_health,
            )
            
            report["result"] = {
                "success": result.success,
                "issues": result.issues,
                "warnings": result.warnings,
                "errors": result.errors,
                "duration_seconds": result.duration_seconds,
                "error": result.error,
            }
            
            report["success"] = result.success
            
            # Générer le rapport si demandé
            if generate_report and result.success:
                report["report"] = self._generate_human_report(result)
            
            return report
            
        except Exception as e:
            report["error"] = str(e)
            report["success"] = False
            return report
    
    def _generate_human_report(self, lint_result) -> str:
        """
        Générer un rapport lisible pour un humain.
        
        Args:
            lint_result: Résultat du linting.
            
        Returns:
            Rapport formaté.
        """
        lines = [
            "# Rapport de Linting du Vault",
            "",
            f"**Date :** {datetime.now().strftime('%Y-%m-%d')}",
            f"**Heure :** {datetime.now().strftime('%H:%M:%S')}",
            f"**Durée :** {lint_result.duration_seconds:.2f} secondes",
            "",
            "## Statistiques",
            f"- **Erreurs :** {len(lint_result.errors)}",
            f"- **Avertissements :** {len(lint_result.warnings)}",
            f"- **Informations :** {len(lint_result.issues)}",
        ]
        
        # Erreurs
        if lint_result.errors:
            lines.append("")
            lines.append("## ❌ Erreurs Critiques")
            for i, error in enumerate(lint_result.errors, 1):
                lines.append(f"\n{i}. **{error.get('message', 'Erreur inconnue')}**")
                lines.append(f"   - **Type :** {error.get('type', 'unknown')}")
                if 'file' in error:
                    lines.append(f"   - **Fichier :** {error['file']}")
                if 'files' in error:
                    lines.append(f"   - **Fichiers :** {', '.join(error['files'])}")
        
        # Avertissements
        if lint_result.warnings:
            lines.append("")
            lines.append("## ⚠️ Avertissements")
            for i, warning in enumerate(lint_result.warnings, 1):
                lines.append(f"\n{i}. **{warning.get('message', 'Avertissement inconnu')}**")
                lines.append(f"   - **Type :** {warning.get('type', 'unknown')}")
                if 'file' in warning:
                    lines.append(f"   - **Fichier :** {warning['file']}")
        
        # Informations
        if lint_result.issues:
            lines.append("")
            lines.append("## ℹ️ Informations")
            for i, issue in enumerate(lint_result.issues, 1):
                lines.append(f"\n{i}. **{issue.get('message', 'Information inconnue')}**")
                lines.append(f"   - **Type :** {issue.get('type', 'unknown')}")
                if 'file' in issue:
                    lines.append(f"   - **Fichier :** {issue['file']}")
        
        # Résumé
        lines.append("")
        lines.append("## Résumé")
        if lint_result.errors:
            status = "❌ Requiert attention urgente"
        elif lint_result.warnings:
            status = "⚠️ Requiert attention"
        else:
            status = "✅ Sain"
        lines.append(f"- **Statut global :** {status}")
        
        return "\n".join(lines)
    
    async def lint_and_fix(
        self,
        auto_fix: bool = False,
    ) -> Dict[str, Any]:
        """
        Linting avec correction automatique optionnelle.
        
        Args:
            auto_fix: Si True, corriger automatiquement les problèmes simples.
            
        Returns:
            Rapport de linting et correction.
        """
        report: Dict[str, Any] = {
            "lint_report": {},
            "fixes_applied": [],
            "fixes_failed": [],
            "success": False,
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            # Effectuer le linting
            lint_report = await self.execute(generate_report=False)
            report["lint_report"] = lint_report
            
            if not lint_report["result"]["success"]:
                return report
            
            # Appliquer les corrections automatiques
            if auto_fix:
                fixes = await self._apply_auto_fixes(lint_report["result"])
                report["fixes_applied"] = fixes["applied"]
                report["fixes_failed"] = fixes["failed"]
            
            report["success"] = True
            return report
            
        except Exception as e:
            report["error"] = str(e)
            report["success"] = False
            return report
    
    async def _apply_auto_fixes(self, lint_result) -> Dict[str, List[str]]:
        """
        Appliquer les corrections automatiques.
        
        Args:
            lint_result: Résultat du linting.
            
        Returns:
            Dictionnaire avec les corrections appliquées et échouées.
        """
        applied = []
        failed = []
        
        # Corriger les problèmes simples
        for issue in lint_result.issues + lint_result.warnings:
            issue_type = issue.get("type", "")
            
            try:
                if issue_type == "broken_link":
                    # Corriger les liens brisés
                    file_path = Path(issue.get("file", ""))
                    if file_path.exists():
                        fixed = self._fix_broken_link(file_path, issue.get("message", ""))
                        if fixed:
                            applied.append(f"Fixed broken link in {file_path}")
                        else:
                            failed.append(f"Failed to fix broken link in {file_path}")
                
                elif issue_type == "missing_reference":
                    # Ajouter les références manquantes
                    file_path = Path(issue.get("file", ""))
                    if file_path.exists():
                        fixed = self._add_missing_reference(file_path, issue.get("message", ""))
                        if fixed:
                            applied.append(f"Added missing reference in {file_path}")
                        else:
                            failed.append(f"Failed to add missing reference in {file_path}")
                
                elif issue_type == "invalid_tag":
                    # Corriger les tags invalides
                    file_path = Path(issue.get("file", ""))
                    if file_path.exists():
                        fixed = self._fix_invalid_tag(file_path, issue.get("message", ""))
                        if fixed:
                            applied.append(f"Fixed invalid tag in {file_path}")
                        else:
                            failed.append(f"Failed to fix invalid tag in {file_path}")
                
            except Exception as e:
                failed.append(f"Error fixing {issue_type} in {issue.get('file', 'unknown')}: {str(e)}")
        
        return {"applied": applied, "failed": failed}
    
    def _fix_broken_link(self, file_path: Path, message: str) -> bool:
        """
        Corriger un lien brisé.
        
        Args:
            file_path: Chemin du fichier.
            message: Message d'erreur.
            
        Returns:
            True si corrigé.
        """
        try:
            # Lire le contenu
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extraire le lien brisé
            import re
            match = re.search(r'\[\[(.*?)\]\]', message)
            if not match:
                return False
            
            broken_link = match.group(1)
            
            # Essayer de trouver une correspondance
            # (Implémentation simplifiée - à améliorer)
            fixed_link = self._find_similar_page(broken_link)
            
            if fixed_link:
                # Remplacer le lien
                fixed_content = content.replace(f"[[{broken_link}]]", f"[[{fixed_link}]]")
                
                # Sauvegarder
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(fixed_content)
                
                return True
            
            return False
            
        except Exception:
            return False
    
    def _find_similar_page(self, broken_link: str) -> Optional[str]:
        """
        Trouver une page similaire.
        
        Args:
            broken_link: Lien brisé.
            
        Returns:
            Nom de la page similaire ou None.
        """
        # Implémentation simplifiée
        # Dans une implémentation complète, on utiliserait la similarité sémantique
        
        # Vérifier si le fichier existe avec une autre extension
        possible_extensions = [".md", ""]
        for ext in possible_extensions:
            possible_path = self.vault_path / "wiki" / f"{broken_link}{ext}"
            if possible_path.exists():
                return broken_link
        
        # Vérifier dans les sous-dossiers
        for subdir in ["entities", "concepts", "sources", "comparisons", "synthesis"]:
            possible_path = self.vault_path / "wiki" / subdir / f"{broken_link}.md"
            if possible_path.exists():
                return f"{subdir}/{broken_link}"
        
        return None
    
    def _add_missing_reference(self, file_path: Path, message: str) -> bool:
        """
        Ajouter une référence manquante.
        
        Args:
            file_path: Chemin du fichier.
            message: Message d'erreur.
            
        Returns:
            True si corrigé.
        """
        # Implémentation à compléter
        return False
    
    def _fix_invalid_tag(self, file_path: Path, message: str) -> bool:
        """
        Corriger un tag invalide.
        
        Args:
            file_path: Chemin du fichier.
            message: Message d'erreur.
            
        Returns:
            True si corrigé.
        """
        # Implémentation à compléter
        return False
    
    def close(self) -> None:
        """Fermer les ressources."""
        self.wiki_engine.close()
        self.vault_manager.close()
