"""
Agent Wiki Ingestor pour le système RAG Wiki.

Cet agent gère l'ingestion complète des sources dans le vault.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import WikiConfig
from ..core.wiki_engine import WikiEngine
from ..storage import VaultManager
from .preprocessing_agent import PreprocessingAgent
from .base_agent import BaseAgent


class WikiIngestorAgent(BaseAgent):
    """
    Agent Wiki Ingestor pour le système RAG Wiki.
    
    Cet agent est responsable de l'ingestion complète des sources :
    - Préprocessing des sources
    - Extraction des métadonnées
    - Création des pages
    - Mise à jour des références
    - Logging des opérations
    """
    
    def __init__(
        self,
        vault_path: Path,
        config: Optional[WikiConfig] = None,
    ) -> None:
        """
        Initialiser l'agent Wiki Ingestor.
        
        Args:
            vault_path: Chemin du vault.
            config: Configuration du wiki.
        """
        super().__init__(
            name="WikiIngestor",
            role="Ingestion des sources et intégration dans le vault",
            vault_manager=VaultManager(vault_path),
            config=config or WikiConfig(vault_path=vault_path),
        )
        
        self.wiki_engine = WikiEngine(config=self.config, vault_path=vault_path)
        self.preprocessing_agent = PreprocessingAgent(vault_path, config)
    
    async def execute(
        self,
        source_path: Path,
        preprocess: bool = True,
        ask_for_confirmation: bool = True,
    ) -> Dict[str, Any]:
        """
        Exécuter l'ingestion d'une source.
        
        Args:
            source_path: Chemin de la source à ingérer.
            preprocess: Si True, préprocesser la source avant ingestion.
            ask_for_confirmation: Si True, demander confirmation pour les suppressions.
            
        Returns:
            Rapport d'ingestion.
        """
        report: Dict[str, Any] = {
            "source_path": str(source_path),
            "preprocessed": False,
            "preprocessing_report": {},
            "ingestion_report": {},
            "success": False,
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            # Étape 1: Préprocessing (optionnel)
            if preprocess:
                success, preprocessed_path, preprocess_report = await self.preprocessing_agent.preprocess(
                    input_path=source_path,
                    ask_for_confirmation=ask_for_confirmation,
                )
                
                if success:
                    report["preprocessed"] = True
                    report["preprocessing_report"] = preprocess_report
                    # Utiliser le fichier préprocessé
                    source_path = preprocessed_path
                else:
                    report["preprocessing_report"] = preprocess_report
                    # Continuer avec le fichier original
            
            # Étape 2: Ingestion
            result = await self.wiki_engine.ingest_source(
                source_path=source_path,
                discuss_with_user=False,
            )
            
            report["ingestion_report"] = {
                "success": result.success,
                "summary_page": result.summary_page,
                "updated_pages": result.updated_pages,
                "cross_references": result.cross_references,
                "duration_seconds": result.duration_seconds,
                "error": result.error,
            }
            
            report["success"] = result.success
            
            return report
            
        except Exception as e:
            report["error"] = str(e)
            report["success"] = False
            return report
    
    async def ingest_batch(
        self,
        source_paths: List[Path],
        preprocess: bool = True,
    ) -> Dict[str, Any]:
        """
        Ingestion de plusieurs sources en batch.
        
        Args:
            source_paths: Liste des chemins des sources.
            preprocess: Si True, préprocesser les sources.
            
        Returns:
            Rapport global.
        """
        global_report: Dict[str, Any] = {
            "total_sources": len(source_paths),
            "successful": 0,
            "failed": 0,
            "sources": {},
            "timestamp": datetime.now().isoformat(),
        }
        
        for source_path in source_paths:
            try:
                report = await self.execute(source_path, preprocess=preprocess)
                
                if report["success"]:
                    global_report["successful"] += 1
                else:
                    global_report["failed"] += 1
                
                global_report["sources"][str(source_path)] = report
                
            except Exception as e:
                global_report["failed"] += 1
                global_report["sources"][str(source_path)] = {
                    "error": str(e),
                    "success": False,
                }
        
        return global_report
    
    def close(self) -> None:
        """Fermer les ressources."""
        self.wiki_engine.close()
        self.preprocessing_agent.close()
        self.vault_manager.close()
