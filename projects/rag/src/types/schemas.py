"""
Schémas Pydantic pour la validation des pages.
"""

from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

from .enums import (
    PageTypeEnum,
    EntityTypeEnum,
    SourceTypeEnum,
    PageStatusEnum,
    AuthorityLevel,
    ConfidenceLevel,
)


class PageSchema(BaseModel):
    """Schéma de base pour toutes les pages."""
    type: PageTypeEnum
    name: str
    description: str
    tags: List[str] = []
    related: List[str] = []
    created: datetime
    updated: datetime
    sources: List[str] = []

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        if not all(isinstance(tag, str) and tag.strip() for tag in v):
            raise ValueError("Tous les tags doivent être des chaînes non vides")
        return [tag.strip().lower() for tag in v]


class EntityPageSchema(PageSchema):
    """Schéma pour les pages d'entités."""
    type: PageTypeEnum = PageTypeEnum.ENTITY
    entity_type: EntityTypeEnum
    aliases: List[str] = []

    @field_validator('aliases')
    @classmethod
    def validate_aliases(cls, v: List[str]) -> List[str]:
        if not all(isinstance(alias, str) and alias.strip() for alias in v):
            raise ValueError("Tous les aliases doivent être des chaînes non vides")
        return [alias.strip() for alias in v]


class ConceptPageSchema(PageSchema):
    """Schéma pour les pages de concepts."""
    type: PageTypeEnum = PageTypeEnum.CONCEPT
    categories: List[str] = []
    status: PageStatusEnum = PageStatusEnum.ACTIVE
    authority: AuthorityLevel = AuthorityLevel.MEDIUM


class SourcePageSchema(PageSchema):
    """Schéma pour les pages de sources."""
    type: PageTypeEnum = PageTypeEnum.SOURCE
    source_type: SourceTypeEnum
    original_path: str
    title: str
    authors: List[str] = []
    date: Optional[datetime] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    summary: str
    ingested: datetime


class ComparisonPageSchema(PageSchema):
    """Schéma pour les pages de comparaisons."""
    type: PageTypeEnum = PageTypeEnum.COMPARISON
    subjects: List[str]
    criteria: List[str] = []


class SynthesisPageSchema(PageSchema):
    """Schéma pour les pages de synthèse."""
    type: PageTypeEnum = PageTypeEnum.SYNTHESIS
    domain: str
    scope: str
    status: PageStatusEnum = PageStatusEnum.CURRENT
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class IndexPageSchema(BaseModel):
    """Schéma pour la page d'index."""
    type: PageTypeEnum = PageTypeEnum.INDEX
    name: str = "Vault Index"
    description: str = "Catalogue complet du vault"
    generated: datetime
    version: str
    statistics: Dict[str, Any] = {}
    pages_by_type: Dict[str, List[str]] = {}
    pages_by_tag: Dict[str, List[str]] = {}
    pages_by_date: Dict[str, List[str]] = {}


class LogPageSchema(BaseModel):
    """Schéma pour la page de log."""
    type: PageTypeEnum = PageTypeEnum.LOG
    name: str = "Vault Log"
    description: str = "Journal des opérations du vault"
    created: datetime
    entries: List[Dict[str, Any]] = []


# Schémas pour la validation
page_schema = PageSchema.model_json_schema()
entity_page_schema = EntityPageSchema.model_json_schema()
concept_page_schema = ConceptPageSchema.model_json_schema()
source_page_schema = SourcePageSchema.model_json_schema()
comparison_page_schema = ComparisonPageSchema.model_json_schema()
synthesis_page_schema = SynthesisPageSchema.model_json_schema()
index_page_schema = IndexPageSchema.model_json_schema()
log_page_schema = LogPageSchema.model_json_schema()


# Fonctions de validation
def validate_page_schema(page_type: PageTypeEnum, data: Dict[str, Any]) -> bool:
    """Valider les données d'une page selon son type."""
    schema_map = {
        PageTypeEnum.ENTITY: entity_page_schema,
        PageTypeEnum.CONCEPT: concept_page_schema,
        PageTypeEnum.SOURCE: source_page_schema,
        PageTypeEnum.COMPARISON: comparison_page_schema,
        PageTypeEnum.SYNTHESIS: synthesis_page_schema,
        PageTypeEnum.INDEX: index_page_schema,
        PageTypeEnum.LOG: log_page_schema,
    }
    
    schema = schema_map.get(page_type)
    if schema is None:
        raise ValueError(f"Type de page inconnu: {page_type}")
    
    # Validation avec Pydantic
    try:
        if page_type == PageTypeEnum.ENTITY:
            EntityPageSchema(**data)
        elif page_type == PageTypeEnum.CONCEPT:
            ConceptPageSchema(**data)
        elif page_type == PageTypeEnum.SOURCE:
            SourcePageSchema(**data)
        elif page_type == PageTypeEnum.COMPARISON:
            ComparisonPageSchema(**data)
        elif page_type == PageTypeEnum.SYNTHESIS:
            SynthesisPageSchema(**data)
        elif page_type == PageTypeEnum.INDEX:
            IndexPageSchema(**data)
        elif page_type == PageTypeEnum.LOG:
            LogPageSchema(**data)
        return True
    except Exception as e:
        raise ValueError(f"Validation échouée pour {page_type}: {str(e)}")


def get_schema_for_type(page_type: PageTypeEnum) -> Dict[str, Any]:
    """Obtenir le schéma JSON pour un type de page."""
    schema_map = {
        PageTypeEnum.ENTITY: entity_page_schema,
        PageTypeEnum.CONCEPT: concept_page_schema,
        PageTypeEnum.SOURCE: source_page_schema,
        PageTypeEnum.COMPARISON: comparison_page_schema,
        PageTypeEnum.SYNTHESIS: synthesis_page_schema,
        PageTypeEnum.INDEX: index_page_schema,
        PageTypeEnum.LOG: log_page_schema,
    }
    
    schema = schema_map.get(page_type)
    if schema is None:
        raise ValueError(f"Type de page inconnu: {page_type}")
    
    return schema
