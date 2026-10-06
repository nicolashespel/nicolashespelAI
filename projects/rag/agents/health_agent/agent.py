"""
Health Agent - Agent de santé pour le système RAG Wiki.

Cet agent utilise:
- Mistral Small pour l'analyse
- Vérifications automatiques des index
- Détection des problèmes de cohérence
- Génération de rapports détaillés
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .validator import ContentValidator
from .analyzer import SystemAnalyzer

logger = logging.getLogger(__name__)


class HealthAgent:
    """
    Agent de santé pour le système RAG Wiki.
    
    Cet agent est responsable de:
    1. La validation mécanique (frontmatter, liens, références)
    2. La validation sémantique (contradictions, orphelins, obsolète)
    3. La vérification de la santé globale
    4. La génération de rapports détaillés
    
    Commande OpenWebUI: `/health`
    """
    
    def __init__(
        self,
        vault_path: Union[Path, str],
        api_key: Optional[str] = None,
        config_path: Optional[str] = None,
    ) -> None:
        """
        Initialiser l'agent de santé.
        
        Args:
            vault_path: Chemin du vault.
            api_key: Clé API Mistral.
            config_path: Chemin du fichier de configuration.
        """
        self.vault_path = Path(vault_path) if isinstance(vault_path, str) else vault_path
        self.vault_path.mkdir(parents=True, exist_ok=True)
        
        # Charger la configuration
        self.config = self._load_config(config_path)
        
        # Initialiser les composants
        self.validator = ContentValidator(
            check_frontmatter=self.config.get("check_frontmatter", True),
            check_links=self.config.get("check_links", True),
            check_references=self.config.get("check_references", True),
            check_types=self.config.get("check_types", True),
            check_tags=self.config.get("check_tags", True),
        )
        
        self.analyzer = SystemAnalyzer(
            detect_contradictions=self.config.get("detect_contradictions", True),
            detect_orphans=self.config.get("detect_orphans", True),
            detect_obsolete=self.config.get("detect_obsolete", True),
            check_coverage=self.config.get("check_coverage", True),
        )
        
        # Chemins
        self.wiki_dir = self.vault_path / "wiki"
        self.log_file = self.wiki_dir / "log.md"
        
        # Historique
        self.history: List[Dict[str, Any]] = []
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Charger la configuration."""
        default_config = {
            "check_frontmatter": True,
            "check_links": True,
            "check_references": True,
            "check_types": True,
            "check_tags": True,
            "detect_contradictions": True,
            "detect_orphans": True,
            "detect_obsolete": True,
            "check_coverage": True,
            "auto_fix": False,
        }
        
        # Charger depuis le fichier si spécifié
        if config_path:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                default_config.update(file_config.get("health_agent", {}))
        
        # Charger depuis le vault
        vault_config = self.vault_path / "configs" / "agents_config.json"
        if vault_config.exists():
            with open(vault_config, "r", encoding="utf-8") as f:
                file_config = json.load(f)
            agent_config = file_config.get("agents", {}).get("health_agent", {})
            default_config.update(agent_config.get("features", {}).get("validation", {}))
            default_config.update(agent_config.get("features", {}).get("analysis", {}))
        
        return default_config
    
    def _get_all_pages(self) -> List[Path]:
        """Obtenir toutes les pages wiki."""
        if not self.wiki_dir.exists():
            return []
        
        pages = [
            f for f in self.wiki_dir.glob("**/*.md")
            if f.is_file() and not f.name.startswith(".")
        ]
        
        return pages
    
    def _log_operation(
        self,
        operation: str,
        details: Dict[str, Any],
    ) -> None:
        """Logger une opération dans log.md."""
        log_entry = f"""- [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{operation.upper()}]
  {json.dumps(details, indent=2, ensure_ascii=False)}
  - status: success
"""
        
        if not self.log_file.exists():
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write("# Log des Opérations\n\n")
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
        
        logger.info(f"Opération loggée: {operation}")
    
    async def health(
        self,
        vault: Optional[Union[Path, str]] = None,
        checks: str = "all",
        fix: bool = False,
        format: str = "full",
    ) -> Dict[str, Any]:
        """
        Vérifier la santé du système RAG.
        
        Args:
            vault: Chemin du vault à analyser (par défaut: celui de l'agent).
            checks: Types de vérifications (all, validation, analysis, statistics, moderation).
            fix: Corriger automatiquement les problèmes.
            format: Format du rapport (full, summary, json).
            
        Returns:
            Rapport de santé.
        """
        start_time = datetime.now()
        
        # Définir le vault si spécifié
        if vault:
            self.vault_path = Path(vault) if isinstance(vault, str) else vault
            self.wiki_dir = self.vault_path / "wiki"
        
        # Initialiser le rapport
        report: Dict[str, Any] = {
            "success": True,
            "start_time": start_time.isoformat(),
            "vault_path": str(self.vault_path),
            "checks": checks,
            "fix": fix,
            "format": format,
            "validation": {},
            "analysis": {},
            "statistics": {},
            "moderation": {},
            "issues": [],
            "warnings": [],
            "errors": [],
        }
        
        try:
            # Obtenir toutes les pages
            all_pages = self._get_all_pages()
            report["statistics"]["total_pages"] = len(all_pages)
            
            # Exécuter les vérifications
            if checks in ["all", "validation"]:
                report["validation"] = self._run_validation(all_pages, fix)
            
            if checks in ["all", "analysis"]:
                report["analysis"] = self._run_analysis(all_pages)
            
            if checks in ["all", "statistics"]:
                report["statistics"] = self._run_statistics(all_pages)
            
            if checks in ["all", "moderation"]:
                report["moderation"] = self._run_moderation(all_pages)
            
            # Compiler les problèmes
            report["issues"] = self._compile_issues(report)
            report["warnings"] = self._compile_warnings(report)
            report["errors"] = self._compile_errors(report)
            
            # Calculer le statut global
            report["status"] = self._calculate_status(report)
            
            # Calculer la durée
            report["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            report["end_time"] = datetime.now().isoformat()
            
            # Logger l'opération
            self._log_operation("health", {
                "checks": checks,
                "issues_found": len(report["issues"]),
                "warnings_found": len(report["warnings"]),
                "errors_found": len(report["errors"]),
                "status": report["status"],
            })
            
            # Ajouter à l'historique
            self.history.append(report)
            
            logger.info(
                f"Vérification terminée: {len(report['issues'])} problèmes, "
                f"{len(report['warnings'])} avertissements, "
                f"statut: {report['status']}"
            )
            
            # Formater le rapport selon le format demandé
            if format == "json":
                return report
            elif format == "summary":
                return self._format_summary(report)
            else:  # full
                return self._format_full(report)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification: {e}")
            return {
                "success": False,
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
            }
    
    def _run_validation(
        self,
        pages: List[Path],
        fix: bool,
    ) -> Dict[str, Any]:
        """Exécuter la validation mécanique."""
        result = self.validator.validate_all(pages)
        
        if fix:
            # Appliquer les corrections automatiques
            self._apply_fixes(pages, result)
        
        return result
    
    def _run_analysis(
        self,
        pages: List[Path],
    ) -> Dict[str, Any]:
        """Exécuter l'analyse sémantique."""
        return self.analyzer.analyze(self.vault_path, pages)
    
    def _run_statistics(
        self,
        pages: List[Path],
    ) -> Dict[str, Any]:
        """Exécuter les statistiques."""
        statistics = {
            "total_pages": len(pages),
            "by_type": {},
            "by_directory": {},
            "index_stats": {},
        }
        
        # Statistiques par type
        for page in pages:
            page_type = self._get_page_type(page)
            if page_type not in statistics["by_type"]:
                statistics["by_type"][page_type] = 0
            statistics["by_type"][page_type] += 1
        
        # Statistiques par dossier
        for page in pages:
            relative_path = page.relative_to(self.wiki_dir)
            directory = str(relative_path.parent) if relative_path.parent != Path(".") else "root"
            
            if directory not in statistics["by_directory"]:
                statistics["by_directory"][directory] = 0
            statistics["by_directory"][directory] += 1
        
        # Statistiques de l'index
        index_path = self.wiki_dir / "index.md"
        if index_path.exists():
            statistics["index_stats"]["exists"] = True
            statistics["index_stats"]["size"] = index_path.stat().st_size
        else:
            statistics["index_stats"]["exists"] = False
        
        return statistics
    
    def _run_moderation(
        self,
        pages: List[Path],
    ) -> Dict[str, Any]:
        """Exécuter la modération."""
        # Implémentation simplifiée
        # Dans une implémentation complète, utiliser Shieldstral
        
        moderation = {
            "blocked_content": [],
            "flagged_content": [],
            "safe": True,
        }
        
        # Liste de mots à bloquer
        block_list = [
            "hate", "harassment", "violence", "self-harm",
            "sexual", "illegal", "personal_data",
        ]
        
        for page in pages:
            try:
                with open(page, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
            
            content_lower = content.lower()
            for word in block_list:
                if word in content_lower:
                    moderation["flagged_content"].append({
                        "page": str(page),
                        "issue": f"Contenu potentiellement inapproprié: {word}",
                        "severity": "high",
                    })
                    moderation["safe"] = False
        
        return moderation
    
    def _get_page_type(self, page: Path) -> str:
        """Obtenir le type d'une page."""
        try:
            with open(page, "r", encoding="utf-8") as f:
                content = f.read()
            
            if content.startswith("---"):
                end_index = content.find("---", 3)
                if end_index != -1:
                    import yaml
                    try:
                        frontmatter = yaml.safe_load(content[3:end_index])
                        return frontmatter.get("type", "unknown")
                    except Exception:
                        pass
        except Exception:
            pass
        
        return "unknown"
    
    def _apply_fixes(
        self,
        pages: List[Path],
        validation_result: Dict[str, Any],
    ) -> None:
        """Appliquer les corrections automatiques."""
        # Implémentation simplifiée
        # Dans une implémentation complète, corriger les problèmes détectés
        
        for result in validation_result.get("results", []):
            if not result.get("success", True):
                errors = result.get("errors", [])
                for error in errors:
                    logger.warning(f"Correction automatique non implémentée: {error}")
    
    def _compile_issues(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compiler tous les problèmes."""
        issues = []
        
        # Validation
        validation = report.get("validation", {})
        for result in validation.get("results", []):
            for error in result.get("errors", []):
                issues.append({
                    "type": "validation",
                    "severity": "error",
                    "message": error,
                    "file": result.get("file", "unknown"),
                })
        
        # Analyse
        analysis = report.get("analysis", {})
        for contradiction in analysis.get("contradictions", []):
            issues.append({
                "type": "analysis",
                "severity": contradiction.get("severity", "high"),
                "message": f"Contradiction détectée: {contradiction.get('subject', 'unknown')}",
                "files": [contradiction.get("page1", ""), contradiction.get("page2", "")],
            })
        
        for orphan in analysis.get("orphans", []):
            issues.append({
                "type": "analysis",
                "severity": orphan.get("severity", "medium"),
                "message": f"Page orpheline: {orphan.get('page', 'unknown')}",
            })
        
        for obsolete in analysis.get("obsolete", []):
            issues.append({
                "type": "analysis",
                "severity": obsolete.get("severity", "low"),
                "message": f"Information obsolète: {obsolete.get('page', 'unknown')}",
            })
        
        # Modération
        moderation = report.get("moderation", {})
        for flagged in moderation.get("flagged_content", []):
            issues.append({
                "type": "moderation",
                "severity": flagged.get("severity", "high"),
                "message": flagged.get("issue", "unknown"),
                "file": flagged.get("page", "unknown"),
            })
        
        return issues
    
    def _compile_warnings(self, report: Dict[str, Any]) -> List[str]:
        """Compiler tous les avertissements."""
        warnings = []
        
        # Validation
        validation = report.get("validation", {})
        for result in validation.get("results", []):
            warnings.extend(result.get("warnings", []))
        
        # Statistiques
        statistics = report.get("statistics", {})
        if not statistics.get("index_stats", {}).get("exists", True):
            warnings.append("Le fichier index.md n'existe pas")
        
        return warnings
    
    def _compile_errors(self, report: Dict[str, Any]) -> List[str]:
        """Compiler toutes les erreurs."""
        errors = []
        
        # Vérifier si des vérifications ont échoué
        if not report.get("validation", {}).get("success", True):
            errors.append("La validation mécanique a échoué")
        
        return errors
    
    def _calculate_status(self, report: Dict[str, Any]) -> str:
        """Calculer le statut global."""
        issues = report.get("issues", [])
        warnings = report.get("warnings", [])
        errors = report.get("errors", [])
        
        if errors:
            return "critical"
        elif issues:
            return "warning"
        elif warnings:
            return "info"
        else:
            return "healthy"
    
    def _format_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Formater le rapport en résumé."""
        summary = {
            "success": report.get("success", True),
            "status": report.get("status", "unknown"),
            "vault_path": report.get("vault_path", ""),
            "total_pages": report.get("statistics", {}).get("total_pages", 0),
            "issues_count": len(report.get("issues", [])),
            "warnings_count": len(report.get("warnings", [])),
            "errors_count": len(report.get("errors", [])),
            "duration_seconds": report.get("duration_seconds", 0),
            "summary": self._generate_summary_text(report),
        }
        
        return summary
    
    def _format_full(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Formater le rapport complet."""
        full = report.copy()
        full["summary"] = self._generate_summary_text(report)
        full["report"] = self._generate_full_report_text(report)
        return full
    
    def _generate_summary_text(self, report: Dict[str, Any]) -> str:
        """Générer un texte de résumé."""
        status = report.get("status", "unknown")
        total_pages = report.get("statistics", {}).get("total_pages", 0)
        issues = len(report.get("issues", []))
        warnings = len(report.get("warnings", []))
        
        status_emoji = {
            "healthy": "✅",
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "❌",
        }
        
        return (
            f"{status_emoji.get(status, '❓')} **Statut:** {status}\n"
            f"📄 **Pages:** {total_pages}\n"
            f"⚠️ **Problèmes:** {issues}\n"
            f"ℹ️ **Avertissements:** {warnings}\n"
        )
    
    def _generate_full_report_text(self, report: Dict[str, Any]) -> str:
        """Générer un rapport complet en texte."""
        lines = []
        
        lines.append("# Rapport de Santé du Système RAG")
        lines.append("")
        lines.append(f"**Date:** {report.get('start_time', '')}")
        lines.append(f"**Durée:** {report.get('duration_seconds', 0):.2f} secondes")
        lines.append("")
        
        # Statut global
        status = report.get("status", "unknown")
        status_emoji = {
            "healthy": "✅",
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "❌",
        }
        lines.append(f"## Statut Global {status_emoji.get(status, '❓')}")
        lines.append(f"**Statut:** {status}")
        lines.append("")
        
        # Statistiques
        statistics = report.get("statistics", {})
        lines.append("## Statistiques")
        lines.append(f"- **Total Pages:** {statistics.get('total_pages', 0)}")
        lines.append("")
        
        # Par type
        by_type = statistics.get("by_type", {})
        if by_type:
            lines.append("### Pages par Type")
            for page_type, count in by_type.items():
                lines.append(f"- **{page_type}:** {count}")
            lines.append("")
        
        # Par dossier
        by_directory = statistics.get("by_directory", {})
        if by_directory:
            lines.append("### Pages par Dossier")
            for directory, count in by_directory.items():
                lines.append(f"- **{directory}:** {count}")
            lines.append("")
        
        # Problèmes
        issues = report.get("issues", [])
        if issues:
            lines.append("## Problèmes Détectés")
            for issue in issues:
                severity_emoji = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢",
                }
                lines.append(f"{severity_emoji.get(issue.get('severity', ''), '⚪')} **{issue.get('type', 'unknown')}** - {issue.get('message', '')}")
            lines.append("")
        
        # Avertissements
        warnings = report.get("warnings", [])
        if warnings:
            lines.append("## Avertissements")
            for warning in warnings:
                lines.append(f"- {warning}")
            lines.append("")
        
        # Validation
        validation = report.get("validation", {})
        if validation:
            lines.append("## Validation Mécanique")
            lines.append(f"- **Pages vérifiées:** {validation.get('total_files', 0)}")
            lines.append(f"- **Pages avec erreurs:** {validation.get('files_with_errors', 0)}")
            lines.append(f"- **Pages avec avertissements:** {validation.get('files_with_warnings', 0)}")
            lines.append(f"- **Total erreurs:** {validation.get('total_errors', 0)}")
            lines.append(f"- **Total avertissements:** {validation.get('total_warnings', 0)}")
            lines.append("")
        
        # Analyse
        analysis = report.get("analysis", {})
        if analysis:
            lines.append("## Analyse Sémantique")
            lines.append(f"- **Contradictions:** {len(analysis.get('contradictions', []))}")
            lines.append(f"- **Pages orphelines:** {len(analysis.get('orphans', []))}")
            lines.append(f"- **Informations obsolètes:** {len(analysis.get('obsolete', []))}")
            lines.append(f"- **Score de couverture:** {analysis.get('coverage', {}).get('score', 0):.2f}")
            lines.append("")
        
        # Recommandations
        lines.append("## Recommandations")
        if issues:
            lines.append("- Corriger les problèmes critiques")
            lines.append("- Vérifier les contradictions détectées")
            lines.append("- Mettre à jour les informations obsolètes")
        else:
            lines.append("✅ Aucun problème détecté! Le système est en bonne santé.")
        
        return "\n".join(lines)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Obtenir l'historique des vérifications."""
        return self.history
    
    def clear_history(self) -> None:
        """Effacer l'historique."""
        self.history = []
    
    async def close(self) -> None:
        """Fermer les ressources."""
        pass


# Instance globale pour OpenWebUI
_health_agent: Optional[HealthAgent] = None


def get_health_agent(
    vault_path: Union[Path, str] = Path("~/vaults/knowledge_base").expanduser(),
    api_key: Optional[str] = None,
) -> HealthAgent:
    """Obtenir une instance globale de l'agent de santé."""
    global _health_agent
    
    if _health_agent is None:
        _health_agent = HealthAgent(vault_path, api_key)
    
    return _health_agent


def reset_health_agent() -> None:
    """Réinitialiser l'instance globale."""
    global _health_agent
    _health_agent = None
