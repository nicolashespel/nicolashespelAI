"""
Gestionnaire du vault pour le système RAG Wiki.

Ce module contient la classe VaultManager qui gère toutes les opérations
liées au vault (création, lecture, écriture, recherche).
"""

import os
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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
)
from ..core.config import WikiConfig, get_config
from .file_manager import FileManager


class VaultManager:
    """
    Gestionnaire du vault pour le système RAG Wiki.
    
    Cette classe gère toutes les opérations de base sur le vault :
    - Initialisation de la structure
    - Lecture/écriture des pages
    - Recherche dans le vault
    - Gestion des statistiques
    """
    
    def __init__(
        self,
        vault_path: Path,
        config: Optional[WikiConfig] = None,
    ) -> None:
        """
        Initialiser le VaultManager.
        
        Args:
            vault_path: Chemin vers le vault.
            config: Configuration du wiki.
        """
        self.vault_path = vault_path
        self.config = config or get_config()
        self.file_manager = FileManager(vault_path)
        
        # Créer les chemins si nécessaire
        self._ensure_vault_structure()
    
    def _ensure_vault_structure(self) -> None:
        """S'assurer que la structure du vault existe."""
        # Créer les dossiers principaux
        (self.vault_path / "raw").mkdir(parents=True, exist_ok=True)
        (self.vault_path / "wiki").mkdir(parents=True, exist_ok=True)
        
        # Créer les sous-dossiers de wiki
        for subdir in ["entities", "concepts", "sources", "comparisons", "synthesis"]:
            (self.vault_path / "wiki" / subdir).mkdir(parents=True, exist_ok=True)
        
        # Créer les sous-dossiers d'entités
        for entity_type in ["people", "organizations", "places", "products", "projects", "events"]:
            (self.vault_path / "wiki" / "entities" / entity_type).mkdir(parents=True, exist_ok=True)
    
    def initialize_vault(
        self,
        topic: str = "Recherche",
        tool: str = "all",
    ) -> None:
        """
        Initialiser un nouveau vault avec la structure complète.
        
        Args:
            topic: Sujet principal du vault.
            tool: Outil LLM à configurer.
        """
        # S'assurer que la structure existe
        self._ensure_vault_structure()
        
        # Créer les fichiers de configuration
        self._create_config_files(tool)
        
        # Créer les fichiers initiaux
        self._create_initial_files(topic)
        
        # Créer les templates
        self._create_templates()
    
    def _create_config_files(self, tool: str) -> None:
        """
        Créer les fichiers de configuration.
        
        Args:
            tool: Outil LLM à configurer.
        """
        # CLAUDE.md
        claude_content = self._generate_claude_config()
        self.file_manager.write_file(
            self.vault_path / "CLAUDE.md",
            claude_content,
        )
        
        # AGENTS.md
        agents_content = self._generate_agents_config()
        self.file_manager.write_file(
            self.vault_path / "AGENTS.md",
            agents_content,
        )
        
        # .cursorrules (optionnel)
        if tool in ["all", "cursor"]:
            cursorrules_content = self._generate_cursorrules_config()
            self.file_manager.write_file(
                self.vault_path / ".cursorrules",
                cursorrules_content,
            )
    
    def _generate_claude_config(self) -> str:
        """Générer le contenu de CLAUDE.md."""
        return """# Claude Code Configuration for RAG Wiki

## Instructions
You are a disciplined wiki maintainer. Follow the SKILL.md rules strictly.

## Commands

### /wiki-init
Initialize a new wiki vault.

### /wiki-ingest <path>
Ingest a source file and update the wiki.

### /wiki-query <query>
Query the wiki and return a synthesized answer.

### /wiki-lint
Run health checks on the wiki.

### /wiki-log
Show the operation log.

## Rules
1. Never edit files in raw/
2. Always update index.md
3. Always log operations in log.md
4. Cross-reference everything
5. Flag contradictions explicitly
"""
    
    def _generate_agents_config(self) -> str:
        """Générer le contenu de AGENTS.md."""
        return """# LLM Wiki Configuration

## Role
You are a disciplined wiki maintainer for the RAG Wiki system.

## Skills
- Wiki Ingestor
- Wiki Librarian  
- Wiki Linter

## Commands

### wiki-init
Initialize a new wiki vault with the specified parameters.

### wiki-ingest
Ingest a source file, create summary, update cross-references, update index, log operation.

### wiki-query
Search the wiki using layered retrieval (index -> BM25 -> embeddings), synthesize answer with citations.

### wiki-lint
Run mechanical and semantic health checks, surface contradictions, orphans, stale claims.

### wiki-log
Display the operation log from log.md.

## Rules
1. IMMUTABLE_RAW: Never modify files in the raw/ directory
2. UPDATE_INDEX: Always update index.md after any change
3. LOG_OPERATIONS: Always append to log.md
4. CROSS_REFERENCE: Link to existing pages when relevant
5. FLAG_CONTRADICTIONS: Explicitly mark contradictions
6. CITE_SOURCES: Always cite sources for claims
"""
    
    def _generate_cursorrules_config(self) -> str:
        """Générer le contenu de .cursorrules."""
        return """# Cursor Rules for RAG Wiki

## System
You are a wiki maintainer. Follow SKILL.md strictly.

## Commands
- /wiki-init: Initialize vault
- /wiki-ingest <path>: Ingest source
- /wiki-query <query>: Query wiki
- /wiki-lint: Health check
- /wiki-log: Show log

## Rules
- NEVER edit raw/
- ALWAYS update index.md
- ALWAYS log to log.md
- Cross-reference everything
- Flag contradictions
"""
    
    def _create_initial_files(self, topic: str) -> None:
        """
        Créer les fichiers initiaux.
        
        Args:
            topic: Sujet principal du vault.
        """
        # Créer index.md
        index_page = IndexPage(
            type="index",
            name="Vault Index",
            description=f"Catalogue complet du vault - {topic}",
            generated=datetime.now(),
            version="1.0.0",
            statistics={},
            pages_by_type={},
            pages_by_tag={},
            pages_by_date={},
        )
        
        index_content = self._page_to_markdown(index_page)
        self.file_manager.write_file(
            self.vault_path / "wiki" / "index.md",
            index_content,
        )
        
        # Créer log.md
        log_page = LogPage(
            type="log",
            name="Vault Log",
            description=f"Journal des opérations du vault - {topic}",
            created=datetime.now(),
            entries=[],
        )
        
        log_content = self._page_to_markdown(log_page)
        self.file_manager.write_file(
            self.vault_path / "wiki" / "log.md",
            log_content,
        )
    
    def _create_templates(self) -> None:
        """Créer les templates de pages."""
        templates_dir = self.vault_path / "templates"
        templates_dir.mkdir(exist_ok=True)
        
        # Template Entité
        entity_template = """---
type: entity
entity_type: <person|organization|place|product|project|event>
name: <nom>
description: <description>
aliases:
  - <alias_1>
  - <alias_2>
tags:
  - <tag_1>
  - <tag_2>
related:
  - <page_liée_1>
  - <page_liée_2>
sources:
  - <source_1>
  - <source_2>
created: {{date}}
updated: {{date}}
---

# {{name}}

## Description
{{description}}

## Contexte
[Contexte historique et importance]

## Relations
- [Liste des relations]

## Contributions/Activités
- [Liste des contributions ou activités]

## Références
- [[<source_1>]]
- [[<source_2>]]
"""
        self.file_manager.write_file(
            templates_dir / "entity_template.md",
            entity_template,
        )
        
        # Template Concept
        concept_template = """---
type: concept
name: <nom>
description: <description>
categories:
  - <catégorie_1>
  - <catégorie_2>
tags:
  - <tag_1>
  - <tag_2>
related:
  - <page_liée_1>
  - <page_liée_2>
sources:
  - <source_1>
  - <source_2>
status: <active|deprecated|obsolete>
authority: <high|medium|low|speculative>
created: {{date}}
updated: {{date}}
---

# {{name}}

## Définition
[Définition claire et concise]

## Contexte
[Contexte historique et développement]

## Fonctionnement
[Explication du fonctionnement interne]

### Sous-sections
[Développement détaillé]

## Applications
- [Liste des applications]

## Avantages
- [Liste des avantages]

## Limites
- [Liste des limites]

## Variantes
- [[<variante_1>]]
- [[<variante_2>]]

## Références
- [[<source_1>]]
- [[<source_2>]]
"""
        self.file_manager.write_file(
            templates_dir / "concept_template.md",
            concept_template,
        )
        
        # Template Source
        source_template = """---
type: source
source_type: <paper|book|article|video|podcast|interview|doc|web>
original_path: <chemin_original>
title: <titre>
authors:
  - <auteur_1>
  - <auteur_2>
date: <date>
url: <url>
doi: <doi>
summary: <résumé>
status: processed
tags:
  - <tag_1>
  - <tag_2>
related:
  - <page_liée_1>
  - <page_liée_2>
sources: []
created: {{date}}
updated: {{date}}
ingested: {{date}}
---

# {{title}}

## Métadonnées
- **Auteurs :** {{authors}}
- **Date :** {{date}}
- **Type :** {{source_type}}
- **URL :** [{{url}}]({{url}})

## Résumé
{{summary}}

## Points clés
- [Liste des points clés extraits]

## Citations
[Extraits importants avec citations de page/section]

## Analyse
[Analyse et interprétation]

## Connexions
- **Concepts liés :** [Liste]
- **Entités liées :** [Liste]
- **Sources connexes :** [Liste]

## Notes
[Notes supplémentaires et réflexions]
"""
        self.file_manager.write_file(
            templates_dir / "source_template.md",
            source_template,
        )
        
        # Template Comparaison
        comparison_template = """---
type: comparison
name: <nom>
description: <description>
subjects:
  - <sujet_1>
  - <sujet_2>
criteria:
  - <critère_1>
  - <critère_2>
tags:
  - <tag_1>
  - <tag_2>
related:
  - <page_liée_1>
  - <page_liée_2>
sources:
  - <source_1>
  - <source_2>
created: {{date}}
updated: {{date}}
---

# {{name}}

## Introduction
[Introduction au sujet de la comparaison]

## Critères de comparaison

### <Critère 1>
[Analyse détaillée]

### <Critère 2>
[Analyse détaillée]

## Avantages et inconvénients

### <Sujet 1>
**Avantages:**
- [Liste]

**Inconvénients:**
- [Liste]

### <Sujet 2>
**Avantages:**
- [Liste]

**Inconvénients:**
- [Liste]

## Conclusion
[Conclusion et recommandations]

## Références
- [[<source_1>]]
- [[<source_2>]]
"""
        self.file_manager.write_file(
            templates_dir / "comparison_template.md",
            comparison_template,
        )
        
        # Template Synthèse
        synthesis_template = """---
type: synthesis
name: <nom>
description: <description>
domain: <domaine>
scope: <portée>
tags:
  - <tag_1>
  - <tag_2>
related:
  - <page_liée_1>
  - <page_liée_2>
sources:
  - <source_1>
  - <source_2>
status: <current|draft|outdated>
confidence: <high|medium|low>
created: {{date}}
updated: {{date}}
---

# {{name}}

## Executive Summary
[Résumé exécutif]

## Contexte
[Contexte et importance du sujet]

## État de l'art
[Vue d'ensemble de l'état actuel]

### Approches principales
- [[<approche_1>]]
- [[<approche_2>]]

### Défis actuels
- [Liste des défis]

## Tendances
[Analyse des tendances]

## Prédictions
[Prédictions pour l'avenir]

## Recommandations
[Recommandations stratégiques]

## Références
- [[<source_1>]]
- [[<source_2>]]
- [[<page_liée_1>]]
"""
        self.file_manager.write_file(
            templates_dir / "synthesis_template.md",
            synthesis_template,
        )
    
    def save_page(self, page_path: Path, content: str) -> None:
        """
        Sauvegarder une page.
        
        Args:
            page_path: Chemin de la page.
            content: Contenu de la page.
        """
        self.file_manager.write_file(page_path, content)
    
    def read_page_content(self, page_path: Path) -> Optional[str]:
        """
        Lire le contenu d'une page.
        
        Args:
            page_path: Chemin de la page.
            
        Returns:
            Contenu de la page ou None.
        """
        return self.file_manager.read_file(page_path)
    
    def get_page(self, page_path: Path) -> Optional[Page]:
        """
        Obtenir une page à partir de son chemin.
        
        Args:
            page_path: Chemin de la page.
            
        Returns:
            Page ou None.
        """
        content = self.read_page_content(page_path)
        if content is None:
            return None
        
        return self._parse_page(content, page_path)
    
    def _parse_page(self, content: str, page_path: Path) -> Optional[Page]:
        """
        Parser le contenu d'une page.
        
        Args:
            content: Contenu de la page.
            page_path: Chemin de la page.
            
        Returns:
            Page ou None.
        """
        # Extraire le frontmatter
        if not content.startswith("---"):
            return None
        
        try:
            # Séparer le frontmatter du contenu
            parts = content.split("---", 2)
            if len(parts) < 3:
                return None
            
            frontmatter_str = parts[1]
            frontmatter = yaml.safe_load(frontmatter_str)
            
            if frontmatter is None:
                return None
            
            # Déterminer le type de page
            page_type = frontmatter.get("type", "unknown")
            
            # Créer la page appropriée
            if page_type == "entity":
                return EntityPage(**frontmatter)
            elif page_type == "concept":
                return ConceptPage(**frontmatter)
            elif page_type == "source":
                return SourcePage(**frontmatter)
            elif page_type == "comparison":
                return ComparisonPage(**frontmatter)
            elif page_type == "synthesis":
                return SynthesisPage(**frontmatter)
            elif page_type == "index":
                return IndexPage(**frontmatter)
            elif page_type == "log":
                return LogPage(**frontmatter)
            else:
                return None
                
        except Exception:
            return None
    
    def _page_to_markdown(self, page: Page) -> str:
        """
        Convertir une page en markdown.
        
        Args:
            page: Page à convertir.
            
        Returns:
            Contenu markdown.
        """
        # Convertir le dataclass en dict
        page_dict = page.__dict__.copy()
        
        # Convertir les datetime en strings
        for key, value in page_dict.items():
            if isinstance(value, datetime):
                page_dict[key] = value.isoformat()
            elif isinstance(value, list):
                page_dict[key] = [str(v) for v in value]
        
        # Générer le frontmatter
        frontmatter = yaml.dump(
            page_dict,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        
        # Générer le contenu
        content = f"""---
{frontmatter}---

{self._generate_page_content(page)}
"""
        
        return content
    
    def _generate_page_content(self, page: Page) -> str:
        """
        Générer le contenu markdown d'une page.
        
        Args:
            page: Page.
            
        Returns:
            Contenu markdown.
        """
        # Contenu par défaut
        return f"# {page.name}\n\n{page.description}"
    
    def get_all_pages(self) -> List[Path]:
        """
        Obtenir tous les chemins de pages dans le vault.
        
        Returns:
            Liste des chemins.
        """
        all_pages = []
        
        # Parcourir tous les fichiers markdown dans wiki/
        for root, _, files in os.walk(self.vault_path / "wiki"):
            for file in files:
                if file.endswith(".md"):
                    all_pages.append(Path(root) / file)
        
        return all_pages
    
    def get_pages_by_type(self, page_type: str) -> List[Path]:
        """
        Obtenir les pages d'un type spécifique.
        
        Args:
            page_type: Type de page.
            
        Returns:
            Liste des chemins.
        """
        pages = []
        
        type_to_dir = {
            "entity": "entities",
            "concept": "concepts",
            "source": "sources",
            "comparison": "comparisons",
            "synthesis": "synthesis",
        }
        
        if page_type in type_to_dir:
            base_dir = self.vault_path / "wiki" / type_to_dir[page_type]
            if base_dir.exists():
                for root, _, files in os.walk(base_dir):
                    for file in files:
                        if file.endswith(".md"):
                            pages.append(Path(root) / file)
        elif page_type == "index":
            index_path = self.vault_path / "wiki" / "index.md"
            if index_path.exists():
                pages.append(index_path)
        elif page_type == "log":
            log_path = self.vault_path / "wiki" / "log.md"
            if log_path.exists():
                pages.append(log_path)
        
        return pages
    
    def get_pages_by_tag(self, tag: str) -> List[Path]:
        """
        Obtenir les pages avec un tag spécifique.
        
        Args:
            tag: Tag à rechercher.
            
        Returns:
            Liste des chemins.
        """
        pages = []
        
        all_pages = self.get_all_pages()
        for page_path in all_pages:
            page = self.get_page(page_path)
            if page and tag in page.tags:
                pages.append(page_path)
        
        return pages
    
    def get_sources(self) -> List[str]:
        """
        Obtenir la liste de toutes les sources.
        
        Returns:
            Liste des identifiants de sources.
        """
        sources = []
        
        source_pages = self.get_pages_by_type("source")
        for page_path in source_pages:
            page = self.get_page(page_path)
            if page and hasattr(page, "name"):
                sources.append(page.name)
        
        return sources
    
    def source_exists(self, source_id: str) -> bool:
        """
        Vérifier si une source existe.
        
        Args:
            source_id: Identifiant de la source.
            
        Returns:
            True si la source existe.
        """
        source_path = self.vault_path / "wiki" / "sources" / f"{source_id}.md"
        return source_path.exists()
    
    def update_page_related(self, page_path: Path, related: List[str]) -> None:
        """
        Mettre à jour les références liées d'une page.
        
        Args:
            page_path: Chemin de la page.
            related: Liste des pages liées.
        """
        page = self.get_page(page_path)
        if page:
            page.related = related
            page.updated = datetime.now()
            
            # Sauvegarder la page
            content = self._page_to_markdown(page)
            self.save_page(page_path, content)
    
    def append_log_entry(self, entry: Dict[str, Any]) -> None:
        """
        Ajouter une entrée dans le log.
        
        Args:
            entry: Entrée de log.
        """
        log_path = self.vault_path / "wiki" / "log.md"
        
        # Lire le contenu existant
        content = self.read_page_content(log_path)
        
        if content is None:
            # Créer un nouveau log
            log_page = LogPage(
                type="log",
                name="Vault Log",
                description="Journal des opérations du vault",
                created=datetime.now(),
                entries=[entry],
            )
            content = self._page_to_markdown(log_page)
        else:
            # Parser le log existant
            page = self.get_page(log_path)
            if page and hasattr(page, "entries"):
                page.entries.append(entry)
                page.updated = datetime.now()
                content = self._page_to_markdown(page)
            else:
                # Ajouter manuellement
                content = content.rstrip() + "\n\n" + yaml.dump(entry, default_flow_style=False)
        
        # Sauvegarder
        self.save_page(log_path, content)
    
    def get_vault_stats(self) -> Dict[str, Any]:
        """
        Obtenir les statistiques du vault.
        
        Returns:
            Dictionnaire avec les statistiques.
        """
        stats = {
            "total_pages": 0,
            "pages_by_type": {},
            "pages_by_tag": {},
            "total_size": 0,
        }
        
        # Compter les pages par type
        for page_type in ["entity", "concept", "source", "comparison", "synthesis", "index", "log"]:
            pages = self.get_pages_by_type(page_type)
            stats["pages_by_type"][page_type] = len(pages)
            stats["total_pages"] += len(pages)
        
        # Compter les pages par tag
        all_pages = self.get_all_pages()
        for page_path in all_pages:
            page = self.get_page(page_path)
            if page and page.tags:
                for tag in page.tags:
                    stats["pages_by_tag"][tag] = stats["pages_by_tag"].get(tag, 0) + 1
        
        # Calculer la taille totale
        for page_path in all_pages:
            if page_path.exists():
                stats["total_size"] += page_path.stat().st_size
        
        return stats
    
    def search(
        self,
        query: str,
        page_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Page]:
        """
        Rechercher des pages dans le vault.
        
        Args:
            query: Requête de recherche.
            page_types: Types de pages à filtrer.
            tags: Tags à filtrer.
            limit: Nombre maximal de résultats.
            
        Returns:
            Liste des pages correspondantes.
        """
        results = []
        
        # Obtenir toutes les pages ou filtrer par type
        if page_types:
            for page_type in page_types:
                results.extend(self.get_pages_by_type(page_type))
        else:
            results = self.get_all_pages()
        
        # Filtrer par tags
        if tags:
            filtered_results = []
            for page_path in results:
                page = self.get_page(page_path)
                if page and any(tag in page.tags for tag in tags):
                    filtered_results.append(page_path)
            results = filtered_results
        
        # Limiter les résultats
        results = results[:limit]
        
        # Charger les pages
        pages = []
        for page_path in results:
            page = self.get_page(page_path)
            if page:
                pages.append(page)
        
        return pages
    
    def close(self) -> None:
        """Fermer les ressources du VaultManager."""
        self.file_manager.close()
