"""
Énumérations pour le système RAG Wiki.
"""

from enum import Enum, auto


class PageTypeEnum(str, Enum):
    """Types de pages dans le vault."""
    ENTITY = "entity"
    CONCEPT = "concept"
    SOURCE = "source"
    COMPARISON = "comparison"
    SYNTHESIS = "synthesis"
    INDEX = "index"
    LOG = "log"


class EntityTypeEnum(str, Enum):
    """Types d'entités."""
    PERSON = "person"
    ORGANIZATION = "organization"
    PLACE = "place"
    PRODUCT = "product"
    PROJECT = "project"
    EVENT = "event"


class SourceTypeEnum(str, Enum):
    """Types de sources."""
    PAPER = "paper"
    BOOK = "book"
    ARTICLE = "article"
    VIDEO = "video"
    PODCAST = "podcast"
    INTERVIEW = "interview"
    DOC = "doc"
    WEB = "web"


class PageStatusEnum(str, Enum):
    """Statuts des pages."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    OBSOLETE = "obsolete"


class AuthorityLevel(str, Enum):
    """Niveaux d'autorité pour les concepts."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SPECULATIVE = "speculative"


class ConfidenceLevel(str, Enum):
    """Niveaux de confiance pour les synthèses."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RetrievalLayer(str, Enum):
    """Couches de récupération."""
    INDEX = "index"
    BM25 = "bm25"
    EMBEDDING = "embedding"


class OperationType(str, Enum):
    """Types d'opérations pour le logging."""
    INGEST = "ingest"
    QUERY = "query"
    LINT = "lint"
    INIT = "init"
    UPDATE = "update"


class LogLevel(str, Enum):
    """Niveaux de log."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
