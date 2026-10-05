"""
Agent OCR dédié pour le système RAG Wiki.

Utilise UNIQUEMENT Mistral OCR API (mistral-ocr-latest).
Gère l'extraction de texte et la description contextuelle des images.
"""

import base64
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx

from ..core.config import WikiConfig, get_config
from ..storage import VaultManager
from ..utils.path_utils import get_file_type


logger = logging.getLogger(__name__)


class OCRAgent:
    """
    Agent dédié à l'OCR via Mistral API.
    
    Fonctionnalités :
    - Extraction de texte depuis PDF/images via Mistral OCR API
    - Description contextuelle des images (contexte document)
    - Gestion des erreurs et retry
    - Optimisation pour les documents techniques (SEO, IA, etc.)
    """
    
    def __init__(
        self,
        vault_path: Union[Path, str],
        config: Optional[WikiConfig] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """
        Initialiser l'agent OCR.
        
        Args:
            vault_path: Chemin du vault.
            config: Configuration du wiki.
            api_key: Clé API Mistral (sinon prise depuis MISTRAL_API_KEY).
        """
        self.vault_path = Path(vault_path) if isinstance(vault_path, str) else vault_path
        self.config = config or get_config()
        self.vault_manager = VaultManager(vault_path)
        
        # Charger la configuration Mistral
        self.mistral_config = self._load_mistral_config()
        
        # Récupérer la clé API
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Clé API Mistral manquante. "
                "Définissez la variable d'environnement MISTRAL_API_KEY ou "
                "passez api_key au constructeur."
            )
        
        # Configuration API
        self.api_base_url = self.mistral_config.get("global", {}).get(
            "api_base_url", "https://api.mistral.ai/v1"
        )
        self.timeout = self.mistral_config.get("global", {}).get("timeout_seconds", 120)
        self.max_retries = self.mistral_config.get("global", {}).get("max_retries", 3)
        self.rate_limit_delay = self.mistral_config.get("global", {}).get("rate_limit_delay", 1.0)
        
        # Configuration OCR
        self.ocr_model = self.mistral_config.get("ocr", {}).get("primary", {}).get(
            "model", "mistral-ocr-latest"
        )
        
        # Client HTTP
        self.client = httpx.AsyncClient(
            base_url=self.api_base_url,
            timeout=self.timeout,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        logger.info(f"OCRAgent initialisé avec modèle: {self.ocr_model}")
    
    def _load_mistral_config(self) -> Dict[str, Any]:
        """Charger la configuration Mistral."""
        config_path = self.vault_path / "configs" / "mistral_config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return {
                "global": {
                    "api_base_url": "https://api.mistral.ai/v1",
                    "timeout_seconds": 120,
                    "max_retries": 3,
                    "rate_limit_delay": 1.0,
                },
                "ocr": {
                    "primary": {
                        "model": "mistral-ocr-latest",
                        "enabled": True,
                    }
                }
            }
    
    async def extract_text(
        self,
        file_path: Path,
        context: Optional[str] = None,
        describe_images: bool = True,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Extraire le texte d'un fichier via Mistral OCR API.
        
        Args:
            file_path: Chemin du fichier à traiter.
            context: Contexte du document (pour description images).
            describe_images: Si True, générer une description contextuelle des images.
            
        Returns:
            Tuple avec (succès, texte extrait, rapport).
        """
        start_time = datetime.now()
        report: Dict[str, Any] = {
            "file_path": str(file_path),
            "file_type": get_file_type(file_path),
            "operations": [],
            "warnings": [],
            "errors": [],
            "stats": {
                "pages_processed": 0,
                "images_detected": 0,
                "images_described": 0,
                "text_length": 0,
            },
            "duration_seconds": 0,
        }
        
        try:
            # Vérifier que le fichier existe
            if not file_path.exists():
                report["errors"].append(f"Fichier non trouvé: {file_path}")
                return False, "", report
            
            file_type = report["file_type"]
            
            # Lire le fichier
            file_content = self._read_file(file_path)
            
            # Extraire selon le type
            if file_type == "pdf":
                text, ocr_report = await self._extract_pdf(file_path, file_content, context, describe_images)
            elif file_type in ["image", "png", "jpg", "jpeg", "gif", "bmp"]:
                text, ocr_report = await self._extract_image(file_path, file_content, context)
            else:
                report["errors"].append(f"Type de fichier non supporté: {file_type}")
                return False, "", report
            
            # Mettre à jour le rapport
            report["operations"].extend(ocr_report.get("operations", []))
            report["warnings"].extend(ocr_report.get("warnings", []))
            report["stats"].update(ocr_report.get("stats", {}))
            report["stats"]["text_length"] = len(text)
            report["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            
            return True, text, report
            
        except Exception as e:
            report["errors"].append(f"Erreur OCR: {str(e)}")
            report["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            logger.error(f"Erreur OCR pour {file_path}: {str(e)}", exc_info=True)
            return False, "", report
    
    def _read_file(self, file_path: Path) -> bytes:
        """Lire un fichier en bytes."""
        with open(file_path, "rb") as f:
            return f.read()
    
    async def _extract_pdf(
        self,
        file_path: Path,
        file_content: bytes,
        context: Optional[str],
        describe_images: bool,
    ) -> Tuple[str, Dict[str, Any]]:
        """Extraire le texte d'un PDF via Mistral OCR API."""
        report: Dict[str, Any] = {"operations": [], "warnings": [], "stats": {}}
        
        try:
            # Préparer la requête pour Mistral OCR
            # Note: Mistral OCR API attend le fichier en base64
            encoded_content = base64.b64encode(file_content).decode("utf-8")
            
            payload = {
                "model": self.ocr_model,
                "document": encoded_content,
                "document_type": "pdf",
            }
            
            # Ajouter le contexte si fourni
            if context:
                payload["context"] = context
            
            # Appeler l'API Mistral OCR
            response = await self._call_mistral_ocr_api(payload)
            
            if not response.get("success", False):
                report["errors"].append(response.get("error", "Erreur API Mistral OCR"))
                return "", report
            
            # Extraire le texte
            text = response.get("text", "")
            pages = response.get("pages", [])
            
            report["operations"].append("pdf_ocr_extraction")
            report["stats"]["pages_processed"] = len(pages)
            
            # Si describe_images est activé, traiter les images
            if describe_images:
                images = response.get("images", [])
                if images:
                    report["stats"]["images_detected"] = len(images)
                    described_images = []
                    for img in images:
                        img_base64 = img.get("content", "")
                        img_description = await self._describe_image(
                            img_base64, context, file_path.stem
                        )
                        if img_description:
                            described_images.append(img_description)
                            report["stats"]["images_described"] += 1
                    
                    if described_images:
                        text += "\n\n---\n\n**Descriptions des images**\n\n" + "\n\n".join(described_images)
                        report["operations"].append("image_description")
            
            return text, report
            
        except Exception as e:
            report["errors"].append(f"Erreur extraction PDF: {str(e)}")
            logger.error(f"Erreur extraction PDF: {str(e)}", exc_info=True)
            return "", report
    
    async def _extract_image(
        self,
        file_path: Path,
        file_content: bytes,
        context: Optional[str],
    ) -> Tuple[str, Dict[str, Any]]:
        """Extraire le texte d'une image via Mistral OCR API."""
        report: Dict[str, Any] = {"operations": [], "warnings": [], "stats": {"images_processed": 1}}
        
        try:
            # Encoder l'image en base64
            encoded_content = base64.b64encode(file_content).decode("utf-8")
            
            payload = {
                "model": self.ocr_model,
                "document": encoded_content,
                "document_type": "image",
            }
            
            if context:
                payload["context"] = context
            
            # Appeler l'API
            response = await self._call_mistral_ocr_api(payload)
            
            if not response.get("success", False):
                report["errors"].append(response.get("error", "Erreur API Mistral OCR"))
                return "", report
            
            # Extraire le texte
            text = response.get("text", "")
            report["operations"].append("image_ocr_extraction")
            
            # Générer une description contextuelle
            if text.strip():
                description = await self._describe_image(
                    encoded_content, context, file_path.stem
                )
                if description:
                    text += f"\n\n**Description contextuelle**: {description}"
                    report["operations"].append("image_contextual_description")
            
            return text, report
            
        except Exception as e:
            report["errors"].append(f"Erreur extraction image: {str(e)}")
            logger.error(f"Erreur extraction image: {str(e)}", exc_info=True)
            return "", report
    
    async def _describe_image(
        self,
        image_base64: str,
        context: Optional[str],
        document_name: str,
    ) -> str:
        """
        Générer une description contextuelle d'une image.
        
        Utilise Mistral LLM pour décrire l'image dans le contexte du document.
        """
        try:
            # Utiliser le modèle LLM pour la description
            llm_model = self.mistral_config.get("llm", {}).get("preprocessing", {}).get(
                "model", "mistral-small-latest"
            )
            
            # Préparer le prompt
            prompt = f"""
Tu es un assistant expert en analyse de documents techniques (IA, SEO, développement web).
Décris cette image dans le contexte du document '{document_name}' en 2-3 phrases.

Contexte supplémentaire: {context or 'Aucun contexte fourni'}

Exemple de format attendu:
- Type: [diagramme/schéma/capture d'écran/tableau/autre]
- Contenu: [description concise]
- Pertinence: [pourquoi cette image est importante dans le document]

Description:
"""
            
            payload = {
                "model": llm_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": f"data:image/png;base64,{image_base64}"}
                        ]
                    }
                ],
                "max_tokens": 512,
                "temperature": 0.3,
            }
            
            # Appeler l'API LLM
            async with httpx.AsyncClient(timeout=self.timeout) as llm_client:
                llm_response = await llm_client.post(
                    f"{self.api_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                )
            
            if llm_response.status_code != 200:
                logger.warning(f"Erreur description image: {llm_response.status_code} - {llm_response.text}")
                return ""
            
            result = llm_response.json()
            description = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Nettoyer la description
            description = description.strip()
            if not description:
                return ""
            
            return description
            
        except Exception as e:
            logger.error(f"Erreur description image: {str(e)}", exc_info=True)
            return ""
    
    async def _call_mistral_ocr_api(
        self,
        payload: Dict[str, Any],
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """Appeler l'API Mistral OCR avec gestion des erreurs."""
        try:
            # Attendre en cas de rate limit
            if retry_count > 0:
                await asyncio.sleep(self.rate_limit_delay * retry_count)
            
            response = await self.client.post(
                "/ocr",  # Endpoint OCR (à confirmer selon l'API Mistral)
                json=payload,
            )
            
            if response.status_code == 200:
                return {"success": True, **response.json()}
            elif response.status_code == 429:  # Rate limit
                if retry_count < self.max_retries:
                    return await self._call_mistral_ocr_api(payload, retry_count + 1)
                else:
                    return {"success": False, "error": "Rate limit dépassé"}
            else:
                return {"success": False, "error": f"Erreur API: {response.status_code} - {response.text}"}
            
        except httpx.TimeoutException:
            if retry_count < self.max_retries:
                return await self._call_mistral_ocr_api(payload, retry_count + 1)
            else:
                return {"success": False, "error": "Timeout"}
        except Exception as e:
            logger.error(f"Erreur appel API OCR: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def extract_batch(
        self,
        file_paths: List[Path],
        context: Optional[str] = None,
        describe_images: bool = True,
    ) -> Dict[str, Any]:
        """Extraire le texte de plusieurs fichiers en batch."""
        results = {}
        
        for file_path in file_paths:
            success, text, report = await self.extract_text(
                file_path, context, describe_images
            )
            results[str(file_path)] = {
                "success": success,
                "text": text,
                "report": report,
            }
        
        return {
            "total_files": len(file_paths),
            "successful": sum(1 for r in results.values() if r["success"]),
            "failed": sum(1 for r in results.values() if not r["success"]),
            "results": results,
        }
    
    async def close(self) -> None:
        """Fermer le client HTTP."""
        await self.client.aclose()
        self.vault_manager.close()


# Import asyncio for standalone usage
import asyncio


async def main():
    """Point d'entrée pour test CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OCRAgent - Extraction de texte via Mistral OCR")
    parser.add_argument("--file", type=str, required=True, help="Chemin du fichier à traiter")
    parser.add_argument("--vault", type=str, default="~/vaults/research", help="Chemin du vault")
    parser.add_argument("--context", type=str, help="Contexte du document")
    parser.add_argument("--no-describe", action="store_true", help="Désactiver la description des images")
    
    args = parser.parse_args()
    
    vault_path = Path(args.vault).expanduser()
    file_path = Path(args.file)
    
    if not file_path.is_absolute():
        file_path = vault_path / file_path
    
    agent = OCRAgent(vault_path)
    
    try:
        success, text, report = await agent.extract_text(
            file_path,
            context=args.context,
            describe_images=not args.no_describe,
        )
        
        if success:
            print(f"✓ Texte extrait: {file_path.name}")
            print(f"  Longueur: {len(text)} caractères")
            print(f"  Pages/images: {report['stats'].get('pages_processed', 0) + report['stats'].get('images_detected', 0)}")
            print(f"\n--- Texte extrait ---\n{text[:500]}...")
        else:
            print(f"✗ Échec: {report['errors']}")
    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
