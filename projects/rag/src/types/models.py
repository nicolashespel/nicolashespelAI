"""
Modèles de données pour le système RAG Wiki.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator

from .enums import (
    AuthorityLevel,
    ConfidenceLevel,
    EntityTypeEnum,
    PageStatusEnum,
    PageTypeEnum,
    SourceTypeEnum,
)


class PageType(BaseModel):
    """Type de page."""
    type: PageTypeEnum


class EntityType(BaseModel):
    """Type d'entité."""
    entity_type: EntityTypeEnum


class SourceType(BaseModel):
    """Type de source."""
    source_type: SourceTypeEnum


class PageStatus(BaseModel):
    """Statut de page."""
    status: PageStatusEnum


class BasePage(BaseModel):
    """Modèle de base pour toutes les pages."""
    type: PageTypeEnum = Field(..., description="Type de la page")
    name: str = Field(..., description="Nom de la page")
    description: str = Field(..., description="Description de la page")
    tags: List[str] = Field(default_factory=list, description="Tags de la page")
    related: List[str] = Field(default_factory=list, description="Pages liées")
    created: datetime = Field(..., description="Date de création")
    updated: datetime = Field(..., description="Date de dernière mise à jour")
    sources: List[str] = Field(default_factory=list, description="Sources de la page")

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Valider que les tags sont des chaînes non vides."""
        if not all(isinstance(tag, str) and tag.strip() for tag in v):
            raise ValueError("Tous les tags doivent être des chaînes non vides")
        return [tag.strip().lower() for tag in v]

    @field_validator('related')
    @classmethod
    def validate_related(cls, v: List[str]) -> List[str]:
        """Valider que les pages liées sont des chaînes non vides."""
        if not all(isinstance(page, str) and page.strip() for page in v):
            raise ValueError("Toutes les pages liées doivent être des chaînes non vides")
        return [page.strip() for page in v]


class EntityPage(BasePage):
    """Modèle pour les pages d'entités."""
    type: PageTypeEnum = Field(default=PageTypeEnum.ENTITY, description="Type de la page")
    entity_type: EntityTypeEnum = Field(..., description="Type d'entité")
    aliases: List[str] = Field(default_factory=list, description="Aliases de l'entité")

    @field_validator('aliases')
    @classmethod
    def validate_aliases(cls, v: List[str]) -> List[str]:
        """Valider que les aliases sont des chaînes non vides."""
        if not all(isinstance(alias, str) and alias.strip() for alias in v):
            raise ValueError("Tous les aliases doivent être des chaînes non vides")
        return [alias.strip() for alias in v]


class ConceptPage(BasePage):
    """Modèle pour les pages de concepts."""
    type: PageTypeEnum = Field(default=PageTypeEnum.CONCEPT, description="Type de la page")
    categories: List[str] = Field(default_factory=list, description="Catégories du concept")
    status: PageStatusEnum = Field(default=PageStatusEnum.ACTIVE, description="Statut du concept")
    authority: AuthorityLevel = Field(default=AuthorityLevel.MEDIUM, description="Niveau d'autorité")


class SourcePage(BasePage):
    """Modèle pour les pages de sources."""
    type: PageTypeEnum = Field(default=PageTypeEnum.SOURCE, description="Type de la page")
    source_type: SourceTypeEnum = Field(..., description="Type de source")
    original_path: str = Field(..., description="Chemin original de la source")
    title: str = Field(..., description="Titre de la source")
    authors: List[str] = Field(default_factory=list, description="Auteurs de la source")
    date: Optional[datetime] = Field(default=None, description="Date de la source")
    url: Optional[str] = Field(default=None, description="URL de la source")
    doi: Optional[str] = Field(default=None, description="DOI de la source")
    summary: str = Field(..., description="Résumé de la source")
    ingested: datetime = Field(..., description="Date d'ingestion")


class ComparisonPage(BasePage):
    """Modèle pour les pages de comparaisons."""
    type: PageTypeEnum = Field(default=PageTypeEnum.COMPARISON, description="Type de la page")
    subjects: List[str] = Field(..., description="Sujets de la comparaison")
    criteria: List[str] = Field(default_factory=list, description="Critères de comparaison")


class SynthesisPage(BasePage):
    """Modèle pour les pages de synthèse."""
    type: PageTypeEnum = Field(default=PageTypeEnum.SYNTHESIS, description="Type de la page")
    domain: str = Field(..., description="Domaine de la synthèse")
    scope: str = Field(..., description="Portée de la synthèse")
    status: PageStatusEnum = Field(default=PageStatusEnum.CURRENT, description="Statut de la synthèse")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="Niveau de confiance")


class IndexPage(BaseModel):
    """Modèle pour la page d'index."""
    type: PageTypeEnum = Field(default=PageTypeEnum.INDEX, description="Type de la page")
    name: str = Field(default="Vault Index", description="Nom de l'index")
    description: str = Field(default="Catalogue complet du vault", description="Description")
    generated: datetime = Field(..., description="Date de génération")
    version: str = Field(..., description="Version de l'index")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="Statistiques du vault")
    pages_by_type: Dict[str, List[str]] = Field(default_factory=dict, description="Pages par type")
    pages_by_tag: Dict[str, List[str]] = Field(default_factory=dict, description="Pages par tag")
    pages_by_date: Dict[str, List[str]] = Field(default_factory=dict, description="Pages par date")


class LogPage(BaseModel):
    """Modèle pour la page de log."""
    type: PageTypeEnum = Field(default=PageTypeEnum.LOG, description="Type de la page")
    name: str = Field(default="Vault Log", description="Nom du log")
    description: str = Field(default="Journal des opérations du vault", description="Description")
    created: datetime = Field(..., description="Date de création")
    entries: List[Dict[str, Any]] = Field(default_factory=list, description="Entrées de log")


class VaultConfig(BaseModel):
    """Configuration du vault."""
    path: str = Field(..., description="Chemin du vault")
    topic: str = Field(..., description="Sujet principal du vault")
    tool: str = Field(default="all", description="Outil LLM à configurer")
    embedding_model: Optional[str] = Field(default=None, description="Modèle d'embedding")
    llm_model: Optional[str] = Field(default=None, description="Modèle LLM")
    max_tokens: int = Field(default=4096, description="Nombre maximal de tokens")
    temperature: float = Field(default=0.7, description="Température du LLM")


class IngestResult(BaseModel):
    """Résultat d'une opération d'ingestion."""
    success: bool = Field(..., description="Succès de l'opération")
    source_path: str = Field(..., description="Chemin de la source")
    summary_page: str = Field(..., description="Page de résumé créée")
    updated_pages: List[str] = Field(default_factory=list, description="Pages mises à jour")
    cross_references: List[str] = Field(default_factory=list, description="Références croisées")
    duration_seconds: float = Field(..., description="Durée en secondes")
    error: Optional[str] = Field(default=None, description="Erreur éventuelle")


class QueryResult(BaseModel):
    """Résultat d'une opération de requête."""
    success: bool = Field(..., description="Succès de l'opération")
    query: str = Field(..., description="Requête effectuée")
    answer: str = Field(..., description="Réponse générée")
    cited_pages: List[str] = Field(default_factory=list, description="Pages citées")
    duration_seconds: float = Field(..., description="Durée en secondes")
    error: Optional[str] = Field(default=None, description="Erreur éventuelle")


class LintResult(BaseModel):
    """Résultat d'une opération de linting."""
    success: bool = Field(..., description="Succès de l'opération")
    issues: List[Dict[str, Any]] = Field(default_factory=list, description="Problèmes détectés")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="Avertissements")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Erreurs")
    duration_seconds: float = Field(..., description="Durée en secondes")


# Union type pour toutes les pages
Page = Union[EntityPage, ConceptPage, SourcePage, ComparisonPage, SynthesisPage, IndexPage, LogPage]
