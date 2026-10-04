"""
Pipeline d'ingestion pour le système RAG Wiki.

Ce module contient la classe IngestPipeline qui gère le processus complet
d'ingestion d'une source dans le vault.
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..types import (
    IngestResult,
    SourcePage,
    EntityPage,
    ConceptPage,
    PageTypeEnum,
    SourceTypeEnum,
    EntityTypeEnum,
)
from ..storage import VaultManager
from ..indexes import IndexManager
from ..sources import SourceParser, get_parser_for_type
from ..pages import PageFactory
from .config import WikiConfig
from .prompts import WIKI_INGESTOR_PROMPT


class IngestPipeline:
    """
    Pipeline d'ingestion pour le système RAG Wiki.
    
    Ce pipeline gère le processus complet d'ingestion d'une source :
    1. Lecture et parsing de la source
    2. Extraction des métadonnées et du contenu
    3. Discussion avec l'utilisateur (optionnelle)
    4. Création de la page source
    5. Mise à jour ou création des pages d'entités et de concepts
    6. Mise à jour de l'index
    7. Logging de l'opération
    """
    
    def __init__(
        self,
        vault_manager: VaultManager,
        index_manager: IndexManager,
        config: WikiConfig,
    ) -> None:
        """
        Initialiser le pipeline d'ingestion.
        
        Args:
            vault_manager: Gestionnaire du vault.
            index_manager: Gestionnaire des index.
            config: Configuration du wiki.
        """
        self.vault_manager = vault_manager
        self.index_manager = index_manager
        self.config = config
        self.page_factory = PageFactory()
    
    async def ingest(
        self,
        source_path: Path,
        discuss_with_user: bool = True,
    ) -> IngestResult:
        """
        Ingestion d'une source.
        
        Args:
            source_path: Chemin vers la source à ingérer.
            discuss_with_user: Si True, discuter avec l'utilisateur avant l'ingestion.
            
        Returns:
            Résultat de l'ingestion.
        """
        start_time = time.time()
        
        try:
            # Étape 1: Valider la source
            if not source_path.exists():
                return IngestResult(
                    success=False,
                    source_path=str(source_path),
                    summary_page="",
                    duration_seconds=time.time() - start_time,
                    error=f"Source non trouvée: {source_path}",
                )
            
            # Étape 2: Déterminer le type de source
            source_type = self._determine_source_type(source_path)
            
            # Étape 3: Parser la source
            parser = get_parser_for_type(source_type)
            parsed_source = await parser.parse(source_path)
            
            if not parsed_source:
                return IngestResult(
                    success=False,
                    source_path=str(source_path),
                    summary_page="",
                    duration_seconds=time.time() - start_time,
                    error=f"Échec du parsing de {source_path}",
                )
            
            # Étape 4: Extraire les métadonnées
            metadata = self._extract_metadata(parsed_source, source_path)
            
            # Étape 5: Générer un identifiant unique pour la source
            source_id = self._generate_source_id(metadata)
            
            # Étape 6: Vérifier si la source a déjà été ingérée
            if self.vault_manager.source_exists(source_id):
                return IngestResult(
                    success=False,
                    source_path=str(source_path),
                    summary_page="",
                    duration_seconds=time.time() - start_time,
                    error=f"Source déjà ingérée: {source_id}",
                )
            
            # Étape 7: Discuter avec l'utilisateur (optionnelle)
            if discuss_with_user:
                await self._discuss_with_user(parsed_source, metadata)
            
            # Étape 8: Créer la page source
            summary_page_path = await self._create_source_page(
                parsed_source, metadata, source_id
            )
            
            # Étape 9: Extraire et créer/mettre à jour les entités et concepts
            updated_pages, cross_references = await self._process_entities_and_concepts(
                parsed_source, metadata, source_id
            )
            
            # Étape 10: Mettre à jour l'index
            self.index_manager.update_index()
            
            # Étape 11: Logger l'opération
            self.vault_manager.append_log_entry({
                "timestamp": datetime.now().isoformat(),
                "operation": "ingest",
                "source_path": str(source_path),
                "source_id": source_id,
                "summary_page": str(summary_page_path),
                "updated_pages": [str(p) for p in updated_pages],
                "cross_references": cross_references,
                "duration_seconds": round(time.time() - start_time, 2),
                "success": True,
            })
            
            return IngestResult(
                success=True,
                source_path=str(source_path),
                summary_page=str(summary_page_path),
                updated_pages=[str(p) for p in updated_pages],
                cross_references=cross_references,
                duration_seconds=time.time() - start_time,
            )
            
        except Exception as e:
            return IngestResult(
                success=False,
                source_path=str(source_path),
                summary_page="",
                duration_seconds=time.time() - start_time,
                error=str(e),
            )
    
    def _determine_source_type(self, source_path: Path) -> str:
        """
        Déterminer le type de source à partir du chemin.
        
        Args:
            source_path: Chemin de la source.
            
        Returns:
            Type de source.
        """
        suffix = source_path.suffix.lower()
        
        if suffix == ".pdf":
            return "pdf"
        elif suffix in [".html", ".htm"]:
            return "html"
        elif suffix == ".md":
            return "markdown"
        elif suffix == ".txt":
            return "text"
        else:
            return "unknown"
    
    def _extract_metadata(
        self,
        parsed_source: Dict[str, Any],
        source_path: Path,
    ) -> Dict[str, Any]:
        """
        Extraire les métadonnées de la source parsée.
        
        Args:
            parsed_source: Source parsée.
            source_path: Chemin de la source.
            
        Returns:
            Métadonnées extraites.
        """
        metadata = {
            "original_path": str(source_path.relative_to(self.config.vault_path / "raw")),
            "title": parsed_source.get("title", source_path.stem),
            "authors": parsed_source.get("authors", []),
            "date": parsed_source.get("date"),
            "url": parsed_source.get("url"),
            "doi": parsed_source.get("doi"),
            "summary": parsed_source.get("summary", ""),
            "content": parsed_source.get("content", ""),
            "source_type": self._map_to_source_type(source_path),
        }
        
        return metadata
    
    def _map_to_source_type(self, source_path: Path) -> SourceTypeEnum:
        """
        Mapper le type de fichier au SourceTypeEnum.
        
        Args:
            source_path: Chemin de la source.
            
        Returns:
            SourceTypeEnum.
        """
        suffix = source_path.suffix.lower()
        
        if suffix == ".pdf":
            return SourceTypeEnum.PAPER
        elif suffix in [".html", ".htm"]:
            return SourceTypeEnum.WEB
        elif suffix == ".md":
            return SourceTypeEnum.DOC
        elif suffix == ".txt":
            return SourceTypeEnum.DOC
        else:
            return SourceTypeEnum.DOC
    
    def _generate_source_id(self, metadata: Dict[str, Any]) -> str:
        """
        Générer un identifiant unique pour la source.
        
        Args:
            metadata: Métadonnées de la source.
            
        Returns:
            Identifiant unique.
        """
        from ..utils.text_utils import normalize_name
        
        source_type = metadata.get("source_type", "doc").value
        title = metadata.get("title", "unknown")
        date = datetime.now().strftime("%Y_%m_%d")
        
        # Générer un identifiant unique basé sur le titre et la date
        normalized_title = normalize_name(title)
        
        # Trouver un numéro de séquence unique
        existing_sources = self.vault_manager.get_sources()
        sequence = 0
        while True:
            source_id = f"{source_type}_{date}_{sequence:03d}_{normalized_title}"
            if source_id not in existing_sources:
                break
            sequence += 1
        
        return source_id
    
    async def _discuss_with_user(
        self,
        parsed_source: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> None:
        """
        Discuter avec l'utilisateur avant l'ingestion.
        
        Args:
            parsed_source: Source parsée.
            metadata: Métadonnées extraites.
        """
        # Dans une implémentation réelle, cela interagirait avec l'interface LLM
        # Pour l'instant, on simule une discussion basique
        print(f"\n=== Discussion pour: {metadata['title']} ===")
        print(f"Type: {metadata['source_type']}")
        print(f"Auteurs: {', '.join(metadata['authors']) if metadata['authors'] else 'Inconnu'}")
        print(f"Résumé initial: {metadata['summary'][:200]}...")
        print("\nSouhaitez-vous continuer avec l'ingestion? (Oui/Non)")
        # En attente de l'implémentation de l'interface utilisateur
    
    async def _create_source_page(
        self,
        parsed_source: Dict[str, Any],
        metadata: Dict[str, Any],
        source_id: str,
    ) -> Path:
        """
        Créer la page source dans le vault.
        
        Args:
            parsed_source: Source parsée.
            metadata: Métadonnées extraites.
            source_id: Identifiant unique de la source.
            
        Returns:
            Chemin de la page source créée.
        """
        # Créer la page source
        source_page = SourcePage(
            type="source",
            source_type=metadata["source_type"],
            original_path=metadata["original_path"],
            title=metadata["title"],
            authors=metadata["authors"],
            date=metadata["date"],
            url=metadata["url"],
            doi=metadata["doi"],
            summary=metadata["summary"],
            created=datetime.now(),
            updated=datetime.now(),
            ingested=datetime.now(),
            tags=self._extract_tags(metadata),
            related=[],
            sources=[],
        )
        
        # Déterminer le chemin de la page
        source_type_str = metadata["source_type"].value
        date_str = datetime.now().strftime("%Y_%m_%d")
        
        # Créer le chemin: wiki/sources/{source_type}_{date}_{sequence}_{title}.md
        filename = f"{source_id}.md"
        page_path = self.config.wiki_path / "sources" / filename
        
        # Créer la page via le factory
        page_content = self.page_factory.create_source_page(source_page)
        
        # Sauvegarder la page
        self.vault_manager.save_page(page_path, page_content)
        
        return page_path
    
    def _extract_tags(self, metadata: Dict[str, Any]) -> List[str]:
        """
        Extraire les tags à partir des métadonnées.
        
        Args:
            metadata: Métadonnées de la source.
            
        Returns:
            Liste de tags.
        """
        tags = []
        
        # Extraire à partir du titre
        title = metadata.get("title", "").lower()
        if "transformer" in title:
            tags.append("transformers")
        if "attention" in title:
            tags.append("attention")
        if "llm" in title or "large language" in title:
            tags.append("llm")
        
        # Extraire à partir du type
        source_type = metadata.get("source_type", "")
        if source_type:
            tags.append(source_type.value)
        
        # Tags par défaut
        tags.extend(["ai", "research"])
        
        return list(set(tags))
    
    async def _process_entities_and_concepts(
        self,
        parsed_source: Dict[str, Any],
        metadata: Dict[str, Any],
        source_id: str,
    ) -> Tuple[List[Path], List[str]]:
        """
        Traiter les entités et concepts de la source.
        
        Args:
            parsed_source: Source parsée.
            metadata: Métadonnées extraites.
            source_id: Identifiant unique de la source.
            
        Returns:
            Tuple avec (pages mises à jour, références croisées).
        """
        updated_pages = []
        cross_references = []
        
        # Extraire les entités (personnes, organisations, etc.)
        entities = self._extract_entities(parsed_source)
        
        for entity in entities:
            entity_path = await self._process_entity(entity, source_id)
            if entity_path:
                updated_pages.append(entity_path)
                cross_references.append(f"entities/{entity_path.name}")
        
        # Extraire les concepts
        concepts = self._extract_concepts(parsed_source)
        
        for concept in concepts:
            concept_path = await self._process_concept(concept, source_id)
            if concept_path:
                updated_pages.append(concept_path)
                cross_references.append(f"concepts/{concept_path.name}")
        
        # Mettre à jour la page source avec les références
        source_page_path = self.config.wiki_path / "sources" / f"{source_id}.md"
        if source_page_path.exists():
            self.vault_manager.update_page_related(
                source_page_path,
                cross_references,
            )
        
        return updated_pages, cross_references
    
    def _extract_entities(self, parsed_source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extraire les entités de la source parsée.
        
        Args:
            parsed_source: Source parsée.
            
        Returns:
            Liste d'entités.
        """
        entities = []
        
        # Extraire les auteurs comme entités de type personne
        authors = parsed_source.get("authors", [])
        for author in authors:
            entities.append({
                "name": author,
                "type": EntityTypeEnum.PERSON,
                "description": f"Auteur de {parsed_source.get('title', 'une publication')}",
            })
        
        # Extraire les organisations mentionnées
        # (Dans une implémentation réelle, utiliser NER ou patterns)
        content = parsed_source.get("content", "")
        org_keywords = ["OpenAI", "Google", "Tesla", "Stanford", "MIT", "Harvard"]
        for keyword in org_keywords:
            if keyword in content:
                entities.append({
                    "name": keyword,
                    "type": EntityTypeEnum.ORGANIZATION,
                    "description": f"Organisation mentionnée dans {parsed_source.get('title', 'une publication')}",
                })
        
        return entities
    
    def _extract_concepts(self, parsed_source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extraire les concepts de la source parsée.
        
        Args:
            parsed_source: Source parsée.
            
        Returns:
            Liste de concepts.
        """
        concepts = []
        
        # Concepts basés sur le titre
        title = parsed_source.get("title", "").lower()
        
        concept_keywords = {
            "transformer": {
                "name": "Transformers",
                "description": "Architecture de réseau de neurones basée sur l'attention",
                "category": "deep-learning",
            },
            "attention": {
                "name": "Attention Mechanism",
                "description": "Mécanisme permettant aux modèles de se concentrer sur des parties pertinentes",
                "category": "deep-learning",
            },
            "llm": {
                "name": "Large Language Models",
                "description": "Modèles de langage de grande taille",
                "category": "nlp",
            },
            "neural network": {
                "name": "Neural Networks",
                "description": "Réseaux de neurones artificiels",
                "category": "machine-learning",
            },
        }
        
        for keyword, concept_info in concept_keywords.items():
            if keyword in title:
                concepts.append(concept_info)
        
        # Concepts basés sur le contenu
        content = parsed_source.get("content", "").lower()
        for keyword, concept_info in concept_keywords.items():
            if keyword in content and concept_info not in concepts:
                concepts.append(concept_info)
        
        return concepts
    
    async def _process_entity(
        self,
        entity: Dict[str, Any],
        source_id: str,
    ) -> Optional[Path]:
        """
        Traiter une entité.
        
        Args:
            entity: Entité à traiter.
            source_id: Identifiant de la source.
            
        Returns:
            Chemin de la page entité ou None.
        """
        from ..utils.text_utils import normalize_name
        
        # Normaliser le nom
        normalized_name = normalize_name(entity["name"])
        entity_type_str = entity["type"].value
        
        # Chemin de la page
        entity_path = self.config.wiki_path / "entities" / entity_type_str / f"{normalized_name}.md"
        
        # Vérifier si l'entité existe déjà
        if entity_path.exists():
            # Mettre à jour l'entité existante
            existing_page = self.vault_manager.get_page(entity_path)
            if existing_page:
                # Ajouter la source aux références
                if source_id not in existing_page.sources:
                    existing_page.sources.append(source_id)
                    existing_page.updated = datetime.now()
                    
                    # Mettre à jour la page
                    page_content = self.page_factory.create_entity_page(existing_page)
                    self.vault_manager.save_page(entity_path, page_content)
                    
                    return entity_path
        else:
            # Créer une nouvelle entité
            entity_page = EntityPage(
                type="entity",
                entity_type=entity["type"],
                name=entity["name"],
                description=entity["description"],
                aliases=[],
                created=datetime.now(),
                updated=datetime.now(),
                tags=[entity_type_str.lower()],
                related=[],
                sources=[source_id],
            )
            
            # Créer la page
            page_content = self.page_factory.create_entity_page(entity_page)
            self.vault_manager.save_page(entity_path, page_content)
            
            return entity_path
        
        return None
    
    async def _process_concept(
        self,
        concept: Dict[str, Any],
        source_id: str,
    ) -> Optional[Path]:
        """
        Traiter un concept.
        
        Args:
            concept: Concept à traiter.
            source_id: Identifiant de la source.
            
        Returns:
            Chemin de la page concept ou None.
        """
        from ..utils.text_utils import normalize_name
        
        # Normaliser le nom
        normalized_name = normalize_name(concept["name"])
        
        # Chemin de la page
        concept_path = self.config.wiki_path / "concepts" / f"{normalized_name}.md"
        
        # Vérifier si le concept existe déjà
        if concept_path.exists():
            # Mettre à jour le concept existant
            existing_page = self.vault_manager.get_page(concept_path)
            if existing_page:
                # Ajouter la source aux références
                if source_id not in existing_page.sources:
                    existing_page.sources.append(source_id)
                    existing_page.updated = datetime.now()
                    
                    # Mettre à jour la page
                    page_content = self.page_factory.create_concept_page(existing_page)
                    self.vault_manager.save_page(concept_path, page_content)
                    
                    return concept_path
        else:
            # Créer un nouveau concept
            concept_page = ConceptPage(
                type="concept",
                name=concept["name"],
                description=concept["description"],
                categories=[concept.get("category", "general")],
                created=datetime.now(),
                updated=datetime.now(),
                tags=["ai", "research"],
                related=[],
                sources=[source_id],
                status="active",
                authority="medium",
            )
            
            # Créer la page
            page_content = self.page_factory.create_concept_page(concept_page)
            self.vault_manager.save_page(concept_path, page_content)
            
            return concept_path
        
        return None
    
    async def close(self) -> None:
        """Fermer les ressources du pipeline."""
        pass
