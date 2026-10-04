"""
Moteur principal du système RAG Wiki.

Ce module contient la classe WikiEngine qui orchestrer les pipelines
d'ingestion, de requête et de linting.
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..types import (
    IngestResult,
    QueryResult,
    LintResult,
    VaultConfig,
    Page,
)
from ..storage import VaultManager
from ..indexes import IndexManager
from ..retrieval import RetrievalService
from .config import WikiConfig, get_config
from .ingest_pipeline import IngestPipeline
from .query_pipeline import QueryPipeline
from .lint_pipeline import LintPipeline


class WikiEngine:
    """
    Moteur principal du système RAG Wiki.
    
    Cette classe orchestrer tous les pipelines et services pour fournir
    une interface unifiée pour l'ingestion, la requête et le linting.
    """
    
    def __init__(
        self,
        config: Optional[WikiConfig] = None,
        vault_path: Optional[Path] = None,
    ) -> None:
        """
        Initialiser le WikiEngine.
        
        Args:
            config: Configuration du wiki. Si None, utilise la configuration par défaut.
            vault_path: Chemin du vault. Si None, utilise le chemin de la configuration.
        """
        self.config = config or get_config()
        
        # Définir le chemin du vault
        if vault_path:
            self.vault_path = vault_path
        else:
            self.vault_path = self.config.vault_path
        
        # Initialiser les managers et services
        self.vault_manager = VaultManager(self.vault_path)
        self.index_manager = IndexManager(self.vault_path)
        self.retrieval_service = RetrievalService(self.vault_path, self.index_manager)
        
        # Initialiser les pipelines
        self.ingest_pipeline = IngestPipeline(
            vault_manager=self.vault_manager,
            index_manager=self.index_manager,
            config=self.config,
        )
        self.query_pipeline = QueryPipeline(
            vault_manager=self.vault_manager,
            retrieval_service=self.retrieval_service,
            config=self.config,
        )
        self.lint_pipeline = LintPipeline(
            vault_manager=self.vault_manager,
            index_manager=self.index_manager,
            config=self.config,
        )
    
    async def initialize_vault(
        self,
        topic: str = "Recherche",
        tool: str = "all",
    ) -> bool:
        """
        Initialiser un nouveau vault.
        
        Args:
            topic: Sujet principal du vault.
            tool: Outil LLM à configurer.
            
        Returns:
            True si l'initialisation a réussi, False sinon.
        """
        try:
            start_time = time.time()
            
            # Créer la structure de base
            self.vault_manager.initialize_vault(topic, tool)
            
            # Initialiser l'index
            self.index_manager.initialize_index()
            
            # Logger l'opération
            self._log_operation(
                operation_type="init",
                details={"topic": topic, "tool": tool},
                duration=time.time() - start_time,
                success=True,
            )
            
            return True
            
        except Exception as e:
            self._log_operation(
                operation_type="init",
                details={"topic": topic, "tool": tool, "error": str(e)},
                duration=time.time() - start_time,
                success=False,
            )
            return False
    
    async def ingest_source(
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
            result = await self.ingest_pipeline.ingest(
                source_path=source_path,
                discuss_with_user=discuss_with_user,
            )
            
            # Logger l'opération
            self._log_operation(
                operation_type="ingest",
                details={
                    "source_path": str(source_path),
                    "summary_page": result.summary_page,
                    "updated_pages": result.updated_pages,
                    "cross_references": result.cross_references,
                },
                duration=result.duration_seconds,
                success=result.success,
            )
            
            return result
            
        except Exception as e:
            self._log_operation(
                operation_type="ingest",
                details={
                    "source_path": str(source_path),
                    "error": str(e),
                },
                duration=time.time() - start_time,
                success=False,
            )
            return IngestResult(
                success=False,
                source_path=str(source_path),
                summary_page="",
                duration_seconds=time.time() - start_time,
                error=str(e),
            )
    
    async def query(
        self,
        query_text: str,
        use_index: bool = True,
        use_bm25: bool = True,
        use_embeddings: bool = True,
    ) -> QueryResult:
        """
        Effectuer une requête sur le vault.
        
        Args:
            query_text: Texte de la requête.
            use_index: Utiliser la recherche dans l'index.
            use_bm25: Utiliser la recherche BM25.
            use_embeddings: Utiliser la recherche par embeddings.
            
        Returns:
            Résultat de la requête.
        """
        start_time = time.time()
        
        try:
            result = await self.query_pipeline.query(
                query_text=query_text,
                use_index=use_index,
                use_bm25=use_bm25,
                use_embeddings=use_embeddings,
            )
            
            # Logger l'opération
            self._log_operation(
                operation_type="query",
                details={
                    "query": query_text,
                    "cited_pages": result.cited_pages,
                },
                duration=result.duration_seconds,
                success=result.success,
            )
            
            return result
            
        except Exception as e:
            self._log_operation(
                operation_type="query",
                details={
                    "query": query_text,
                    "error": str(e),
                },
                duration=time.time() - start_time,
                success=False,
            )
            return QueryResult(
                success=False,
                query=query_text,
                answer="",
                duration_seconds=time.time() - start_time,
                error=str(e),
            )
    
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
        
        try:
            result = await self.lint_pipeline.lint(
                check_mechanical=check_mechanical,
                check_semantic=check_semantic,
                check_health=check_health,
            )
            
            # Logger l'opération
            self._log_operation(
                operation_type="lint",
                details={
                    "issues_count": len(result.issues),
                    "warnings_count": len(result.warnings),
                    "errors_count": len(result.errors),
                },
                duration=result.duration_seconds,
                success=result.success,
            )
            
            return result
            
        except Exception as e:
            self._log_operation(
                operation_type="lint",
                details={"error": str(e)},
                duration=time.time() - start_time,
                success=False,
            )
            return LintResult(
                success=False,
                duration_seconds=time.time() - start_time,
                error=str(e),
            )
    
    async def update_index(self) -> bool:
        """
        Mettre à jour l'index manuellement.
        
        Returns:
            True si la mise à jour a réussi, False sinon.
        """
        start_time = time.time()
        
        try:
            self.index_manager.update_index()
            
            self._log_operation(
                operation_type="update_index",
                details={},
                duration=time.time() - start_time,
                success=True,
            )
            
            return True
            
        except Exception as e:
            self._log_operation(
                operation_type="update_index",
                details={"error": str(e)},
                duration=time.time() - start_time,
                success=False,
            )
            return False
    
    def _log_operation(
        self,
        operation_type: str,
        details: Dict[str, Any],
        duration: float,
        success: bool,
    ) -> None:
        """
        Logger une opération.
        
        Args:
            operation_type: Type de l'opération.
            details: Détails de l'opération.
            duration: Durée de l'opération en secondes.
            success: Si l'opération a réussi.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation_type,
            "details": details,
            "duration_seconds": round(duration, 2),
            "success": success,
        }
        
        self.vault_manager.append_log_entry(entry)
    
    def get_vault_stats(self) -> Dict[str, Any]:
        """
        Obtenir les statistiques du vault.
        
        Returns:
            Dictionnaire avec les statistiques.
        """
        return self.vault_manager.get_vault_stats()
    
    def get_page(self, page_path: Path) -> Optional[Page]:
        """
        Obtenir une page spécifique.
        
        Args:
            page_path: Chemin de la page.
            
        Returns:
            La page ou None si non trouvée.
        """
        return self.vault_manager.get_page(page_path)
    
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
        return self.vault_manager.search(
            query=query,
            page_types=page_types,
            tags=tags,
            limit=limit,
        )
    
    async def close(self) -> None:
        """Fermer les ressources du WikiEngine."""
        await self.ingest_pipeline.close()
        await self.query_pipeline.close()
        await self.lint_pipeline.close()
        self.vault_manager.close()
        self.index_manager.close()
        self.retrieval_service.close()
