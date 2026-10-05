"""
Agent de Prétraitement pour le système RAG Wiki.

Cet agent nettoie et optimise les documents APRES OCR.
Il ne fait PAS d'OCR (c'est le rôle de OCRAgent).
Fonctions: nettoyage, déduplication, structuration Markdown, chunking.
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import unicodedata

from ..core.config import WikiConfig, get_config
from ..storage import VaultManager
from ..utils.text_utils import clean_text, normalize_name
from ..utils.path_utils import get_file_type
from ..utils.date_utils import get_current_timestamp


class PreprocessingAgent:
    """
    Agent de prétraitement pour nettoyer et optimiser les documents APRES OCR.
    
    Fonctionnalités :
    - Nettoyage du texte (en-têtes, pieds de page, bruit)
    - Structuration en Markdown
    - Détection et suppression des redondances (>=2 occurrences)
    - Demande confirmation pour les informations uniques (1 occurrence)
    - Découpage en chunks optimisés
    - Validation de la qualité
    
    NOTE: L'OCR est géré par OCRAgent. Ce agent ne fait que le post-traitement.
    """
    
    def __init__(
        self,
        vault_path: Path,
        config: Optional[WikiConfig] = None,
    ) -> None:
        """
        Initialiser l'agent de prétraitement.
        
        Args:
            vault_path: Chemin du vault.
            config: Configuration du wiki.
        """
        self.vault_path = vault_path
        self.config = config or get_config()
        self.vault_manager = VaultManager(vault_path)
        
        # Charger la configuration Mistral
        self.mistral_config = self._load_mistral_config()
    
    def _load_mistral_config(self) -> Dict[str, Any]:
        """Charger la configuration Mistral."""
        config_path = self.vault_path / "configs" / "mistral_config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # Configuration par défaut
            return {
                "preprocessing": {
                    "deduplication": {
                        "enabled": True,
                        "similarity_threshold": 0.85,
                        "min_occurrences": 2,
                        "ask_for_unique": True,
                    },
                    "compression": {
                        "max_tokens_per_chunk": 2000,
                        "overlap_tokens": 200,
                    },
                },
            }
    
    async def preprocess(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        ask_for_confirmation: bool = True,
    ) -> Tuple[bool, Path, Dict[str, Any]]:
        """
        Prétraiter un fichier (APRES OCR).
        
        Args:
            input_path: Chemin du fichier d'entrée (déjà en texte).
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
            
            # Lire le contenu brut (déjà extrait par OCRAgent)
            raw_content, raw_size = self._read_file(input_path)
            report["stats"]["original_size"] = raw_size
            
            # Nettoyer le texte
            clean_content, cleaning_report = self._clean_text(raw_content)
            report["operations"].extend(cleaning_report.get("operations", []))
            report["warnings"].extend(cleaning_report.get("warnings", []))
            
            # Structurer en Markdown
            structured_content, struct_report = self._structure_to_markdown(clean_content)
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
            report["errors"].append(f"Erreur lors du prétraitement: {str(e)}")
            report["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            return False, input_path, report
    
    def _read_file(self, file_path: Path) -> Tuple[str, int]:
        """Lire un fichier texte."""
        with open(file_path, "rb") as f:
            content = f.read()
        
        # Décoder en UTF-8
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
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
    
    def _clean_text(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """Nettoyer le texte."""
        report: Dict[str, Any] = {"operations": [], "warnings": []}
        
        try:
            # Nettoyage de base
            clean_content = clean_text(content)
            
            # Supprimer les pages vides
            clean_content = re.sub(r'\n{3,}', '\n\n', clean_content)
            
            # Supprimer les espaces en début/fin de ligne
            clean_content = '\n'.join(line.strip() for line in clean_content.split('\n'))
            
            # Supprimer les lignes vides en trop
            clean_content = re.sub(r'\n\s*\n', '\n\n', clean_content)
            
            report["operations"].append("text_cleaning")
            
            return clean_content, report
            
        except Exception as e:
            report["warnings"].append(f"Erreur nettoyage: {str(e)}")
            return content, report
    
    def _structure_to_markdown(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """Structurer le contenu en Markdown."""
        report: Dict[str, Any] = {"operations": [], "warnings": []}
        
        # Détecter la langue
        lang = self._detect_language(content)
        
        # Structuration générique
        structured = self._structure_generic(content, lang)
        
        report["operations"].append("markdown_structuring")
        
        return structured, report
    
    def _detect_language(self, text: str) -> str:
        """Détecter la langue du texte."""
        text_lower = text.lower()
        
        french_words = ["le", "la", "les", "de", "des", "un", "une", "et", "est", "en"]
        english_words = ["the", "a", "an", "and", "is", "in", "of", "to", "for"]
        
        french_count = sum(1 for word in french_words if f" {word} " in f" {text_lower} ")
        english_count = sum(1 for word in english_words if f" {word} " in f" {text_lower} ")
        
        return "fr" if french_count > english_count else "en"
    
    def _structure_generic(self, content: str, lang: str) -> str:
        """Structurer un contenu générique en Markdown."""
        # Découper en paragraphes
        paragraphs = content.split('\n\n')
        structured_paragraphs = []
        
        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Première ligne comme titre si c'est la première
            if i == 0:
                structured_paragraphs.append(f"# {paragraph}\n")
            else:
                # Détecter les titres
                if re.match(r'^[A-Z][A-Z\s:]+$', paragraph) and len(paragraph) < 100:
                    structured_paragraphs.append(f"\n## {paragraph}\n")
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
                # Supprimer les redondances (garder la première occurrence)
                if normalized not in seen_normalized:
                    deduplicated_sentences.append(sentence)
                    seen_normalized.add(normalized)
                report["operations"].append(f"removed_redundant")
            elif normalized in unique:
                # Garder les uniques
                if ask_for_confirmation:
                    # Simuler une question (dans une vraie implémentation, on interagirait avec l'utilisateur)
                    # Ici, on garde par défaut
                    report["warnings"].append(f"Info unique détectée (à vérifier): {sentence[:50]}...")
                
                deduplicated_sentences.append(sentence)
                report["operations"].append(f"kept_unique")
            else:
                deduplicated_sentences.append(sentence)
        
        # Reconstruire le contenu
        deduplicated_content = " ".join(deduplicated_sentences)
        
        return deduplicated_content, report
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Découper le texte en phrases."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _normalize_sentence(self, sentence: str) -> str:
        """Normaliser une phrase pour la comparaison."""
        # Supprimer la ponctuation
        normalized = re.sub(r'[^\w\s]', '', sentence.lower())
        # Supprimer les mots vides
        stop_words = {"le", "la", "les", "un", "une", "des", "de", "du", "the", "a", "an", "of", "to", "in", "is", "are", "et", "est", "en", "dans", "pour"}
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
        
        # Retourner tous les chunks séparés par des marqueurs
        if len(chunks) == 1:
            return chunks[0], report
        else:
            return "\n\n---\n\nCHUNK_BREAK\n\n---\n\n".join(chunks), report
    
    async def preprocess_batch(
        self,
        input_paths: List[Path],
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Prétraiter plusieurs fichiers en batch.
        
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
