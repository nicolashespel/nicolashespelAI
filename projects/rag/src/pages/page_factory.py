"""
Fabrique de pages pour le système RAG Wiki.

Ce module contient la classe PageFactory qui crée les différentes
pages du vault à partir des modèles.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml

from ..types import (
    Page,
    EntityPage,
    ConceptPage,
    SourcePage,
    ComparisonPage,
    SynthesisPage,
    IndexPage,
    LogPage,
    PageTypeEnum,
    EntityTypeEnum,
    SourceTypeEnum,
)
from .templates import PageTemplates


class PageFactory:
    """
    Fabrique de pages pour le système RAG Wiki.
    
    Cette classe crée les différentes pages du vault à partir des modèles
    et des données fournies.
    """
    
    def __init__(self) -> None:
        """Initialiser la PageFactory."""
        self.templates = PageTemplates()
    
    def create_page(
        self,
        page_type: PageTypeEnum,
        data: Dict[str, Any],
    ) -> str:
        """
        Créer une page de type spécifique.
        
        Args:
            page_type: Type de la page.
            data: Données pour la page.
            
        Returns:
            Contenu markdown de la page.
        """
        if page_type == PageTypeEnum.ENTITY:
            return self.create_entity_page(EntityPage(**data))
        elif page_type == PageTypeEnum.CONCEPT:
            return self.create_concept_page(ConceptPage(**data))
        elif page_type == PageTypeEnum.SOURCE:
            return self.create_source_page(SourcePage(**data))
        elif page_type == PageTypeEnum.COMPARISON:
            return self.create_comparison_page(ComparisonPage(**data))
        elif page_type == PageTypeEnum.SYNTHESIS:
            return self.create_synthesis_page(SynthesisPage(**data))
        elif page_type == PageTypeEnum.INDEX:
            return self.create_index_page(IndexPage(**data))
        elif page_type == PageTypeEnum.LOG:
            return self.create_log_page(LogPage(**data))
        else:
            raise ValueError(f"Type de page inconnu: {page_type}")
    
    def create_entity_page(self, page: EntityPage) -> str:
        """
        Créer une page d'entité.
        
        Args:
            page: Page d'entité.
            
        Returns:
            Contenu markdown.
        """
        # Convertir en dict pour le frontmatter
        page_dict = self._page_to_dict(page)
        
        # Générer le frontmatter
        frontmatter = yaml.dump(
            page_dict,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        
        # Générer le contenu
        content = self.templates.get_entity_template()
        content = self._replace_placeholders(content, page_dict)
        
        return f"""---
{frontmatter}---

{content}
"""
    
    def create_concept_page(self, page: ConceptPage) -> str:
        """
        Créer une page de concept.
        
        Args:
            page: Page de concept.
            
        Returns:
            Contenu markdown.
        """
        # Convertir en dict pour le frontmatter
        page_dict = self._page_to_dict(page)
        
        # Générer le frontmatter
        frontmatter = yaml.dump(
            page_dict,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        
        # Générer le contenu
        content = self.templates.get_concept_template()
        content = self._replace_placeholders(content, page_dict)
        
        return f"""---
{frontmatter}---

{content}
"""
    
    def create_source_page(self, page: SourcePage) -> str:
        """
        Créer une page de source.
        
        Args:
            page: Page de source.
            
        Returns:
            Contenu markdown.
        """
        # Convertir en dict pour le frontmatter
        page_dict = self._page_to_dict(page)
        
        # Générer le frontmatter
        frontmatter = yaml.dump(
            page_dict,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        
        # Générer le contenu
        content = self.templates.get_source_template()
        content = self._replace_placeholders(content, page_dict)
        
        return f"""---
{frontmatter}---

{content}
"""
    
    def create_comparison_page(self, page: ComparisonPage) -> str:
        """
        Créer une page de comparaison.
        
        Args:
            page: Page de comparaison.
            
        Returns:
            Contenu markdown.
        """
        # Convertir en dict pour le frontmatter
        page_dict = self._page_to_dict(page)
        
        # Générer le frontmatter
        frontmatter = yaml.dump(
            page_dict,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        
        # Générer le contenu
        content = self.templates.get_comparison_template()
        content = self._replace_placeholders(content, page_dict)
        
        return f"""---
{frontmatter}---

{content}
"""
    
    def create_synthesis_page(self, page: SynthesisPage) -> str:
        """
        Créer une page de synthèse.
        
        Args:
            page: Page de synthèse.
            
        Returns:
            Contenu markdown.
        """
        # Convertir en dict pour le frontmatter
        page_dict = self._page_to_dict(page)
        
        # Générer le frontmatter
        frontmatter = yaml.dump(
            page_dict,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        
        # Générer le contenu
        content = self.templates.get_synthesis_template()
        content = self._replace_placeholders(content, page_dict)
        
        return f"""---
{frontmatter}---

{content}
"""
    
    def create_index_page(self, page: IndexPage) -> str:
        """
        Créer une page d'index.
        
        Args:
            page: Page d'index.
            
        Returns:
            Contenu markdown.
        """
        # Convertir en dict pour le frontmatter
        page_dict = self._page_to_dict(page)
        
        # Générer le frontmatter
        frontmatter = yaml.dump(
            page_dict,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        
        # Générer le contenu
        content = self._generate_index_content(page)
        
        return f"""---
{frontmatter}---

{content}
"""
    
    def create_log_page(self, page: LogPage) -> str:
        """
        Créer une page de log.
        
        Args:
            page: Page de log.
            
        Returns:
            Contenu markdown.
        """
        # Convertir en dict pour le frontmatter
        page_dict = self._page_to_dict(page)
        
        # Générer le frontmatter
        frontmatter = yaml.dump(
            page_dict,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        
        # Générer le contenu
        content = self._generate_log_content(page)
        
        return f"""---
{frontmatter}---

{content}
"""
    
    def _page_to_dict(self, page: Page) -> Dict[str, Any]:
        """
        Convertir une page en dictionnaire.
        
        Args:
            page: Page à convertir.
            
        Returns:
            Dictionnaire.
        """
        page_dict = page.__dict__.copy()
        
        # Convertir les datetime en strings
        for key, value in page_dict.items():
            if isinstance(value, datetime):
                page_dict[key] = value.isoformat()
            elif isinstance(value, list):
                page_dict[key] = [str(v) for v in value]
            elif hasattr(value, '__dict__'):
                # Pour les enum
                page_dict[key] = value.value
        
        return page_dict
    
    def _replace_placeholders(self, template: str, data: Dict[str, Any]) -> str:
        """
        Remplacer les placeholders dans un template.
        
        Args:
            template: Template avec placeholders.
            data: Données à insérer.
            
        Returns:
            Template avec placeholders remplacés.
        """
        # Remplacer les placeholders simples
        for key, value in data.items():
            if isinstance(value, (str, int, float)):
                placeholder = f"{{{{{key}}}}}"
                template = template.replace(placeholder, str(value))
        
        # Remplacer les placeholders de liste
        if 'authors' in data and data['authors']:
            authors_str = ", ".join(data['authors'])
            template = template.replace("{{authors}}", authors_str)
        
        if 'tags' in data and data['tags']:
            tags_str = ", ".join(data['tags'])
            template = template.replace("{{tags}}", tags_str)
        
        if 'related' in data and data['related']:
            related_str = ", ".join([f"[[{r}]]" for r in data['related']])
            template = template.replace("{{related}}", related_str)
        
        if 'sources' in data and data['sources']:
            sources_str = ", ".join([f"[[{s}]]" for s in data['sources']])
            template = template.replace("{{sources}}", sources_str)
        
        return template
    
    def _generate_index_content(self, page: IndexPage) -> str:
        """
        Générer le contenu de l'index.
        
        Args:
            page: Page d'index.
            
        Returns:
            Contenu markdown.
        """
        lines = [
            f"# {page.name}",
            "",
            "## Statistiques",
            f"- **Total pages :** {page.statistics.get('total_pages', 0)}",
            f"- **Entités :** {page.statistics.get('entities', 0)}",
            f"- **Concepts :** {page.statistics.get('concepts', 0)}",
            f"- **Sources :** {page.statistics.get('sources', 0)}",
            f"- **Comparaisons :** {page.statistics.get('comparisons', 0)}",
            f"- **Synthèses :** {page.statistics.get('syntheses', 0)}",
            f"- **Dernière mise à jour :** {page.generated.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Par Type",
        ]
        
        # Pages par type
        for page_type, pages in page.pages_by_type.items():
            if pages:
                lines.append(f"### {page_type.capitalize()} ({len(pages)})")
                for p in pages:
                    lines.append(f"- [[{p}]]")
                lines.append("")
        
        # Pages par tag
        if page.pages_by_tag:
            lines.append("## Par Tag")
            for tag, pages in sorted(page.pages_by_tag.items()):
                if pages:
                    lines.append(f"### {tag} ({len(pages)})")
                    for p in pages:
                        lines.append(f"- [[{p}]]")
                    lines.append("")
        
        # Pages par date
        if page.pages_by_date:
            lines.append("## Par Date")
            for date, pages in sorted(page.pages_by_date.items(), reverse=True):
                if pages:
                    lines.append(f"### {date} ({len(pages)})")
                    for p in pages:
                        lines.append(f"- [[{p}]]")
                    lines.append("")
        
        lines.append("## Recherche")
        lines.append("Utilisez les commandes `/wiki-query` ou `/wiki-search` pour trouver du contenu.")
        
        return "\n".join(lines)
    
    def _generate_log_content(self, page: LogPage) -> str:
        """
        Générer le contenu du log.
        
        Args:
            page: Page de log.
            
        Returns:
            Contenu markdown.
        """
        lines = [
            f"# {page.name}",
            "",
            f"{page.description}",
            "",
        ]
        
        # Grouper les entrées par date
        entries_by_date = {}
        for entry in page.entries:
            if 'timestamp' in entry:
                date = entry['timestamp'][:10]  # Extraire la date
                if date not in entries_by_date:
                    entries_by_date[date] = []
                entries_by_date[date].append(entry)
        
        # Ajouter les entrées
        for date, entries in sorted(entries_by_date.items(), reverse=True):
            lines.append(f"## {date}")
            lines.append("")
            
            for entry in entries:
                # Extraire les informations
                operation = entry.get('operation', 'unknown')
                details = entry.get('details', {})
                duration = entry.get('duration_seconds', 0)
                success = entry.get('success', False)
                
                # Formater l'heure
                timestamp = entry.get('timestamp', '')
                if timestamp and len(timestamp) > 11:
                    time_part = timestamp[11:19]
                else:
                    time_part = ""
                
                # Formater les détails
                details_str = ""
                if isinstance(details, dict):
                    for key, value in details.items():
                        if isinstance(value, list):
                            details_str += f"\n- **{key}:** {', '.join([str(v) for v in value])}"
                        else:
                            details_str += f"\n- **{key}:** {value}"
                
                # Statut
                status = "✅" if success else "❌"
                
                lines.append(f"### {time_part} - {operation.capitalize()}")
                lines.append(f"{status} **Status:** {status}")
                lines.append(f"- **Durée:** {duration:.2f}s")
                if details_str:
                    lines.append(details_str)
                lines.append("")
        
        return "\n".join(lines)
