"""
Cleanup Agent - Agent de nettoyage pour le système RAG Wiki.

Cet agent combine:
- Mistral OCR pour extraire le texte des images/PDF
- Nettoyage intelligent du texte
- Structuration et préparation pour l'ingestion RAG
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .ocr_processor import OCRProcessor
from .cleanup_processor import CleanupProcessor

logger = logging.getLogger(__name__)


class CleanupAgent:
    """
    Agent de nettoyage pour le système RAG Wiki.
    
    Cet agent est responsable de:
    1. L'extraction de texte via OCR (PDF, images)
    2. Le nettoyage du texte (en-têtes, pieds de page, etc.)
    3. La structuration du texte pour l'ingestion RAG
    4. La préparation des fichiers pour les autres agents
    
    Commande OpenWebUI: `/clean` ou `/cleanup`
    """
    
    def __init__(
        self,
        vault_path: Union[Path, str],
        api_key: Optional[str] = None,
        config_path: Optional[str] = None,
    ) -> None:
        """
        Initialiser l'agent de nettoyage.
        
        Args:
            vault_path: Chemin du vault.
            api_key: Clé API Mistral.
            config_path: Chemin du fichier de configuration.
        """
        self.vault_path = Path(vault_path) if isinstance(vault_path, str) else vault_path
        self.vault_path.mkdir(parents=True, exist_ok=True)
        
        # Charger la configuration
        self.config = self._load_config(config_path)
        
        # Initialiser les processeurs
        self.ocr_processor = OCRProcessor(
            api_key=api_key,
            api_base_url=self.config.get("api_base_url", "https://api.mistral.ai/v1"),
            timeout=self.config.get("timeout", 120),
            max_retries=self.config.get("max_retries", 3),
        )
        
        self.cleanup_processor = CleanupProcessor(
            remove_headers=self.config.get("remove_headers", True),
            remove_footers=self.config.get("remove_footers", True),
            remove_page_numbers=self.config.get("remove_page_numbers", True),
            remove_boilerplate=self.config.get("remove_boilerplate", True),
            normalize_text=self.config.get("normalize_text", True),
            detect_language=self.config.get("detect_language", True),
            min_text_length=self.config.get("min_text_length", 50),
        )
        
        # Chemins
        self.raw_dir = self.vault_path / "raw"
        self.cleaned_dir = self.vault_path / "cleaned"
        self.raw_dir.mkdir(exist_ok=True)
        self.cleaned_dir.mkdir(exist_ok=True)
        
        # Historique
        self.history: List[Dict[str, Any]] = []
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Charger la configuration."""
        # Configuration par défaut
        default_config = {
            "api_base_url": "https://api.mistral.ai/v1",
            "timeout": 120,
            "max_retries": 3,
            "remove_headers": True,
            "remove_footers": True,
            "remove_page_numbers": True,
            "remove_boilerplate": True,
            "normalize_text": True,
            "detect_language": True,
            "min_text_length": 50,
            "enhance_quality": True,
            "auto_rotate": True,
        }
        
        # Charger depuis le fichier si spécifié
        if config_path:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                default_config.update(file_config.get("cleanup_agent", {}))
        
        # Charger depuis le vault
        vault_config = self.vault_path / "configs" / "agents_config.json"
        if vault_config.exists():
            with open(vault_config, "r", encoding="utf-8") as f:
                file_config = json.load(f)
            default_config.update(file_config.get("agents", {}).get("cleanup_agent", {}).get("features", {}).get("cleanup", {}))
        
        return default_config
    
    def _get_file_type(self, file_path: Path) -> str:
        """Déterminer le type de fichier."""
        extension = file_path.suffix.lower()
        
        if extension in [".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]:
            return "image"
        elif extension in [".txt", ".md", ".markdown"]:
            return "text"
        else:
            return "unknown"
    
    def _should_use_ocr(self, file_path: Path) -> bool:
        """Déterminer si OCR est nécessaire."""
        file_type = self._get_file_type(file_path)
        return file_type == "image"
    
    async def _process_with_ocr(
        self,
        file_path: Path,
        enhance_quality: bool = True,
        auto_rotate: bool = True,
        detect_language: bool = True,
    ) -> Dict[str, Any]:
        """Traiter un fichier avec OCR."""
        logger.info(f"Traitement OCR: {file_path.name}")
        
        try:
            result = await self.ocr_processor.process_file(
                file_path,
                enhance_quality=enhance_quality,
                auto_rotate=auto_rotate,
                detect_language=detect_language,
            )
            
            if result.get("success", False):
                # Sauvegarder le texte extrait
                output_path = self.cleaned_dir / f"{file_path.stem}.txt"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result["text"])
                
                result["output_path"] = str(output_path)
                result["status"] = "ocr_completed"
            
            return result
            
        except Exception as e:
            logger.error(f"Échec OCR pour {file_path.name}: {e}")
            return {
                "success": False,
                "file": file_path.name,
                "error": str(e),
                "status": "ocr_failed",
            }
    
    async def _process_text_file(
        self,
        file_path: Path,
    ) -> Dict[str, Any]:
        """Traiter un fichier texte."""
        logger.info(f"Nettoyage texte: {file_path.name}")
        
        try:
            result = self.cleanup_processor.clean_file(file_path)
            
            if result.get("success", False):
                # Sauvegarder le texte nettoyé
                output_path = self.cleaned_dir / f"cleaned_{file_path.name}"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result["text"])
                
                result["output_path"] = str(output_path)
                result["status"] = "cleanup_completed"
            
            return result
            
        except Exception as e:
            logger.error(f"Échec nettoyage pour {file_path.name}: {e}")
            return {
                "success": False,
                "file": file_path.name,
                "error": str(e),
                "status": "cleanup_failed",
            }
    
    async def _process_file(
        self,
        file_path: Path,
        mode: str = "auto",
        enhance_quality: bool = True,
        auto_rotate: bool = True,
        detect_language: bool = True,
    ) -> Dict[str, Any]:
        """Traiter un fichier selon son type."""
        file_path = Path(file_path)
        
        # Vérifier que le fichier existe
        if not file_path.exists():
            return {
                "success": False,
                "file": str(file_path),
                "error": "Fichier non trouvé",
                "status": "not_found",
            }
        
        # Déterminer le mode
        if mode == "auto":
            mode = "both" if self._should_use_ocr(file_path) else "cleanup_only"
        
        # Traiter selon le mode
        if mode in ["ocr_only", "both"] and self._should_use_ocr(file_path):
            ocr_result = await self._process_with_ocr(
                file_path,
                enhance_quality=enhance_quality,
                auto_rotate=auto_rotate,
                detect_language=detect_language,
            )
            
            if mode == "both" and ocr_result.get("success", False):
                # Nettoyer le texte extrait
                text_result = self.cleanup_processor.clean_text(
                    ocr_result["text"],
                    file_path,
                )
                
                # Fusionner les résultats
                ocr_result.update({
                    "cleanup": text_result,
                    "final_text": text_result.get("text", ""),
                })
                
                # Sauvegarder le résultat final
                output_path = self.cleaned_dir / f"final_{file_path.stem}.txt"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(text_result.get("text", ""))
                
                ocr_result["final_output_path"] = str(output_path)
        
        elif mode in ["cleanup_only", "both"]:
            ocr_result = await self._process_text_file(file_path)
        
        else:
            ocr_result = {
                "success": False,
                "file": file_path.name,
                "error": f"Mode non supporté: {mode}",
                "status": "invalid_mode",
            }
        
        return ocr_result
    
    async def process(
        self,
        input_path: Union[Path, str],
        output_dir: Optional[Union[Path, str]] = None,
        mode: str = "auto",
        language: str = "auto",
        enhance_quality: bool = True,
        auto_rotate: bool = True,
        detect_language: bool = True,
    ) -> Dict[str, Any]:
        """
        Traiter une entrée (fichier ou dossier).
        
        Args:
            input_path: Chemin du fichier ou dossier à traiter.
            output_dir: Dossier de sortie (par défaut: cleaned/).
            mode: Mode de traitement (auto, ocr_only, cleanup_only, both).
            language: Langue (auto, fr, en, etc.).
            enhance_quality: Améliorer la qualité de l'image.
            auto_rotate: Rotation automatique.
            detect_language: Détecter la langue.
            
        Returns:
            Résultat du traitement.
        """
        start_time = datetime.now()
        input_path = Path(input_path)
        
        # Définir le dossier de sortie
        if output_dir:
            self.cleaned_dir = Path(output_dir) if isinstance(output_dir, str) else output_dir
            self.cleaned_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialiser le rapport
        report: Dict[str, Any] = {
            "success": True,
            "start_time": start_time.isoformat(),
            "input": str(input_path),
            "output_dir": str(self.cleaned_dir),
            "mode": mode,
            "files_processed": 0,
            "files_successful": 0,
            "files_failed": 0,
            "results": [],
        }
        
        try:
            # Traiter selon le type de l'entrée
            if input_path.is_file():
                # Traiter un seul fichier
                result = await self._process_file(
                    input_path,
                    mode=mode,
                    enhance_quality=enhance_quality,
                    auto_rotate=auto_rotate,
                    detect_language=detect_language,
                )
                
                report["results"].append(result)
                report["files_processed"] = 1
                
                if result.get("success", False):
                    report["files_successful"] = 1
                else:
                    report["files_failed"] = 1
                    report["success"] = False
                
            elif input_path.is_dir():
                # Traiter tous les fichiers dans le dossier
                files = [f for f in input_path.glob("**/*") if f.is_file()]
                
                tasks = [
                    self._process_file(
                        f,
                        mode=mode,
                        enhance_quality=enhance_quality,
                        auto_rotate=auto_rotate,
                        detect_language=detect_language,
                    )
                    for f in files
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        report["results"].append({
                            "success": False,
                            "error": str(result),
                            "status": "exception",
                        })
                        report["files_failed"] += 1
                    else:
                        report["results"].append(result)
                        report["files_processed"] += 1
                        if result.get("success", False):
                            report["files_successful"] += 1
                        else:
                            report["files_failed"] += 1
                
                report["success"] = report["files_failed"] == 0
            else:
                return {
                    "success": False,
                    "error": "Chemin invalide: doit être un fichier ou un dossier",
                }
            
            # Calculer la durée
            report["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            report["end_time"] = datetime.now().isoformat()
            
            # Ajouter à l'historique
            self.history.append(report)
            
            logger.info(
                f"Traitement terminé: {report['files_processed']} fichiers, "
                f"{report['files_successful']} réussis, "
                f"{report['files_failed']} échoués"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement: {e}")
            return {
                "success": False,
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
            }
    
    async def cleanup(
        self,
        input_path: Union[Path, str],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Méthode alias pour process (compatibilité OpenWebUI).
        """
        return await self.process(input_path, **kwargs)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Obtenir l'historique des traitements."""
        return self.history
    
    def clear_history(self) -> None:
        """Effacer l'historique."""
        self.history = []
    
    async def close(self) -> None:
        """Fermer les ressources."""
        await self.ocr_processor.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.run(self.close())


# Instance globale pour OpenWebUI
_cleanup_agent: Optional[CleanupAgent] = None


def get_cleanup_agent(
    vault_path: Union[Path, str] = Path("~/vaults/knowledge_base").expanduser(),
    api_key: Optional[str] = None,
) -> CleanupAgent:
    """Obtenir une instance globale de l'agent de nettoyage."""
    global _cleanup_agent
    
    if _cleanup_agent is None:
        _cleanup_agent = CleanupAgent(vault_path, api_key)
    
    return _cleanup_agent


def reset_cleanup_agent() -> None:
    """Réinitialiser l'instance globale."""
    global _cleanup_agent
    _cleanup_agent = None
