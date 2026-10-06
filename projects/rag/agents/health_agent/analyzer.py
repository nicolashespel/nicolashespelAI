"""
Analyseur du système RAG pour la détection des problèmes.

Ce module analyse:
- Les contradictions entre documents
- Les pages orphelines
- Les informations obsolètes
- La couverture des sujets
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class SystemAnalyzer:
    """
    Analyseur du système RAG.
    
    Fonctionnalités:
    - Détection des contradictions
    - Détection des pages orphelines
    - Détection des informations obsolètes
    - Analyse de la couverture
    """
    
    def __init__(
        self,
        detect_contradictions: bool = True,
        detect_orphans: bool = True,
        detect_obsolete: bool = True,
        check_coverage: bool = True,
    ) -> None:
        """
        Initialiser l'analyseur.
        
        Args:
            detect_contradictions: Détecter les contradictions.
            detect_orphans: Détecter les pages orphelines.
            detect_obsolete: Détecter les informations obsolètes.
            check_coverage: Vérifier la couverture.
        """
        self.detect_contradictions = detect_contradictions
        self.detect_orphans = detect_orphans
        self.detect_obsolete = detect_obsolete
        self.check_coverage = check_coverage
    
    def analyze(
        self,
        vault_path: Union[Path, str],
        all_pages: Optional[List[Path]] = None,
    ) -> Dict[str, Any]:
        """
        Analyser le système RAG.
        
        Args:
            vault_path: Chemin du vault.
            all_pages: Liste de toutes les pages (optionnel).
            
        Returns:
            Résultat de l'analyse.
        """
        vault_path = Path(vault_path)
        
        if all_pages is None:
            all_pages = [
                f for f in vault_path.glob("**/*.md")
                if f.is_file() and not f.name.startswith(".")
            ]
        
        results: Dict[str, Any] = {
            "success": True,
            "vault_path": str(vault_path),
            "pages_analyzed": len(all_pages),
            "contradictions": [],
            "orphans": [],
            "obsolete": [],
            "coverage": {},
        }
        
        # Détecter les contradictions
        if self.detect_contradictions:
            results["contradictions"] = self._detect_contradictions(all_pages)
        
        # Détecter les pages orphelines
        if self.detect_orphans:
            results["orphans"] = self._detect_orphans(all_pages)
        
        # Détecter les informations obsolètes
        if self.detect_obsolete:
            results["obsolete"] = self._detect_obsolete(all_pages)
        
        # Analyser la couverture
        if self.check_coverage:
            results["coverage"] = self._analyze_coverage(all_pages)
        
        # Calculer les statistiques
        results["statistics"] = {
            "total_issues": (
                len(results["contradictions"]) +
                len(results["orphans"]) +
                len(results["obsolete"])
            ),
            "contradictions_count": len(results["contradictions"]),
            "orphans_count": len(results["orphans"]),
            "obsolete_count": len(results["obsolete"]),
            "coverage_score": results["coverage"].get("score", 0),
        }
        
        return results
    
    def _detect_contradictions(self, pages: List[Path]) -> List[Dict[str, Any]]:
        """Détecter les contradictions entre pages."""
        contradictions = []
        
        # Grouper les pages par sujet
        subjects: Dict[str, List[Path]] = {}
        
        for page in pages:
            # Extraire les sujets du nom de fichier et du contenu
            subjects_from_page = self._extract_subjects(page)
            
            for subject in subjects_from_page:
                if subject not in subjects:
                    subjects[subject] = []
                subjects[subject].append(page)
        
        # Comparer les pages pour chaque sujet
        for subject, subject_pages in subjects.items():
            if len(subject_pages) < 2:
                continue
            
            # Extraire les affirmations de chaque page
            statements_by_page = {}
            for page in subject_pages:
                statements = self._extract_statements(page)
                if statements:
                    statements_by_page[str(page)] = statements
            
            # Comparer les affirmations
            for page1, statements1 in statements_by_page.items():
                for page2, statements2 in statements_by_page.items():
                    if page1 >= page2:
                        continue
                    
                    # Trouver les contradictions
                    for statement1 in statements1:
                        for statement2 in statements2:
                            if self._are_contradictory(statement1, statement2):
                                contradictions.append({
                                    "subject": subject,
                                    "page1": page1,
                                    "page2": page2,
                                    "statement1": statement1,
                                    "statement2": statement2,
                                    "severity": "high",
                                })
        
        return contradictions
    
    def _extract_subjects(self, page: Path) -> List[str]:
        """Extraire les sujets d'une page."""
        subjects = []
        
        try:
            with open(page, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extraire du frontmatter
            if content.startswith("---"):
                end_index = content.find("---", 3)
                if end_index != -1:
                    import yaml
                    frontmatter = yaml.safe_load(content[3:end_index])
                    if frontmatter:
                        # Ajouter les tags
                        tags = frontmatter.get("tags", [])
                        subjects.extend(tags)
                        
                        # Ajouter le type
                        page_type = frontmatter.get("type", "")
                        if page_type:
                            subjects.append(page_type)
                        
                        # Ajouter le titre
                        title = frontmatter.get("title", "")
                        if title:
                            subjects.append(title.lower())
            
            # Extraire des mots-clés du contenu
            import re
            words = re.findall(r'\b[A-Z][a-z]+\b', content)
            subjects.extend([w.lower() for w in words[:5]])
            
        except Exception:
            pass
        
        return list(set(subjects))
    
    def _extract_statements(self, page: Path) -> List[str]:
        """Extraire les affirmations d'une page."""
        statements = []
        
        try:
            with open(page, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extraire le contenu principal (après le frontmatter)
            if content.startswith("---"):
                end_index = content.find("---", 3)
                if end_index != -1:
                    content = content[end_index + 3:]
            
            # Diviser en phrases
            import re
            sentences = re.split(r'[.!?]', content)
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 20:  # Ignorer les phrases trop courtes
                    statements.append(sentence)
            
        except Exception:
            pass
        
        return statements
    
    def _are_contradictory(self, statement1: str, statement2: str) -> bool:
        """Vérifier si deux affirmations sont contradictoires."""
        # Implémentation simplifiée
        # Dans une implémentation complète, utiliser un modèle de langage
        
        # Liste de mots contradictoires
        contradictions = [
            ("est", "n'est pas"),
            ("vrai", "faux"),
            ("correct", "incorrect"),
            ("efficace", "inefficace"),
            ("meilleur", "pire"),
            ("augmente", "diminue"),
            ("prouve", "réfute"),
            ("recommande", "déconseille"),
        ]
        
        statement1_lower = statement1.lower()
        statement2_lower = statement2.lower()
        
        for word1, word2 in contradictions:
            if word1 in statement1_lower and word2 in statement2_lower:
                return True
            if word2 in statement1_lower and word1 in statement2_lower:
                return True
        
        return False
    
    def _detect_orphans(self, pages: List[Path]) -> List[Dict[str, Any]]:
        """Détecter les pages orphelines."""
        orphans = []
        
        # Créer un index des pages
        page_names = {p.stem for p in pages}
        
        # Vérifier chaque page
        for page in pages:
            # Lire le contenu
            try:
                with open(page, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
            
            # Trouver tous les liens dans le contenu
            import re
            links = re.findall(r'\[\[([^\]]+)\]\]', content)
            
            # Vérifier si la page est référencée par d'autres pages
            is_referenced = False
            for other_page in pages:
                if other_page == page:
                    continue
                
                try:
                    with open(other_page, "r", encoding="utf-8") as f:
                        other_content = f.read()
                    
                    if page.stem in other_content:
                        is_referenced = True
                        break
                except Exception:
                    continue
            
            # Si la page n'est pas référencée et n'est pas dans l'index
            if not is_referenced and not self._is_in_index(page):
                orphans.append({
                    "page": str(page),
                    "type": "unreferenced",
                    "severity": "medium",
                })
        
        return orphans
    
    def _is_in_index(self, page: Path) -> bool:
        """Vérifier si une page est dans l'index."""
        index_path = page.parent.parent / "index.md"
        
        if not index_path.exists():
            return False
        
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                index_content = f.read()
            
            return page.name in index_content
        except Exception:
            return False
    
    def _detect_obsolete(self, pages: List[Path]) -> List[Dict[str, Any]]:
        """Détecter les informations obsolètes."""
        obsolete = []
        
        # Vérifier les dates
        current_year = datetime.now().year
        
        for page in pages:
            try:
                with open(page, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
            
            # Extraire les dates du frontmatter
            if content.startswith("---"):
                end_index = content.find("---", 3)
                if end_index != -1:
                    import yaml
                    try:
                        frontmatter = yaml.safe_load(content[3:end_index])
                        if frontmatter:
                            # Vérifier la date de création
                            created = frontmatter.get("created", "")
                            if created:
                                try:
                                    import dateutil.parser
                                    created_date = dateutil.parser.parse(created)
                                    if current_year - created_date.year > 2:
                                        obsolete.append({
                                            "page": str(page),
                                            "issue": "Date de création ancienne",
                                            "date": created,
                                            "severity": "low",
                                        })
                                except Exception:
                                    pass
                            
                            # Vérifier la date de mise à jour
                            updated = frontmatter.get("updated", "")
                            if updated:
                                try:
                                    import dateutil.parser
                                    updated_date = dateutil.parser.parse(updated)
                                    if current_year - updated_date.year > 1:
                                        obsolete.append({
                                            "page": str(page),
                                            "issue": "Non mis à jour depuis longtemps",
                                            "date": updated,
                                            "severity": "medium",
                                        })
                                except Exception:
                                    pass
            
            # Vérifier les années dans le contenu
            import re
            years = re.findall(r'\b(19|20)\d{2}\b', content)
            for year in years:
                year_int = int(year)
                if year_int < current_year - 5:
                    obsolete.append({
                        "page": str(page),
                        "issue": f"Année ancienne: {year}",
                        "severity": "info",
                    })
        
        return obsolete
    
    def _analyze_coverage(self, pages: List[Path]) -> Dict[str, Any]:
        """Analyser la couverture des sujets."""
        coverage = {
            "total_subjects": 0,
            "covered_subjects": 0,
            "coverage_ratio": 0.0,
            "subjects": {},
            "score": 0.0,
        }
        
        # Extraire tous les sujets
        all_subjects = []
        for page in pages:
            subjects = self._extract_subjects(page)
            all_subjects.extend(subjects)
        
        # Compter les sujets uniques
        unique_subjects = list(set(all_subjects))
        coverage["total_subjects"] = len(unique_subjects)
        
        # Analyser la couverture par type de page
        type_coverage = {}
        for page in pages:
            try:
                with open(page, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
            
            # Extraire le type
            page_type = "unknown"
            if content.startswith("---"):
                end_index = content.find("---", 3)
                if end_index != -1:
                    import yaml
                    try:
                        frontmatter = yaml.safe_load(content[3:end_index])
                        page_type = frontmatter.get("type", "unknown")
                    except Exception:
                        pass
            
            if page_type not in type_coverage:
                type_coverage[page_type] = 0
            type_coverage[page_type] += 1
        
        coverage["by_type"] = type_coverage
        
        # Calculer le score de couverture
        # Score basé sur la diversité des types
        type_diversity = len(type_coverage)
        coverage["score"] = min(type_diversity / 5, 1.0)  # 5 types max
        
        return coverage


# Importer datetime pour _detect_obsolete
import datetime
