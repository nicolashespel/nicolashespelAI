"""
Pipeline de linting pour le système RAG Wiki.

Ce module contient la classe LintPipeline qui gère le processus complet
de linting du vault.
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..types import (
    LintResult,
    Page,
)
from ..storage import VaultManager
from ..indexes import IndexManager
from .config import WikiConfig
from .prompts import WIKI_LINTER_PROMPT


class LintPipeline:
    """
    Pipeline de linting pour le système RAG Wiki.
    
    Ce pipeline gère le processus complet de linting :
    1. Vérifications mécaniques (frontmatter, liens, références)
    2. Vérifications sémantiques (contradictions, orphelins)
    3. Vérifications de santé globale
    4. Génération du rapport
    """
    
    def __init__(
        self,
        vault_manager: VaultManager,
        index_manager: IndexManager,
        config: WikiConfig,
    ) -> None:
        """
        Initialiser le pipeline de linting.
        
        Args:
            vault_manager: Gestionnaire du vault.
            index_manager: Gestionnaire des index.
            config: Configuration du wiki.
        """
        self.vault_manager = vault_manager
        self.index_manager = index_manager
        self.config = config
    
    async def lint(
        self,
        check_mechanical: bool = True,
        check_semantic: bool = True,
        check_health: bool = True,
    ) -> LintResult:
        """
        Effectuer un linting du vault.
        
        Args:
            check_mechanical: Vérifier les aspects mécaniques.
            check_semantic: Vérifier les aspects sémantiques.
            check_health: Vérifier la santé globale.
            
        Returns:
            Résultat du linting.
        """
        start_time = time.time()
        
        issues: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        
        try:
            # Étape 1: Vérifications mécaniques
            if check_mechanical:
                mechanical_issues, mechanical_warnings, mechanical_errors = await self._check_mechanical()
                issues.extend(mechanical_issues)
                warnings.extend(mechanical_warnings)
                errors.extend(mechanical_errors)
            
            # Étape 2: Vérifications sémantiques
            if check_semantic:
                semantic_issues, semantic_warnings, semantic_errors = await self._check_semantic()
                issues.extend(semantic_issues)
                warnings.extend(semantic_warnings)
                errors.extend(semantic_errors)
            
            # Étape 3: Vérifications de santé
            if check_health:
                health_issues, health_warnings, health_errors = await self._check_health()
                issues.extend(health_issues)
                warnings.extend(health_warnings)
                errors.extend(health_errors)
            
            # Générer le rapport
            report = self._generate_report(
                issues=issues,
                warnings=warnings,
                errors=errors,
                duration=time.time() - start_time,
            )
            
            return LintResult(
                success=True,
                issues=issues,
                warnings=warnings,
                errors=errors,
                duration_seconds=time.time() - start_time,
            )
            
        except Exception as e:
            return LintResult(
                success=False,
                issues=[],
                warnings=[],
                errors=[{"type": "internal_error", "message": str(e)}],
                duration_seconds=time.time() - start_time,
                error=str(e),
            )
    
    async def _check_mechanical(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Effectuer les vérifications mécaniques.
        
        Returns:
            Tuple avec (issues, warnings, errors).
        """
        issues: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        
        # Vérifier tous les fichiers dans wiki/
        all_pages = self.vault_manager.get_all_pages()
        
        for page_path in all_pages:
            # 1. Vérifier le frontmatter
            frontmatter_issues = self._check_frontmatter(page_path)
            errors.extend(frontmatter_issues)
            
            # 2. Vérifier les liens
            link_issues = self._check_links(page_path)
            errors.extend(link_issues)
            
            # 3. Vérifier les références
            reference_issues = self._check_references(page_path)
            warnings.extend(reference_issues)
            
            # 4. Vérifier les types
            type_issues = self._check_types(page_path)
            errors.extend(type_issues)
            
            # 5. Vérifier les tags
            tag_issues = self._check_tags(page_path)
            warnings.extend(tag_issues)
        
        return issues, warnings, errors
    
    def _check_frontmatter(self, page_path: Path) -> List[Dict[str, Any]]:
        """
        Vérifier le frontmatter d'une page.
        
        Args:
            page_path: Chemin de la page.
            
        Returns:
            Liste d'erreurs.
        """
        issues = []
        
        try:
            page = self.vault_manager.get_page(page_path)
            if page is None:
                issues.append({
                    "type": "frontmatter_missing",
                    "file": str(page_path),
                    "message": "Fichier introuvable",
                    "severity": "error",
                })
                return issues
            
            # Vérifier que tous les champs requis sont présents
            required_fields = ["type", "name", "description", "created", "updated"]
            for field in required_fields:
                if not hasattr(page, field) or getattr(page, field) is None:
                    issues.append({
                        "type": "frontmatter_incomplete",
                        "file": str(page_path),
                        "message": f"Champ requis manquant: {field}",
                        "severity": "error",
                    })
            
        except Exception as e:
            issues.append({
                "type": "frontmatter_error",
                "file": str(page_path),
                "message": f"Erreur lors de la vérification du frontmatter: {str(e)}",
                "severity": "error",
            })
        
        return issues
    
    def _check_links(self, page_path: Path) -> List[Dict[str, Any]]:
        """
        Vérifier les liens dans une page.
        
        Args:
            page_path: Chemin de la page.
            
        Returns:
            Liste d'erreurs.
        """
        issues = []
        
        try:
            content = self.vault_manager.read_page_content(page_path)
            if content is None:
                return issues
            
            # Extraire les liens wiki [[...]]
            import re
            links = re.findall(r'\[\[([^\]]+)\]\]', content)
            
            for link in links:
                # Construire le chemin potentiel
                link_path = self._resolve_link(link, page_path)
                
                # Vérifier si le fichier existe
                if not link_path.exists():
                    issues.append({
                        "type": "broken_link",
                        "file": str(page_path),
                        "message": f"Lien brisé vers: [[{link}]]",
                        "severity": "error",
                        "line": self._find_line_number(content, f"[[{link}]]"),
                    })
            
        except Exception as e:
            issues.append({
                "type": "link_check_error",
                "file": str(page_path),
                "message": f"Erreur lors de la vérification des liens: {str(e)}",
                "severity": "error",
            })
        
        return issues
    
    def _resolve_link(self, link: str, current_page_path: Path) -> Path:
        """
        Résoudre un lien wiki en chemin de fichier.
        
        Args:
            link: Lien wiki.
            current_page_path: Chemin de la page actuelle.
            
        Returns:
            Chemin résolu.
        """
        # Simple resolution pour l'instant
        # Dans une implémentation complète, cela gérera les liens relatifs
        
        # Si le lien contient un chemin
        if "/" in link:
            return self.config.wiki_path / link.replace("/", "")
        else:
            # Chercher dans tous les dossiers
            for page_type in ["entities", "concepts", "sources", "comparisons", "synthesis"]:
                potential_path = self.config.wiki_path / page_type / f"{link}.md"
                if potential_path.exists():
                    return potential_path
            
            # Retourner un chemin par défaut
            return self.config.wiki_path / f"{link}.md"
    
    def _find_line_number(self, content: str, text: str) -> int:
        """
        Trouver le numéro de ligne d'un texte dans un contenu.
        
        Args:
            content: Contenu complet.
            text: Texte à chercher.
            
        Returns:
            Numéro de ligne (1-based).
        """
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if text in line:
                return i
        return -1
    
    def _check_references(self, page_path: Path) -> List[Dict[str, Any]]:
        """
        Vérifier les références dans une page.
        
        Args:
            page_path: Chemin de la page.
            
        Returns:
            Liste d'avertissements.
        """
        warnings = []
        
        try:
            page = self.vault_manager.get_page(page_path)
            if page is None:
                return warnings
            
            # Vérifier que toutes les sources existent
            for source in page.sources:
                source_path = self.config.wiki_path / "sources" / f"{source}.md"
                if not source_path.exists():
                    warnings.append({
                        "type": "missing_reference",
                        "file": str(page_path),
                        "message": f"Source manquante: {source}",
                        "severity": "warning",
                    })
            
        except Exception as e:
            warnings.append({
                "type": "reference_check_error",
                "file": str(page_path),
                "message": f"Erreur lors de la vérification des références: {str(e)}",
                "severity": "warning",
            })
        
        return warnings
    
    def _check_types(self, page_path: Path) -> List[Dict[str, Any]]:
        """
        Vérifier le type d'une page.
        
        Args:
            page_path: Chemin de la page.
            
        Returns:
            Liste d'erreurs.
        """
        issues = []
        
        try:
            page = self.vault_manager.get_page(page_path)
            if page is None:
                return issues
            
            # Vérifier que le type est valide
            valid_types = ["entity", "concept", "source", "comparison", "synthesis", "index", "log"]
            if page.type not in valid_types:
                issues.append({
                    "type": "invalid_type",
                    "file": str(page_path),
                    "message": f"Type de page invalide: {page.type}",
                    "severity": "error",
                })
            
            # Vérifier que le type correspond au chemin
            expected_type = self._infer_type_from_path(page_path)
            if expected_type and page.type != expected_type:
                issues.append({
                    "type": "type_mismatch",
                    "file": str(page_path),
                    "message": f"Type de page ({page.type}) ne correspond pas au chemin ({expected_type})",
                    "severity": "error",
                })
            
        except Exception as e:
            issues.append({
                "type": "type_check_error",
                "file": str(page_path),
                "message": f"Erreur lors de la vérification du type: {str(e)}",
                "severity": "error",
            })
        
        return issues
    
    def _infer_type_from_path(self, page_path: Path) -> Optional[str]:
        """
        Déduire le type de page à partir du chemin.
        
        Args:
            page_path: Chemin de la page.
            
        Returns:
            Type de page ou None.
        """
        relative_path = page_path.relative_to(self.config.wiki_path)
        parts = relative_path.parts
        
        if len(parts) >= 2:
            if parts[0] == "entities":
                return "entity"
            elif parts[0] == "concepts":
                return "concept"
            elif parts[0] == "sources":
                return "source"
            elif parts[0] == "comparisons":
                return "comparison"
            elif parts[0] == "synthesis":
                return "synthesis"
            elif parts[0] == "index.md":
                return "index"
            elif parts[0] == "log.md":
                return "log"
        
        return None
    
    def _check_tags(self, page_path: Path) -> List[Dict[str, Any]]:
        """
        Vérifier les tags d'une page.
        
        Args:
            page_path: Chemin de la page.
            
        Returns:
            Liste d'avertissements.
        """
        warnings = []
        
        try:
            page = self.vault_manager.get_page(page_path)
            if page is None:
                return warnings
            
            # Vérifier que les tags sont valides
            for tag in page.tags:
                if not isinstance(tag, str) or not tag.strip():
                    warnings.append({
                        "type": "invalid_tag",
                        "file": str(page_path),
                        "message": f"Tag invalide: {tag}",
                        "severity": "warning",
                    })
                elif len(tag) > 50:
                    warnings.append({
                        "type": "long_tag",
                        "file": str(page_path),
                        "message": f"Tag trop long: {tag}",
                        "severity": "warning",
                    })
            
            # Vérifier les doublons
            if len(page.tags) != len(set(page.tags)):
                warnings.append({
                    "type": "duplicate_tags",
                    "file": str(page_path),
                    "message": "Tags dupliqués détectés",
                    "severity": "warning",
                })
            
        except Exception as e:
            warnings.append({
                "type": "tag_check_error",
                "file": str(page_path),
                "message": f"Erreur lors de la vérification des tags: {str(e)}",
                "severity": "warning",
            })
        
        return warnings
    
    async def _check_semantic(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Effectuer les vérifications sémantiques.
        
        Returns:
            Tuple avec (issues, warnings, errors).
        """
        issues: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        
        # 1. Détecter les orphelins
        orphan_issues = self._check_orphans()
        warnings.extend(orphan_issues)
        
        # 2. Détecter les contradictions
        contradiction_issues = await self._check_contradictions()
        errors.extend(contradiction_issues)
        
        # 3. Détecter les affirmations obsolètes
        stale_issues = self._check_stale_claims()
        warnings.extend(stale_issues)
        
        # 4. Détecter les lacunes de références
        reference_gap_issues = self._check_reference_gaps()
        issues.extend(reference_gap_issues)
        
        return issues, warnings, errors
    
    def _check_orphans(self) -> List[Dict[str, Any]]:
        """
        Détecter les pages orphelines.
        
        Returns:
            Liste d'avertissements.
        """
        warnings = []
        
        # Obtenir toutes les pages
        all_pages = self.vault_manager.get_all_pages()
        
        # Obtenir toutes les références
        all_references = set()
        for page_path in all_pages:
            page = self.vault_manager.get_page(page_path)
            if page:
                for related in page.related:
                    all_references.add(related)
                for source in page.sources:
                    all_references.add(source)
        
        # Trouver les pages qui ne sont pas référencées
        for page_path in all_pages:
            page_name = page_path.stem
            if page_name not in all_references:
                # Exclure index.md et log.md
                if page_name not in ["index", "log"]:
                    warnings.append({
                        "type": "orphan_page",
                        "file": str(page_path),
                        "message": f"Page orpheline: {page_name}",
                        "severity": "warning",
                    })
        
        return warnings
    
    async def _check_contradictions(self) -> List[Dict[str, Any]]:
        """
        Détecter les contradictions entre les pages.
        
        Returns:
            Liste d'erreurs.
        """
        errors = []
        
        # Obtenir toutes les pages source
        source_pages = self.vault_manager.get_pages_by_type("source")
        
        # Comparer les sources par paires
        for i, source_path_1 in enumerate(source_pages):
            for source_path_2 in source_pages[i+1:]:
                contradictions = await self._compare_sources(source_path_1, source_path_2)
                if contradictions:
                    errors.append({
                        "type": "contradiction",
                        "files": [str(source_path_1), str(source_path_2)],
                        "message": f"Contradictions détectées: {', '.join(contradictions)}",
                        "severity": "error",
                    })
        
        return errors
    
    async def _compare_sources(
        self,
        source_path_1: Path,
        source_path_2: Path,
    ) -> List[str]:
        """
        Comparer deux sources pour détecter les contradictions.
        
        Args:
            source_path_1: Chemin de la première source.
            source_path_2: Chemin de la deuxième source.
            
        Returns:
            Liste de contradictions.
        """
        # Implémentation simplifiée
        # Dans une implémentation complète, cela utiliserait le LLM pour détecter les contradictions
        
        contradictions = []
        
        try:
            source_1 = self.vault_manager.get_page(source_path_1)
            source_2 = self.vault_manager.get_page(source_path_2)
            
            if source_1 and source_2:
                # Comparaison basique des résumés
                summary_1 = source_1.description.lower()
                summary_2 = source_2.description.lower()
                
                # Détecter les négations
                if "not" in summary_1 and "not" not in summary_2:
                    contradictions.append("Affirmation vs négation")
                elif "not" in summary_2 and "not" not in summary_1:
                    contradictions.append("Affirmation vs négation")
                
                # Détecter les opposés
                opposites = [
                    ("good", "bad"),
                    ("effective", "ineffective"),
                    ("better", "worse"),
                    ("increase", "decrease"),
                    ("proves", "disproves"),
                ]
                
                for word1, word2 in opposites:
                    if word1 in summary_1 and word2 in summary_2:
                        contradictions.append(f"Opposés détectés: {word1} vs {word2}")
                    elif word2 in summary_1 and word1 in summary_2:
                        contradictions.append(f"Opposés détectés: {word2} vs {word1}")
            
        except Exception:
            pass
        
        return contradictions
    
    def _check_stale_claims(self) -> List[Dict[str, Any]]:
        """
        Détecter les affirmations obsolètes.
        
        Returns:
            Liste d'avertissements.
        """
        warnings = []
        
        # Obtenir toutes les pages
        all_pages = self.vault_manager.get_all_pages()
        
        for page_path in all_pages:
            page = self.vault_manager.get_page(page_path)
            if page:
                # Vérifier si la page est ancienne
                if page.updated:
                    age_days = (datetime.now() - page.updated).days
                    if age_days > 365:  # Plus d'un an
                        warnings.append({
                            "type": "stale_page",
                            "file": str(page_path),
                            "message": f"Page potentiellement obsolète (dernière mise à jour: {page.updated.date()})",
                            "severity": "warning",
                        })
        
        return warnings
    
    def _check_reference_gaps(self) -> List[Dict[str, Any]]:
        """
        Détecter les lacunes de références croisées.
        
        Returns:
            Liste d'issues.
        """
        issues = []
        
        # Obtenir toutes les pages
        all_pages = self.vault_manager.get_all_pages()
        
        # Obtenir tous les tags
        all_tags = set()
        for page_path in all_pages:
            page = self.vault_manager.get_page(page_path)
            if page:
                all_tags.update(page.tags)
        
        # Pour chaque tag, vérifier si les pages avec ce tag sont liées
        for tag in all_tags:
            pages_with_tag = self.vault_manager.get_pages_by_tag(tag)
            
            # Vérifier les connexions
            for page_path_1 in pages_with_tag:
                page_1 = self.vault_manager.get_page(page_path_1)
                if page_1:
                    for page_path_2 in pages_with_tag:
                        if page_path_1 != page_path_2:
                            page_name_2 = page_path_2.stem
                            if page_name_2 not in page_1.related:
                                issues.append({
                                    "type": "reference_gap",
                                    "tag": tag,
                                    "files": [str(page_path_1), str(page_path_2)],
                                    "message": f"Lacune de référence entre pages avec tag '{tag}'",
                                    "severity": "info",
                                })
        
        return issues
    
    async def _check_health(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Effectuer les vérifications de santé globale.
        
        Returns:
            Tuple avec (issues, warnings, errors).
        """
        issues: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        
        # 1. Vérifier l'index
        index_issues = self._check_index_health()
        errors.extend(index_issues)
        
        # 2. Vérifier le log
        log_issues = self._check_log_health()
        warnings.extend(log_issues)
        
        # 3. Vérifier les performances
        performance_issues = self._check_performance()
        issues.extend(performance_issues)
        
        return issues, warnings, errors
    
    def _check_index_health(self) -> List[Dict[str, Any]]:
        """
        Vérifier la santé de l'index.
        
        Returns:
            Liste d'erreurs.
        """
        errors = []
        
        # Vérifier que index.md existe
        index_path = self.config.wiki_path / "index.md"
        if not index_path.exists():
            errors.append({
                "type": "missing_index",
                "file": str(index_path),
                "message": "Fichier index.md manquant",
                "severity": "error",
            })
            return errors
        
        # Vérifier que index.md est à jour
        index_page = self.vault_manager.get_page(index_path)
        if index_page:
            all_pages = self.vault_manager.get_all_pages()
            
            # Vérifier que toutes les pages sont listées
            pages_in_index = set()
            if "pages_by_type" in index_page.__dict__:
                for pages in index_page.pages_by_type.values():
                    pages_in_index.update(pages)
            
            all_page_names = {p.stem for p in all_pages if p != index_path}
            
            missing_pages = all_page_names - pages_in_index
            if missing_pages:
                errors.append({
                    "type": "incomplete_index",
                    "file": str(index_path),
                    "message": f"Pages manquantes dans l'index: {', '.join(sorted(missing_pages))}",
                    "severity": "error",
                })
        
        return errors
    
    def _check_log_health(self) -> List[Dict[str, Any]]:
        """
        Vérifier la santé du log.
        
        Returns:
            Liste d'avertissements.
        """
        warnings = []
        
        # Vérifier que log.md existe
        log_path = self.config.wiki_path / "log.md"
        if not log_path.exists():
            warnings.append({
                "type": "missing_log",
                "file": str(log_path),
                "message": "Fichier log.md manquant",
                "severity": "warning",
            })
            return warnings
        
        # Vérifier que log.md est valide
        log_page = self.vault_manager.get_page(log_path)
        if log_page:
            if not hasattr(log_page, "entries") or not log_page.entries:
                warnings.append({
                    "type": "empty_log",
                    "file": str(log_path),
                    "message": "Fichier log.md vide",
                    "severity": "warning",
                })
        
        return warnings
    
    def _check_performance(self) -> List[Dict[str, Any]]:
        """
        Vérifier les performances du vault.
        
        Returns:
            Liste d'issues.
        """
        issues = []
        
        # Obtenir les statistiques
        stats = self.vault_manager.get_vault_stats()
        
        # Vérifier la taille
        if stats.get("total_pages", 0) > 1000:
            issues.append({
                "type": "large_vault",
                "message": f"Vault très grand: {stats['total_pages']} pages",
                "severity": "info",
            })
        
        # Vérifier la distribution des types
        page_types = stats.get("pages_by_type", {})
        if page_types.get("source", 0) > 500:
            issues.append({
                "type": "many_sources",
                "message": f"Nombre élevé de sources: {page_types['source']}",
                "severity": "info",
            })
        
        return issues
    
    def _generate_report(
        self,
        issues: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]],
        errors: List[Dict[str, Any]],
        duration: float,
    ) -> str:
        """
        Générer un rapport de linting.
        
        Args:
            issues: Liste des issues.
            warnings: Liste des avertissements.
            errors: Liste des erreurs.
            duration: Durée de l'opération.
            
        Returns:
            Rapport formaté.
        """
        report = f"""# Rapport de Linting du Vault

**Date :** {datetime.now().strftime('%Y-%m-%d')}
**Heure :** {datetime.now().strftime('%H:%M:%S')}
**Durée :** {duration:.2f} secondes

## Statistiques
- **Pages vérifiées :** {len(issues) + len(warnings) + len(errors)}
- **Erreurs :** {len(errors)}
- **Avertissements :** {len(warnings)}
- **Informations :** {len(issues)}

## Erreurs Critiques ❌
"""
        
        if errors:
            for i, error in enumerate(errors, 1):
                report += f"\n{i}. **{error.get('message', 'Erreur inconnue')}**\n"
                report += f"   - **Type :** {error.get('type', 'unknown')}\n"
                if 'file' in error:
                    report += f"   - **Fichier :** {error['file']}\n"
                if 'files' in error:
                    report += f"   - **Fichiers :** {', '.join(error['files'])}\n"
                if 'line' in error:
                    report += f"   - **Ligne :** {error['line']}\n"
        else:
            report += "\nAucune erreur critique détectée.\n"
        
        report += "\n## Avertissements ⚠️\n"
        
        if warnings:
            for i, warning in enumerate(warnings, 1):
                report += f"\n{i}. **{warning.get('message', 'Avertissement inconnu')}**\n"
                report += f"   - **Type :** {warning.get('type', 'unknown')}\n"
                if 'file' in warning:
                    report += f"   - **Fichier :** {warning['file']}\n"
                if 'files' in warning:
                    report += f"   - **Fichiers :** {', '.join(warning['files'])}\n"
        else:
            report += "\nAucun avertissement détecté.\n"
        
        report += "\n## Informations ℹ️\n"
        
        if issues:
            for i, issue in enumerate(issues, 1):
                report += f"\n{i}. **{issue.get('message', 'Information inconnue')}**\n"
                report += f"   - **Type :** {issue.get('type', 'unknown')}\n"
                if 'file' in issue:
                    report += f"   - **Fichier :** {issue['file']}\n"
                if 'files' in issue:
                    report += f"   - **Fichiers :** {', '.join(issue['files'])}\n"
        else:
            report += "\nAucune information à signaler.\n"
        
        # Résumé
        if errors:
            status = "❌ Requiert attention urgente"
        elif warnings:
            status = "⚠️ Requiert attention"
        else:
            status = "✅ Sain"
        
        report += f"\n## Résumé\n"
        report += f"- **Statut global :** {status}\n"
        report += f"- **Actions recommandées :**\n"
        
        if errors:
            report += "  1. Corriger les erreurs critiques\n"
        if warnings:
            report += "  2. Examiner les avertissements\n"
        if issues:
            report += "  3. Prendre note des informations\n"
        
        return report
    
    async def close(self) -> None:
        """Fermer les ressources du pipeline."""
        pass
