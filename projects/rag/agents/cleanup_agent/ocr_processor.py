"""
Processeur OCR utilisant Mistral OCR API.

Ce module gère l'extraction de texte à partir d'images et PDF
via l'API Mistral OCR.
"""

import asyncio
import base64
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx

logger = logging.getLogger(__name__)


class OCRProcessor:
    """
    Processeur pour l'OCR via Mistral API.
    
    Fonctionnalités:
    - Extraction de texte à partir d'images (PNG, JPG, JPEG, GIF, BMP, WEBP)
    - Extraction de texte à partir de PDF
    - Détection automatique de la langue
    - Amélioration de la qualité
    - Rotation automatique
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base_url: str = "https://api.mistral.ai/v1",
        timeout: float = 120.0,
        max_retries: int = 3,
    ) -> None:
        """
        Initialiser le processeur OCR.
        
        Args:
            api_key: Clé API Mistral. Si None, utilise MISTRAL_API_KEY.
            api_base_url: URL de base de l'API.
            timeout: Timeout en secondes.
            max_retries: Nombre de tentatives maximales.
        """
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Clé API Mistral requise. "
                "Définissez MISTRAL_API_KEY ou passez api_key."
            )
        
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Configuration OCR
        self.supported_formats = [
            ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"
        ]
        self.max_file_size_mb = 100
        self.api_endpoint = "/ocr"
        
        # Client HTTP
        self.client = httpx.AsyncClient(
            base_url=self.api_base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
    
    async def _make_request(
        self,
        payload: Dict[str, Any],
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """Effectuer une requête à l'API OCR avec gestion des erreurs."""
        try:
            response = await self.client.post(
                self.api_endpoint,
                json=payload,
            )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and retry_count < self.max_retries:
                # Rate limiting - attendre et réessayer
                await asyncio.sleep(1)
                return await self._make_request(payload, retry_count + 1)
            
            logger.error(f"Erreur API OCR: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la requête OCR: {e}")
            raise
    
    def _encode_file_to_base64(self, file_path: Path) -> str:
        """Encoder un fichier en base64."""
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Obtenir les informations du fichier."""
        stat = file_path.stat()
        return {
            "filename": file_path.name,
            "size_bytes": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "mime_type": self._get_mime_type(file_path),
        }
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Obtenir le type MIME du fichier."""
        extension = file_path.suffix.lower()
        mime_types = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp",
        }
        return mime_types.get(extension, "application/octet-stream")
    
    async def process_file(
        self,
        file_path: Union[Path, str],
        enhance_quality: bool = True,
        auto_rotate: bool = True,
        detect_language: bool = True,
    ) -> Dict[str, Any]:
        """
        Traiter un fichier avec OCR.
        
        Args:
            file_path: Chemin du fichier à traiter.
            enhance_quality: Améliorer la qualité de l'image.
            auto_rotate: Rotation automatique.
            detect_language: Détecter la langue.
            
        Returns:
            Résultat de l'OCR avec texte extrait et métadonnées.
        """
        file_path = Path(file_path)
        
        # Vérifier que le fichier existe
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {file_path}")
        
        # Vérifier l'extension
        if file_path.suffix.lower() not in self.supported_formats:
            raise ValueError(
                f"Format non supporté: {file_path.suffix}. "
                f"Formats supportés: {', '.join(self.supported_formats)}"
            )
        
        # Vérifier la taille
        file_info = self._get_file_info(file_path)
        if file_info["size_mb"] > self.max_file_size_mb:
            raise ValueError(
                f"Fichier trop grand: {file_info['size_mb']:.1f}MB. "
                f"Maximum: {self.max_file_size_mb}MB"
            )
        
        logger.info(f"Traitement OCR: {file_path.name} ({file_info['size_mb']:.1f}MB)")
        
        # Préparer le payload
        payload = {
            "model": "mistral-ocr-latest",
            "image": self._encode_file_to_base64(file_path),
            "enhance_quality": enhance_quality,
            "auto_rotate": auto_rotate,
            "detect_language": detect_language,
        }
        
        # Effectuer la requête
        try:
            result = await self._make_request(payload)
            
            # Formater le résultat
            formatted_result = {
                "success": True,
                "file": file_info["filename"],
                "size_mb": file_info["size_mb"],
                "text": result.get("text", ""),
                "language": result.get("language", "unknown"),
                "pages": result.get("pages", 1),
                "model": result.get("model", "mistral-ocr-latest"),
                "processing_time": result.get("processing_time", 0),
                "metadata": result.get("metadata", {}),
            }
            
            logger.info(f"OCR terminé: {len(formatted_result['text'])} caractères extraits")
            return formatted_result
            
        except Exception as e:
            logger.error(f"Échec de l'OCR pour {file_path.name}: {e}")
            return {
                "success": False,
                "file": file_info["filename"],
                "error": str(e),
            }
    
    async def process_multiple_files(
        self,
        file_paths: List[Union[Path, str]],
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Traiter plusieurs fichiers avec OCR.
        
        Args:
            file_paths: Liste des chemins de fichiers.
            **kwargs: Arguments à passer à process_file.
            
        Returns:
            Liste des résultats.
        """
        tasks = [
            self.process_file(file_path, **kwargs)
            for file_path in file_paths
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def close(self) -> None:
        """Fermer le client HTTP."""
        await self.client.aclose()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.run(self.close())
