"""
Agent Wiki Ingestor pour le système RAG Wiki.

Cet agent gère l'ingestion complète des sources dans le vault.
Il utilise OCRAgent pour l'extraction de texte, puis PreprocessingAgent pour le nettoyage.
"""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import WikiConfig
from ..core.wiki_engine import WikiEngine
from ..storage import VaultManager
from .ocr_agent import OCRAgent
from .preprocessing_agent import PreprocessingAgent
from .base_agent import BaseAgent


class WikiIngestorAgent(BaseAgent):
    """
    Agent Wiki Ingestor pour le système RAG Wiki.
    
    Cet agent est responsable de l'ingestion complète des sources :
    - OCR via OCRAgent (UNIQUEMENT Mistral OCR API)
    - Prétraitement via PreprocessingAgent (nettoyage, déduplication)
    - Extraction des métadonnées
    - Création des pages
    - Mise à jour des références
    - Logging des opérations
    """
    
    def __init__(
        self,
        vault_path: Path,
        config: Optional[WikiConfig] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """
        Initialiser l'agent Wiki Ingestor.
        
        Args:
            vault_path: Chemin du vault.
            config: Configuration du wiki.
            api_key: Clé API Mistral (optionnel).
        """
        super().__init__(
            name="WikiIngestor",
            role="Ingestion des sources et intégration dans le vault",
            vault_manager=VaultManager(vault_path),
            config=config or WikiConfig(vault_path=vault_path),
        )
        
        self.vault_path = vault_path
        self.wiki_engine = WikiEngine(config=self.config, vault_path=vault_path)
        self.ocr_agent = OCRAgent(vault_path, config, api_key)
        self.preprocessing_agent = PreprocessingAgent(vault_path, config)
    
    async def execute(
        self,
        source_path: Path,
        preprocess: bool = True,
        ask_for_confirmation: bool = True,
        describe_images: bool = True,
    ) -> Dict[str, Any]:
        """
        Exécuter l'ingestion d'une source.
        
        Workflow:
        1. OCR via OCRAgent (si fichier PDF/image)
        2. Prétraitement via PreprocessingAgent (nettoyage, déduplication)
        3. Ingestion via WikiEngine
        
        Args:
            source_path: Chemin de la source à ingérer.
            preprocess: Si True, prétraiter la source avant ingestion.
            ask_for_confirmation: Si True, demander confirmation pour les suppressions.
            describe_images: Si True, générer des descriptions pour les images.
            
        Returns:
            Rapport d'ingestion.
        """
        report: Dict[str, Any] = {
            "source_path": str(source_path),
            "ocr_processed": False,
            "ocr_report": {},
            "preprocessed": False,
            "preprocessing_report": {},
            "ingestion_report": {},
            "success": False,
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            # Étape 0: Vérifier le type de fichier
            from ..utils.path_utils import get_file_type
            file_type = get_file_type(source_path)
            
            # Étape 1: OCR (si fichier PDF ou image)
            if file_type in ["pdf", "image", "png", "jpg", "jpeg", "gif", "bmp"]:
                success, ocr_text, ocr_report = await self.ocr_agent.extract_text(
                    file_path=source_path,
                    describe_images=describe_images,
                )
                
                if not success:
                    report["ocr_report"] = ocr_report
                    report["error"] = "Échec de l'OCR"
                    report["success"] = False
                    return report
                
                report["ocr_processed"] = True
                report["ocr_report"] = ocr_report
                
                # Sauvegarder le texte OCR dans un fichier temporaire
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".txt",
                    delete=False,
                    encoding="utf-8"
                ) as tmp_file:
                    tmp_file.write(ocr_text)
                    ocr_output_path = Path(tmp_file.name)
            else:
                # Fichier texte pur (MD, TXT, HTML), pas besoin d'OCR
                ocr_output_path = source_path
            
            # Étape 2: Prétraitement (nettoyage, déduplication, structuration)
            if preprocess:
                success, preprocessed_path, preprocess_report = await self.preprocessing_agent.preprocess(
                    input_path=ocr_output_path,
                    ask_for_confirmation=ask_for_confirmation,
                )
                
                if success:
                    report["preprocessed"] = True
                    report["preprocessing_report"] = preprocess_report
                    # Utiliser le fichier prétraité
                    final_source_path = preprocessed_path
                else:
                    report["preprocessing_report"] = preprocess_report
                    # Continuer avec le fichier OCR
                    final_source_path = ocr_output_path
            else:
                final_source_path = ocr_output_path
            
            # Étape 3: Ingestion
            result = await self.wiki_engine.ingest_source(
                source_path=final_source_path,
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
            
            # Nettoyer le fichier temporaire OCR
            if file_type in ["pdf", "image", "png", "jpg", "jpeg", "gif", "bmp"]:
                try:
                    ocr_output_path.unlink()
                except Exception:
                    pass
            
            return report
            
        except Exception as e:
            report["error"] = str(e)
            report["success"] = False
            return report
    
    async def ingest_batch(
        self,
        source_paths: List[Path],
        preprocess: bool = True,
        describe_images: bool = True,
    ) -> Dict[str, Any]:
        """
        Ingestion de plusieurs sources en batch.
        
        Args:
            source_paths: Liste des chemins des sources.
            preprocess: Si True, prétraiter les sources.
            describe_images: Si True, générer des descriptions pour les images.
            
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
                report = await self.execute(
                    source_path,
                    preprocess=preprocess,
                    describe_images=describe_images,
                )
                
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
        asyncio.run(self._async_close())
    
    async def _async_close(self) -> None:
        """Fermer les ressources de manière asynchrone."""
        await self.ocr_agent.close()
        self.wiki_engine.close()
        self.preprocessing_agent.close()
        self.vault_manager.close()
