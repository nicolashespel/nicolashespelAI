"""
Agent de Préprocessing pour le système RAG Wiki.

Cet agent nettoie et optimise les documents dans raw/ avant ingestion.
Il utilise OCR pour les PDF/images, nettoie le texte, et structure en Markdown.
"""

import asyncio
import json
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import unicodedata

# Essayer d'importer les bibliothèques OCR
try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from ..core.config import WikiConfig, get_config
from ..storage import VaultManager
from ..utils.text_utils import clean_text, normalize_name
from ..utils.path_utils import get_file_type
from ..utils.date_utils import get_current_timestamp


class PreprocessingAgent:
    """
    Agent de préprocessing pour nettoyer et optimiser les documents avant ingestion.
    
    Fonctionnalités :
    - OCR pour PDF et images
    - Nettoyage du texte (en-têtes, pieds de page, bruit)
    - Structuration en Markdown
    - Détection et suppression des redondances
    - Découpage en chunks optimisés
    - Validation de la qualité
    """
    
    def __init__(
        self,
        vault_path: Path,
        config: Optional[WikiConfig] = None,
    ) -> None:
        """
        Initialiser l'agent de préprocessing.
        
        Args:
            vault_path: Chemin du vault.
            config: Configuration du wiki.
        """
        self.vault_path = vault_path
        self.config = config or get_config()
        self.vault_manager = VaultManager(vault_path)
        
        # Charger la configuration Mistral
        self.mistral_config = self._load_mistral_config()
        
        # Vérifier les dépendances
        self._check_dependencies()
    
    def _load_mistral_config(self) -> Dict[str, Any]:
        """Charger la configuration Mistral."""
        config_path = self.vault_path / "configs" / "mistral_config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # Configuration par défaut
            return {
                "ocr": {
                    "fallback": {"enabled": True, "lang": "fra+eng"},
                    "pdf": {"extract_images": True},
                },
                "preprocessing": {
                    "deduplication": {"enabled": True, "similarity_threshold": 0.85, "min_occurrences": 2, "ask_for_unique": True},
                },
            }
    
    def _check_dependencies(self) -> None:
        """Vérifier les dépendances nécessaires."""
        self.has_pypdf = HAS_PYPDF
        self.has_tesseract = HAS_TESSERACT
        self.has_pil = HAS_PIL
        
        if not self.has_pypdf:
            print("⚠️  PyPDF non disponible. Installation : pip install pypdf")
        if not self.has_tesseract:
            print("⚠️  Tesseract non disponible. Installation : pip install pytesseract + tesseract-ocr")
        if not self.has_pil:
            print("⚠️  PIL non disponible. Installation : pip install pillow")
    
    async def preprocess(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        ask_for_confirmation: bool = True,
    ) -> Tuple[bool, Path, Dict[str, Any]]:
        """
        Préprocesser un fichier.
        
        Args:
            input_path: Chemin du fichier d'entrée.
            output_path: Chemin du fichier de sortie (optionnel).
            ask_for_confirmation: Demander confirmation pour les suppressions.
            
        Returns:
            Tuple avec (succès, chemin_sortie, rapport).
        """
        start_time = datetime.now()
        report: Dict[str, Any] = {
            "input_path": str(input_path),
            "output_path": "",
            "operations": [],
            "warnings": [],
            "errors": [],
            "stats": {
                "original_size": 0,
                "cleaned_size": 0,
                "redundant_removed": 0,
                "unique_kept": 0,
                "chunks_created": 0,
            },
            "duration_seconds": 0,
        }
        
        try:
            # Vérifier que le fichier existe
            if not input_path.exists():
                report["errors"].append(f"Fichier non trouvé: {input_path}")
                return False, input_path, report
            
            # Déterminer le type de fichier
            file_type = get_file_type(input_path)
            report["file_type"] = file_type
            
            # Lire le contenu brut
            raw_content, raw_size = self._read_file(input_path)
            report["stats"]["original_size"] = raw_size
            
            # Préprocessing selon le type
            if file_type == "pdf":
                clean_content, preprocessing_report = await self._preprocess_pdf(input_path, raw_content)
            elif file_type == "html":
                clean_content, preprocessing_report = self._preprocess_html(raw_content)
            elif file_type in ["markdown", "md"]:
                clean_content, preprocessing_report = self._preprocess_markdown(raw_content)
            elif file_type == "text":
                clean_content, preprocessing_report = self._preprocess_text(raw_content)
            else:
                clean_content = raw_content
                preprocessing_report = {"operations": ["copy"]}
            
            # Mettre à jour le rapport
            report["operations"].extend(preprocessing_report.get("operations", []))
            report["warnings"].extend(preprocessing_report.get("warnings", []))
            
            # Structurer en Markdown
            structured_content, struct_report = self._structure_to_markdown(clean_content, file_type)
            report["operations"].extend(struct_report.get("operations", []))
            
            # Détecter et supprimer les redondances
            deduplicated_content, dedup_report = await self._remove_redundancies(
                structured_content,
                ask_for_confirmation=ask_for_confirmation,
            )
            report["operations"].extend(dedup_report.get("operations", []))
            report["stats"]["redundant_removed"] = dedup_report.get("redundant_removed", 0)
            report["stats"]["unique_kept"] = dedup_report.get("unique_kept", 0)
            
            # Découper en chunks si nécessaire
            final_content, chunk_report = self._chunk_content(deduplicated_content)
            report["stats"]["chunks_created"] = chunk_report.get("chunks_created", 0)
            
            # Déterminer le chemin de sortie
            if output_path is None:
                output_dir = self.vault_path / "raw" / "clean"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"{input_path.stem}.md"
            
            # Sauvegarder le fichier
            self._save_file(output_path, final_content)
            report["output_path"] = str(output_path)
            report["stats"]["cleaned_size"] = len(final_content.encode('utf-8'))
            
            # Calculer la durée
            report["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            
            return True, output_path, report
            
        except Exception as e:
            report["errors"].append(f"Erreur lors du préprocessing: {str(e)}")
            report["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            return False, input_path, report
    
    def _read_file(self, file_path: Path) -> Tuple[str, int]:
        """Lire un fichier."""
        with open(file_path, "rb") as f:
            content = f.read()
        
        # Essayer de décoder en UTF-8
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            # Essayer Latin-1
            try:
                text = content.decode('latin-1')
            except Exception:
                text = content.decode('utf-8', errors='replace')
        
        return text, len(content)
    
    def _save_file(self, file_path: Path, content: str) -> None:
        """Sauvegarder un fichier."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    async def _preprocess_pdf(
        self,
        file_path: Path,
        raw_content: str,
    ) -> Tuple[str, Dict[str, Any]]:
        """Préprocesser un PDF."""
        report: Dict[str, Any] = {"operations": [], "warnings": []}
        
        if not self.has_pypdf:
            report["warnings"].append("PyPDF non disponible, utilisation de l'extraction basique")
            return raw_content, report
        
        try:
            # Extraire le texte avec PyPDF
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
            
            text_content = "\n".join([page.extract_text() for page in reader.pages])
            
            # Nettoyer le texte
            clean_text_content = clean_text(text_content)
            
            report["operations"].append("pdf_text_extraction")
            
            # Extraire les images et faire OCR si Tesseract est disponible
            if self.has_tesseract and self.has_pil and self.mistral_config.get("ocr", {}).get("pdf", {}).get("extract_images", False):
                images_text = await self._extract_images_from_pdf(reader)
                if images_text:
                    clean_text_content += "\n\n" + images_text
                    report["operations"].append("pdf_image_ocr")
            
            return clean_text_content, report
            
        except Exception as e:
            report["warnings"].append(f"Erreur PDF: {str(e)}")
            return raw_content, report
    
    async def _extract_images_from_pdf(self, reader) -> str:
        """Extraire le texte des images dans un PDF."""
        images_text = []
        
        for page in reader.pages:
            if "/XObject" in page["Resources"]:
                xobjects = page["Resources"]["XObject"].get_object()
                for obj_name in xobjects:
                    obj = xobjects[obj_name]
                    if obj["Subtype"] == "/Image":
                        try:
                            # Extraire l'image (simplifié)
                            image_data = obj.get_data()
                            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                                tmp.write(image_data)
                                tmp_path = tmp.name
                            
                            # OCR avec Tesseract
                            text = pytesseract.image_to_string(Image.open(tmp_path), lang=self.mistral_config["ocr"]["fallback"]["lang"])
                            if text.strip():
                                images_text.append(text.strip())
                        except Exception:
                            pass
        
        return "\n\n".join(images_text)
    
    def _preprocess_html(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """Préprocesser du HTML."""
        report: Dict[str, Any] = {"operations": [], "warnings": []}
        
        try:
            # Extraire le texte principal
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Supprimer les scripts et styles
            for script in soup(["script", "style", "noscript", "meta", "link"]):
                script.decompose()
            
            # Extraire le texte
            text = soup.get_text()
            
            # Nettoyer
            clean_text_content = clean_text(text)
            
            report["operations"].append("html_cleaning")
            
            return clean_text_content, report
            
        except Exception as e:
            report["warnings"].append(f"Erreur HTML: {str(e)}")
            return content, report
    
    def _preprocess_markdown(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """Préprocesser du Markdown."""
        report: Dict[str, Any] = {"operations": [], "warnings": []}
        
        # Nettoyer le contenu
        clean_content = clean_text(content)
        
        # Supprimer les métadonnées YAML si présentes
        clean_content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', clean_content, flags=re.DOTALL)
        
        report["operations"].append("markdown_cleaning")
        
        return clean_content, report
    
    def _preprocess_text(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """Préprocesser du texte brut."""
        report: Dict[str, Any] = {"operations": [], "warnings": []}
        
        # Nettoyer le contenu
        clean_content = clean_text(content)
        
        report["operations"].append("text_cleaning")
        
        return clean_content, report
    
    def _structure_to_markdown(self, content: str, file_type: str) -> Tuple[str, Dict[str, Any]]:
        """Structurer le contenu en Markdown."""
        report: Dict[str, Any] = {"operations": [], "warnings": []}
        
        # Détecter la langue
        lang = self._detect_language(content)
        
        # Structurer selon le type
        if file_type == "pdf":
            structured = self._structure_pdf(content, lang)
        else:
            structured = self._structure_generic(content, lang)
        
        report["operations"].append("markdown_structuring")
        
        return structured, report
    
    def _detect_language(self, text: str) -> str:
        """Détecter la langue du texte."""
        # Simple detection based on common words
        text_lower = text.lower()
        
        french_words = ["le", "la", "les", "de", "des", "un", "une", "et", "est", "en"]
        english_words = ["the", "a", "an", "and", "is", "in", "of", "to", "for"]
        
        french_count = sum(1 for word in french_words if f" {word} " in f" {text_lower} ")
        english_count = sum(1 for word in english_words if f" {word} " in f" {text_lower} ")
        
        if french_count > english_count:
            return "fr"
        else:
            return "en"
    
    def _structure_pdf(self, content: str, lang: str) -> str:
        """Structurer un contenu PDF en Markdown."""
        lines = content.split('\n')
        structured_lines = []
        
        in_code_block = False
        in_list = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Détecter les titres
            if re.match(r'^[A-Z][A-Z\s]+$', line) and len(line) < 50:
                structured_lines.append(f"# {line}\n")
            elif re.match(r'^[0-9]+(\.[0-9]+)*\s+', line):
                # Numérotation de section
                structured_lines.append(f"\n## {line}\n")
            elif re.match(r'^[••-]\s+', line):
                # Liste
                structured_lines.append(f"- {line[2:]}")
            elif re.match(r'^[0-9]+\.\s+', line):
                # Liste numérotée
                structured_lines.append(f"1. {line[3:]}")
            else:
                structured_lines.append(line)
        
        return "\n".join(structured_lines)
    
    def _structure_generic(self, content: str, lang: str) -> str:
        """Structurer un contenu générique en Markdown."""
        # Simple structuration
        paragraphs = content.split('\n\n')
        structured_paragraphs = []
        
        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Première ligne comme titre
            if i == 0:
                structured_paragraphs.append(f"# {paragraph}\n")
            else:
                structured_paragraphs.append(f"\n{paragraph}\n")
        
        return "".join(structured_paragraphs)
    
    async def _remove_redundancies(
        self,
        content: str,
        ask_for_confirmation: bool = True,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Supprimer les redondances dans le contenu.
        
        Args:
            content: Contenu à analyser.
            ask_for_confirmation: Demander confirmation pour les infos uniques.
            
        Returns:
            Tuple avec (contenu dédupliqué, rapport).
        """
        report: Dict[str, Any] = {
            "operations": [],
            "warnings": [],
            "redundant_removed": 0,
            "unique_kept": 0,
            "questions": [],
        }
        
        # Découper en phrases
        sentences = self._split_into_sentences(content)
        
        # Compter les occurrences
        sentence_counts = {}
        for sentence in sentences:
            normalized = self._normalize_sentence(sentence)
            sentence_counts[normalized] = sentence_counts.get(normalized, 0) + 1
        
        # Séparer les redondances et les uniques
        redundant = {s for s, count in sentence_counts.items() if count >= 2}
        unique = {s for s, count in sentence_counts.items() if count == 1}
        
        report["redundant_removed"] = len(redundant)
        report["unique_kept"] = len(unique)
        
        # Construire le contenu dédupliqué
        deduplicated_sentences = []
        seen_normalized = set()
        
        for sentence in sentences:
            normalized = self._normalize_sentence(sentence)
            
            if normalized in redundant:
                # Supprimer les redondances
                if normalized not in seen_normalized:
                    deduplicated_sentences.append(sentence)
                    seen_normalized.add(normalized)
                report["operations"].append(f"removed_redundant_{normalized[:30]}")
            elif normalized in unique:
                # Garder les uniques, mais poser des questions
                if ask_for_confirmation:
                    # Simuler une question (dans une vraie implémentation, on interagirait avec l'utilisateur)
                    question = {
                        "sentence": sentence,
                        "normalized": normalized,
                        "action": "keep",  # Par défaut on garde
                    }
                    report["questions"].append(question)
                    report["warnings"].append(f"Unique info detected: {normalized[:50]}...")
                
                deduplicated_sentences.append(sentence)
                report["operations"].append(f"kept_unique_{normalized[:30]}")
            else:
                deduplicated_sentences.append(sentence)
        
        # Reconstruire le contenu
        deduplicated_content = " ".join(deduplicated_sentences)
        
        return deduplicated_content, report
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Découper le texte en phrases."""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _normalize_sentence(self, sentence: str) -> str:
        """Normaliser une phrase pour la comparaison."""
        # Supprimer la ponctuation
        normalized = re.sub(r'[^\w\s]', '', sentence.lower())
        # Supprimer les mots vides
        stop_words = {"le", "la", "les", "un", "une", "des", "de", "du", "the", "a", "an", "of", "to", "in", "is", "are"}
        words = normalized.split()
        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
        return " ".join(filtered_words)
    
    def _chunk_content(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """Découper le contenu en chunks optimisés."""
        report: Dict[str, Any] = {"operations": [], "chunks_created": 0}
        
        max_chunk_size = self.mistral_config.get("preprocessing", {}).get("compression", {}).get("max_tokens_per_chunk", 2000)
        overlap = self.mistral_config.get("preprocessing", {}).get("compression", {}).get("overlap_tokens", 200)
        
        # Estimer la taille en tokens (1 token ≈ 4 caractères)
        estimated_tokens = len(content) // 4
        
        if estimated_tokens <= max_chunk_size:
            return content, report
        
        # Découper en chunks
        chunks = []
        chunk_size_chars = max_chunk_size * 4
        overlap_chars = overlap * 4
        
        start = 0
        while start < len(content):
            end = min(start + chunk_size_chars, len(content))
            chunk = content[start:end]
            chunks.append(chunk)
            
            if end < len(content):
                # Ajouter l'overlap
                start = end - overlap_chars
            else:
                start = end
        
        report["chunks_created"] = len(chunks)
        report["operations"].append(f"chunked_{len(chunks)}_parts")
        
        # Retourner le premier chunk (ou tout si un seul)
        if len(chunks) == 1:
            return chunks[0], report
        else:
            # Retourner tous les chunks séparés par des marqueurs
            return "\n\n---\n\nCHUNK_BREAK\n\n---\n\n".join(chunks), report
    
    async def preprocess_batch(
        self,
        input_paths: List[Path],
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Préprocesser plusieurs fichiers en batch.
        
        Args:
            input_paths: Liste des chemins d'entrée.
            output_dir: Dossier de sortie (optionnel).
            
        Returns:
            Rapport global.
        """
        global_report: Dict[str, Any] = {
            "total_files": len(input_paths),
            "successful": 0,
            "failed": 0,
            "files": {},
            "duration_seconds": 0,
        }
        
        start_time = datetime.now()
        
        for input_path in input_paths:
            try:
                success, output_path, report = await self.preprocess(input_path, output_dir=output_dir)
                
                if success:
                    global_report["successful"] += 1
                else:
                    global_report["failed"] += 1
                
                global_report["files"][str(input_path)] = report
                
            except Exception as e:
                global_report["failed"] += 1
                global_report["files"][str(input_path)] = {
                    "error": str(e),
                    "success": False,
                }
        
        global_report["duration_seconds"] = (datetime.now() - start_time).total_seconds()
        
        return global_report
    
    def close(self) -> None:
        """Fermer les ressources."""
        self.vault_manager.close()
