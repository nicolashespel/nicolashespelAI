"""
Tests unitaires pour les types et modèles de données.
"""

import pytest
from datetime import datetime
from pathlib import Path
import sys

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from types.models import (
    EntityPage,
    ConceptPage,
    SourcePage,
    ComparisonPage,
    SynthesisPage,
    IndexPage,
    LogPage,
    VaultConfig,
    IngestResult,
    QueryResult,
    LintResult,
)
from types.enums import (
    PageTypeEnum,
    EntityTypeEnum,
    SourceTypeEnum,
    PageStatusEnum,
    AuthorityLevel,
    ConfidenceLevel,
)


class TestEnums:
    """Tests pour les énumérations."""
    
    def test_page_type_enum(self):
        """Tester PageTypeEnum."""
        assert PageTypeEnum.ENTITY.value == "entity"
        assert PageTypeEnum.CONCEPT.value == "concept"
        assert PageTypeEnum.SOURCE.value == "source"
        assert PageTypeEnum.COMPARISON.value == "comparison"
        assert PageTypeEnum.SYNTHESIS.value == "synthesis"
        assert PageTypeEnum.INDEX.value == "index"
        assert PageTypeEnum.LOG.value == "log"
    
    def test_entity_type_enum(self):
        """Tester EntityTypeEnum."""
        assert EntityTypeEnum.PERSON.value == "person"
        assert EntityTypeEnum.ORGANIZATION.value == "organization"
        assert EntityTypeEnum.PLACE.value == "place"
        assert EntityTypeEnum.PRODUCT.value == "product"
        assert EntityTypeEnum.PROJECT.value == "project"
        assert EntityTypeEnum.EVENT.value == "event"
    
    def test_source_type_enum(self):
        """Tester SourceTypeEnum."""
        assert SourceTypeEnum.PAPER.value == "paper"
        assert SourceTypeEnum.BOOK.value == "book"
        assert SourceTypeEnum.ARTICLE.value == "article"
        assert SourceTypeEnum.VIDEO.value == "video"
        assert SourceTypeEnum.PODCAST.value == "podcast"
        assert SourceTypeEnum.INTERVIEW.value == "interview"
        assert SourceTypeEnum.DOC.value == "doc"
        assert SourceTypeEnum.WEB.value == "web"
    
    def test_page_status_enum(self):
        """Tester PageStatusEnum."""
        assert PageStatusEnum.DRAFT.value == "draft"
        assert PageStatusEnum.ACTIVE.value == "active"
        assert PageStatusEnum.ARCHIVED.value == "archived"
        assert PageStatusEnum.DEPRECATED.value == "deprecated"
        assert PageStatusEnum.OBSOLETE.value == "obsolete"
    
    def test_authority_level_enum(self):
        """Tester AuthorityLevel."""
        assert AuthorityLevel.HIGH.value == "high"
        assert AuthorityLevel.MEDIUM.value == "medium"
        assert AuthorityLevel.LOW.value == "low"
        assert AuthorityLevel.SPECULATIVE.value == "speculative"
    
    def test_confidence_level_enum(self):
        """Tester ConfidenceLevel."""
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"


class TestEntityPage:
    """Tests pour EntityPage."""
    
    def test_create_entity_page(self):
        """Tester la création d'une page d'entité."""
        page = EntityPage(
            type=PageTypeEnum.ENTITY,
            entity_type=EntityTypeEnum.PERSON,
            name="Test Person",
            description="A test person",
            aliases=["Test", "T."],
            tags=["test", "person"],
            related=["organizations/test_org"],
            sources=["sources/test_source"],
            created=datetime(2024, 1, 20, 10, 30),
            updated=datetime(2024, 1, 20, 14, 45),
        )
        
        assert page.type == PageTypeEnum.ENTITY
        assert page.entity_type == EntityTypeEnum.PERSON
        assert page.name == "Test Person"
        assert page.description == "A test person"
        assert page.aliases == ["Test", "T."]
        assert page.tags == ["test", "person"]
        assert page.related == ["organizations/test_org"]
        assert page.sources == ["sources/test_source"]
    
    def test_entity_page_validation(self):
        """Tester la validation d'une page d'entité."""
        # Test avec des aliases valides
        page = EntityPage(
            type=PageTypeEnum.ENTITY,
            entity_type=EntityTypeEnum.PERSON,
            name="Test",
            description="Test",
            aliases=["A", "B"],
            tags=["test"],
            related=[],
            sources=[],
            created=datetime.now(),
            updated=datetime.now(),
        )
        assert page.aliases == ["A", "B"]
        
        # Test avec des tags valides
        page = EntityPage(
            type=PageTypeEnum.ENTITY,
            entity_type=EntityTypeEnum.PERSON,
            name="Test",
            description="Test",
            aliases=[],
            tags=["test", "valid"],
            related=[],
            sources=[],
            created=datetime.now(),
            updated=datetime.now(),
        )
        assert page.tags == ["test", "valid"]


class TestConceptPage:
    """Tests pour ConceptPage."""
    
    def test_create_concept_page(self):
        """Tester la création d'une page de concept."""
        page = ConceptPage(
            type=PageTypeEnum.CONCEPT,
            name="Test Concept",
            description="A test concept",
            categories=["ai", "ml"],
            tags=["test", "concept"],
            related=["concepts/related"],
            sources=["sources/test"],
            created=datetime(2024, 1, 20, 10, 30),
            updated=datetime(2024, 1, 20, 14, 45),
            status=PageStatusEnum.ACTIVE,
            authority=AuthorityLevel.HIGH,
        )
        
        assert page.type == PageTypeEnum.CONCEPT
        assert page.name == "Test Concept"
        assert page.categories == ["ai", "ml"]
        assert page.status == PageStatusEnum.ACTIVE
        assert page.authority == AuthorityLevel.HIGH


class TestSourcePage:
    """Tests pour SourcePage."""
    
    def test_create_source_page(self):
        """Tester la création d'une page de source."""
        page = SourcePage(
            type=PageTypeEnum.SOURCE,
            source_type=SourceTypeEnum.PAPER,
            original_path="raw/papers/test.pdf",
            title="Test Paper",
            authors=["Author 1", "Author 2"],
            date=datetime(2024, 1, 15),
            url="https://example.com/test",
            doi="10.1234/test",
            summary="A test paper summary",
            ingested=datetime(2024, 1, 20, 10, 30),
            created=datetime(2024, 1, 20, 10, 30),
            updated=datetime(2024, 1, 20, 14, 45),
            tags=["test", "paper"],
            related=["concepts/test"],
            sources=[],
        )
        
        assert page.type == PageTypeEnum.SOURCE
        assert page.source_type == SourceTypeEnum.PAPER
        assert page.original_path == "raw/papers/test.pdf"
        assert page.title == "Test Paper"
        assert page.authors == ["Author 1", "Author 2"]
        assert page.summary == "A test paper summary"


class TestComparisonPage:
    """Tests pour ComparisonPage."""
    
    def test_create_comparison_page(self):
        """Tester la création d'une page de comparaison."""
        page = ComparisonPage(
            type=PageTypeEnum.COMPARISON,
            name="A vs B",
            description="Comparison between A and B",
            subjects=["concepts/a", "concepts/b"],
            criteria=["performance", "complexity"],
            tags=["comparison", "test"],
            related=["concepts/c"],
            sources=["sources/test"],
            created=datetime(2024, 1, 20, 10, 30),
            updated=datetime(2024, 1, 20, 14, 45),
        )
        
        assert page.type == PageTypeEnum.COMPARISON
        assert page.name == "A vs B"
        assert page.subjects == ["concepts/a", "concepts/b"]
        assert page.criteria == ["performance", "complexity"]


class TestSynthesisPage:
    """Tests pour SynthesisPage."""
    
    def test_create_synthesis_page(self):
        """Tester la création d'une page de synthèse."""
        page = SynthesisPage(
            type=PageTypeEnum.SYNTHESIS,
            name="AI Overview",
            description="Overview of AI",
            domain="ai",
            scope="overview",
            tags=["synthesis", "ai"],
            related=["concepts/ml"],
            sources=["sources/test"],
            created=datetime(2024, 1, 20, 10, 30),
            updated=datetime(2024, 1, 20, 14, 45),
            status=PageStatusEnum.CURRENT,
            confidence=ConfidenceLevel.HIGH,
        )
        
        assert page.type == PageTypeEnum.SYNTHESIS
        assert page.name == "AI Overview"
        assert page.domain == "ai"
        assert page.scope == "overview"
        assert page.status == PageStatusEnum.CURRENT
        assert page.confidence == ConfidenceLevel.HIGH


class TestIndexPage:
    """Tests pour IndexPage."""
    
    def test_create_index_page(self):
        """Tester la création d'une page d'index."""
        page = IndexPage(
            type=PageTypeEnum.INDEX,
            name="Vault Index",
            description="Complete vault index",
            generated=datetime(2024, 1, 20, 10, 30),
            version="1.0.0",
            statistics={"total_pages": 10},
            pages_by_type={"entity": ["test"]},
            pages_by_tag={"test": ["test"]},
            pages_by_date={"2024-01-20": ["test"]},
        )
        
        assert page.type == PageTypeEnum.INDEX
        assert page.name == "Vault Index"
        assert page.version == "1.0.0"
        assert page.statistics["total_pages"] == 10


class TestLogPage:
    """Tests pour LogPage."""
    
    def test_create_log_page(self):
        """Tester la création d'une page de log."""
        page = LogPage(
            type=PageTypeEnum.LOG,
            name="Vault Log",
            description="Operation log",
            created=datetime(2024, 1, 20, 10, 30),
            entries=[
                {"timestamp": "2024-01-20T10:30:00", "operation": "init"},
            ],
        )
        
        assert page.type == PageTypeEnum.LOG
        assert page.name == "Vault Log"
        assert len(page.entries) == 1


class TestVaultConfig:
    """Tests pour VaultConfig."""
    
    def test_create_vault_config(self):
        """Tester la création d'une configuration de vault."""
        config = VaultConfig(
            path="/path/to/vault",
            topic="Test Topic",
            tool="all",
        )
        
        assert config.path == "/path/to/vault"
        assert config.topic == "Test Topic"
        assert config.tool == "all"


class TestResultModels:
    """Tests pour les modèles de résultats."""
    
    def test_ingest_result(self):
        """Tester IngestResult."""
        result = IngestResult(
            success=True,
            source_path="raw/test.pdf",
            summary_page="wiki/sources/test.md",
            updated_pages=["wiki/concepts/test.md"],
            cross_references=["concepts/test"],
            duration_seconds=120.5,
        )
        
        assert result.success is True
        assert result.source_path == "raw/test.pdf"
        assert result.duration_seconds == 120.5
    
    def test_query_result(self):
        """Tester QueryResult."""
        result = QueryResult(
            success=True,
            query="test query",
            answer="test answer",
            cited_pages=["concepts/test"],
            duration_seconds=5.5,
        )
        
        assert result.success is True
        assert result.query == "test query"
        assert result.answer == "test answer"
    
    def test_lint_result(self):
        """Tester LintResult."""
        result = LintResult(
            success=True,
            issues=[{"type": "info", "message": "test"}],
            warnings=[{"type": "warning", "message": "test"}],
            errors=[{"type": "error", "message": "test"}],
            duration_seconds=60.0,
        )
        
        assert result.success is True
        assert len(result.issues) == 1
        assert len(result.warnings) == 1
        assert len(result.errors) == 1
