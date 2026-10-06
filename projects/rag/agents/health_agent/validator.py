"""
Validateur de contenu pour le système RAG.

Ce module vérifie:
- La validité du frontmatter
- Les liens internes
- Les références
- Les types de pages
- Les tags
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

logger = logging.getLogger(__name__)


class ContentValidator:
    """
    Validateur de contenu pour le système RAG.
    
    Fonctionnalités:
    - Validation du frontmatter YAML
    - Vérification des liens internes
    - Vérification des références
    - Vérification des types de pages
    - Vérification des tags
    """
    
    def __init__(
        self,
        check_frontmatter: bool = True,
        check_links: bool = True,
        check_references: bool = True,
        check_types: bool = True,
        check_tags: bool = True,
    ) -> None:
        """
        Initialiser le validateur.
        
        Args:
            check_frontmatter: Vérifier le frontmatter.
            check_links: Vérifier les liens.
            check_references: Vérifier les références.
            check_types: Vérifier les types.
            check_tags: Vérifier les tags.
        """
        self.check_frontmatter = check_frontmatter
        self.check_links = check_links
        self.check_references = check_references
        self.check_types = check_types
        self.check_tags = check_tags
        
        # Types de pages valides
        self.valid_types = ["source", "entity", "concept", "comparison", "synthesis"]
        
        # Entity types valides
        self.valid_entity_types = ["person", "organization", "place", "product", "project", "event"]
        
        # Patterns pour les liens wiki
        self.link_pattern = r'\[\[([^\]]+)\]\]'
    
    def validate_file(
        self,
        file_path: Union[Path, str],
        all_pages: Optional[List[Path]] = None,
    ) -> Dict[str, Any]:
        """
        Valider un fichier.
        
        Args:
            file_path: Chemin du fichier à valider.
            all_pages: Liste de tous les chemins de pages (pour vérifier les liens).
            
        Returns:
            Résultat de la validation avec erreurs et avertissements.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                "success": False,
                "file": str(file_path),
                "error": "Fichier non trouvé",
                "errors": ["Fichier non trouvé"],
                "warnings": [],
            }
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return self.validate_content(content, file_path, all_pages)
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation de {file_path}: {e}")
            return {
                "success": False,
                "file": str(file_path),
                "error": str(e),
                "errors": [str(e)],
                "warnings": [],
            }
    
    def validate_content(
        self,
        content: str,
        file_path: Optional[Path] = None,
        all_pages: Optional[List[Path]] = None,
    ) -> Dict[str, Any]:
        """
        Valider le contenu d'un fichier.
        
        Args:
            content: Contenu à valider.
            file_path: Chemin du fichier (pour logging).
            all_pages: Liste de tous les chemins de pages.
            
        Returns:
            Résultat de la validation.
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # Vérifier le frontmatter
        if self.check_frontmatter:
            frontmatter_errors, frontmatter_warnings = self._validate_frontmatter(content)
            errors.extend(frontmatter_errors)
            warnings.extend(frontmatter_warnings)
        
        # Vérifier les liens
        if self.check_links and all_pages:
            link_errors, link_warnings = self._validate_links(content, all_pages)
            errors.extend(link_errors)
            warnings.extend(link_warnings)
        
        # Vérifier les références
        if self.check_references:
            ref_errors, ref_warnings = self._validate_references(content)
            errors.extend(ref_errors)
            warnings.extend(ref_warnings)
        
        # Vérifier le type
        if self.check_types:
            type_errors, type_warnings = self._validate_type(content)
            errors.extend(type_errors)
            warnings.extend(type_warnings)
        
        # Vérifier les tags
        if self.check_tags:
            tag_errors, tag_warnings = self._validate_tags(content)
            errors.extend(tag_errors)
            warnings.extend(tag_warnings)
        
        return {
            "success": len(errors) == 0,
            "file": str(file_path) if file_path else "unknown",
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings),
        }
    
    def _validate_frontmatter(self, content: str) -> Tuple[List[str], List[str]]:
        """Valider le frontmatter YAML."""
        errors: List[str] = []
        warnings: List[str] = []
        
        # Vérifier la présence du frontmatter
        if not content.startswith("---"):
            errors.append("Frontmatter manquant: le fichier doit commencer par '---'")
            return errors, warnings
        
        # Extraire le frontmatter
        try:
            # Trouver la fin du frontmatter
            end_index = content.find("---", 3)
            if end_index == -1:
                errors.append("Frontmatter incomplet: '---' de fin manquant")
                return errors, warnings
            
            frontmatter_str = content[3:end_index]
            frontmatter = yaml.safe_load(frontmatter_str)
            
            if not frontmatter:
                errors.append("Frontmatter vide")
                return errors, warnings
            
            # Vérifier les champs requis
            if "type" not in frontmatter:
                errors.append("Champ 'type' manquant dans le frontmatter")
            
            if "title" not in frontmatter:
                warnings.append("Champ 'title' manquant dans le frontmatter")
            
            if "created" not in frontmatter:
                warnings.append("Champ 'created' manquant dans le frontmatter")
            
            return errors, warnings
            
        except yaml.YAMLError as e:
            errors.append(f"Erreur de syntaxe YAML dans le frontmatter: {e}")
            return errors, warnings
        except Exception as e:
            errors.append(f"Erreur lors de la validation du frontmatter: {e}")
            return errors, warnings
    
    def _validate_links(
        self,
        content: str,
        all_pages: List[Path],
    ) -> Tuple[List[str], List[str]]:
        """Valider les liens internes."""
        errors: List[str] = []
        warnings: List[str] = []
        
        # Trouver tous les liens wiki
        links = re.findall(self.link_pattern, content)
        
        if not links:
            warnings.append("Aucun lien wiki trouvé dans le contenu")
            return errors, warnings
        
        # Créer une liste des noms de pages valides
        valid_pages = {p.stem for p in all_pages}
        
        for link in links:
            # Normaliser le nom de la page
            page_name = link.strip()
            
            # Vérifier si la page existe
            if page_name not in valid_pages:
                # Vérifier si c'est un lien vers une section
                if "#" in page_name:
                    page_name = page_name.split("#")[0]
                    if page_name not in valid_pages:
                        errors.append(f"Lien brisé vers: [[{link}]]")
                else:
                    errors.append(f"Lien brisé vers: [[{link}]]")
        
        return errors, warnings
    
    def _validate_references(
        self,
        content: str,
    ) -> Tuple[List[str], List[str]]:
        """Valider les références."""
        errors: List[str] = []
        warnings: List[str] = []
        
        # Extraire le frontmatter
        try:
            if not content.startswith("---"):
                return errors, warnings
            
            end_index = content.find("---", 3)
            if end_index == -1:
                return errors, warnings
            
            frontmatter_str = content[3:end_index]
            frontmatter = yaml.safe_load(frontmatter_str)
            
            if not frontmatter:
                return errors, warnings
            
            # Vérifier les références
            sources = frontmatter.get("sources", [])
            related = frontmatter.get("related", [])
            
            if not sources and not related:
                warnings.append("Aucune référence (sources ou related) dans le frontmatter")
            
            return errors, warnings
            
        except Exception:
            return errors, warnings
    
    def _validate_type(self, content: str) -> Tuple[List[str], List[str]]:
        """Valider le type de page."""
        errors: List[str] = []
        warnings: List[str] = []
        
        try:
            if not content.startswith("---"):
                errors.append("Frontmatter manquant pour vérifier le type")
                return errors, warnings
            
            end_index = content.find("---", 3)
            if end_index == -1:
                errors.append("Frontmatter incomplet pour vérifier le type")
                return errors, warnings
            
            frontmatter_str = content[3:end_index]
            frontmatter = yaml.safe_load(frontmatter_str)
            
            if not frontmatter:
                errors.append("Frontmatter vide pour vérifier le type")
                return errors, warnings
            
            page_type = frontmatter.get("type", "")
            
            if page_type not in self.valid_types:
                errors.append(f"Type de page invalide: '{page_type}'. Types valides: {', '.join(self.valid_types)}")
            
            # Vérifier les types spécifiques
            if page_type == "entity":
                entity_type = frontmatter.get("entity_type", "")
                if entity_type not in self.valid_entity_types:
                    warnings.append(f"Type d'entité invalide: '{entity_type}'. Types valides: {', '.join(self.valid_entity_types)}")
            
            return errors, warnings
            
        except Exception:
            return errors, warnings
    
    def _validate_tags(self, content: str) -> Tuple[List[str], List[str]]:
        """Valider les tags."""
        errors: List[str] = []
        warnings: List[str] = []
        
        try:
            if not content.startswith("---"):
                warnings.append("Frontmatter manquant pour vérifier les tags")
                return errors, warnings
            
            end_index = content.find("---", 3)
            if end_index == -1:
                warnings.append("Frontmatter incomplet pour vérifier les tags")
                return errors, warnings
            
            frontmatter_str = content[3:end_index]
            frontmatter = yaml.safe_load(frontmatter_str)
            
            if not frontmatter:
                warnings.append("Frontmatter vide pour vérifier les tags")
                return errors, warnings
            
            tags = frontmatter.get("tags", [])
            
            if not tags:
                warnings.append("Aucun tag dans le frontmatter")
                return errors, warnings
            
            # Vérifier le format des tags
            for tag in tags:
                if not isinstance(tag, str):
                    errors.append(f"Tag invalide: '{tag}' doit être une chaîne de caractères")
                elif len(tag) > 50:
                    warnings.append(f"Tag trop long: '{tag}' ({len(tag)} caractères)")
                elif not tag.replace("-", "").replace("_", "").isalnum():
                    warnings.append(f"Tag avec caractères spéciaux: '{tag}'")
            
            return errors, warnings
            
        except Exception:
            return errors, warnings
    
    def validate_all(
        self,
        files: List[Union[Path, str]],
    ) -> Dict[str, Any]:
        """
        Valider tous les fichiers.
        
        Args:
            files: Liste des fichiers à valider.
            
        Returns:
            Résultat global de la validation.
        """
        results = []
        all_pages = [Path(f) for f in files]
        
        for file_path in files:
            result = self.validate_file(file_path, all_pages)
            results.append(result)
        
        # Calculer les statistiques
        total_files = len(results)
        files_with_errors = sum(1 for r in results if not r.get("success", True))
        files_with_warnings = sum(1 for r in results if r.get("warning_count", 0) > 0)
        total_errors = sum(r.get("error_count", 0) for r in results)
        total_warnings = sum(r.get("warning_count", 0) for r in results)
        
        return {
            "success": files_with_errors == 0,
            "total_files": total_files,
            "files_with_errors": files_with_errors,
            "files_with_warnings": files_with_warnings,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "results": results,
        }
