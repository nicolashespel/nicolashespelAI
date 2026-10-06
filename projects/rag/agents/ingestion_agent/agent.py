"""
Ingestion Agent - Agent d'ingestion pour le système RAG Wiki.

Cet agent utilise:
- Mistral Large pour comprendre et structurer le contenu
- Mistral Embed pour générer les embeddings
- BM25 et recherche hybride pour l'indexation
- Découpage intelligent pour les longs documents
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .chunking import TextChunker
from .embedding import TextEmbedder
from .indexing import ContentIndexer

logger = logging.getLogger(__name__)


class IngestionAgent:
    """
    Agent d'ingestion pour le système RAG Wiki.
    
    Cet agent est responsable de:
    1. Le découpage des documents en chunks optimisés
    2. La génération d'embeddings avec Mistral Embed
    3. L'indexation dans BM25 et l'index hybride
    4. La création des pages wiki structurées
    5. La mise à jour de l'index et du log
    
    Commande OpenWebUI: `/ingest`
    """
    
    def __init__(
        self,
        vault_path: Union[Path, str],
        api_key: Optional[str] = None,
        config_path: Optional[str] = None,
    ) -> None:
        """
        Initialiser l'agent d'ingestion.
        
        Args:
            vault_path: Chemin du vault.
            api_key: Clé API Mistral.
            config_path: Chemin du fichier de configuration.
        """
        self.vault_path = Path(vault_path) if isinstance(vault_path, str) else vault_path
        self.vault_path.mkdir(parents=True, exist_ok=True)
        
        # Charger la configuration
        self.config = self._load_config(config_path)
        
        # Initialiser les composants
        self.chunker = TextChunker(
            chunk_size=self.config.get("chunk_size", 2000),
            chunk_overlap=self.config.get("chunk_overlap", 200),
            max_tokens=self.config.get("max_tokens", 8192),
            preserve_important=self.config.get("preserve_important", []),
        )
        
        self.embedder = TextEmbedder(
            api_key=api_key,
            api_base_url=self.config.get("api_base_url", "https://api.mistral.ai/v1"),
            model=self.config.get("embedding_model", "mistral-embed"),
            dimension=self.config.get("embedding_dimension", 1024),
            batch_size=self.config.get("batch_size", 32),
            timeout=self.config.get("timeout", 120),
            max_retries=self.config.get("max_retries", 3),
        )
        
        self.indexer = ContentIndexer(
            index_dir=self.vault_path / "indexes",
            use_bm25=self.config.get("use_bm25", True),
            use_embeddings=self.config.get("use_embeddings", True),
            bm25_k1=self.config.get("bm25_k1", 1.5),
            bm25_b=self.config.get("bm25_b", 0.75),
            embedding_dimension=self.config.get("embedding_dimension", 1024),
        )
        
        # Chemins
        self.cleaned_dir = self.vault_path / "cleaned"
        self.wiki_dir = self.vault_path / "wiki"
        self.sources_dir = self.wiki_dir / "sources"
        self.entities_dir = self.wiki_dir / "entities"
        self.concepts_dir = self.wiki_dir / "concepts"
        self.index_file = self.wiki_dir / "index.md"
        self.log_file = self.wiki_dir / "log.md"
        
        # Créer les dossiers si nécessaire
        self.cleaned_dir.mkdir(exist_ok=True)
        self.wiki_dir.mkdir(exist_ok=True)
        self.sources_dir.mkdir(exist_ok=True)
        self.entities_dir.mkdir(exist_ok=True)
        self.concepts_dir.mkdir(exist_ok=True)
        
        # Historique
        self.history: List[Dict[str, Any]] = []
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Charger la configuration."""
        default_config = {
            "api_base_url": "https://api.mistral.ai/v1",
            "timeout": 120,
            "max_retries": 3,
            "chunk_size": 2000,
            "chunk_overlap": 200,
            "max_tokens": 8192,
            "embedding_model": "mistral-embed",
            "embedding_dimension": 1024,
            "batch_size": 32,
            "use_bm25": True,
            "use_embeddings": True,
            "bm25_k1": 1.5,
            "bm25_b": 0.75,
            "preserve_important": ["titles", "authors", "dates", "citations", "code", "formulas"],
        }
        
        # Charger depuis le fichier si spécifié
        if config_path:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                default_config.update(file_config.get("ingestion_agent", {}))
        
        # Charger depuis le vault
        vault_config = self.vault_path / "configs" / "agents_config.json"
        if vault_config.exists():
            with open(vault_config, "r", encoding="utf-8") as f:
                file_config = json.load(f)
            agent_config = file_config.get("agents", {}).get("ingestion_agent", {})
            default_config.update(agent_config.get("features", {}).get("chunking", {}))
            default_config.update(agent_config.get("features", {}).get("embedding", {}))
            default_config.update(agent_config.get("features", {}).get("indexing", {}))
        
        return default_config
    
    def _generate_doc_id(self, file_path: Path) -> str:
        """Générer un ID unique pour un document."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{file_path.stem}"
    
    def _extract_metadata(self, file_path: Path, text: str) -> Dict[str, Any]:
        """Extraire les métadonnées d'un document."""
        metadata = {
            "source_file": file_path.name,
            "source_path": str(file_path),
            "ingestion_date": datetime.now().isoformat(),
            "char_count": len(text),
            "token_count": len(text) // 4,  # Estimation
            "language": "unknown",
        }
        
        # Détecter la langue (simplifié)
        text_lower = text.lower()
        french_words = ["le", "la", "les", "de", "des", "un", "une"]
        english_words = ["the", "a", "an", "and", "is", "in", "on"]
        
        french_count = sum(text_lower.count(word) for word in french_words)
        english_count = sum(text_lower.count(word) for word in english_words)
        
        if french_count > english_count:
            metadata["language"] = "fr"
        elif english_count > french_count:
            metadata["language"] = "en"
        
        return metadata
    
    async def _process_file(
        self,
        file_path: Path,
        preprocess: bool = True,
    ) -> Dict[str, Any]:
        """Traiter un fichier pour ingestion."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                "success": False,
                "file": str(file_path),
                "error": "Fichier non trouvé",
            }
        
        try:
            # Lire le fichier
            if file_path.suffix == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                text = data.get("text", "")
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            
            if not text or len(text.strip()) == 0:
                return {
                    "success": False,
                    "file": str(file_path),
                    "error": "Fichier vide",
                }
            
            # Extraire les métadonnées
            metadata = self._extract_metadata(file_path, text)
            
            # Découper le texte
            chunks = self.chunker.chunk_text(text)
            
            logger.info(f"Découpage: {len(chunks)} chunks pour {file_path.name}")
            
            # Générer les embeddings
            chunks_with_embeddings = await self.embedder.embed_chunks(chunks)
            
            logger.info(f"Embeddings: {len(chunks_with_embeddings)} chunks avec embeddings")
            
            # Générer un ID pour le document
            doc_id = self._generate_doc_id(file_path)
            
            # Ajouter à l'index
            for chunk in chunks_with_embeddings:
                chunk_id = f"{doc_id}_chunk_{chunk['index']}"
                
                self.indexer.add_document(
                    doc_id=chunk_id,
                    text=chunk["text"],
                    embedding=chunk.get("embedding"),
                    metadata={
                        **metadata,
                        "chunk_index": chunk["index"],
                        "chunk_total": len(chunks),
                    },
                )
            
            # Créer la page source dans wiki
            source_page = self._create_source_page(file_path, text, metadata, doc_id)
            
            # Mettre à jour l'index
            self._update_index(file_path, source_page, metadata)
            
            # Logger l'opération
            self._log_operation("ingest", file_path, metadata)
            
            return {
                "success": True,
                "file": str(file_path),
                "doc_id": doc_id,
                "chunks": len(chunks),
                "source_page": source_page,
                "metadata": metadata,
            }
            
        except Exception as e:
            logger.error(f"Échec de l'ingestion pour {file_path.name}: {e}")
            return {
                "success": False,
                "file": str(file_path),
                "error": str(e),
            }
    
    def _create_source_page(
        self,
        file_path: Path,
        text: str,
        metadata: Dict[str, Any],
        doc_id: str,
    ) -> str:
        """Créer une page source dans wiki/sources/."""
        # Déterminer le type de source
        extension = file_path.suffix.lower()
        if extension == ".pdf":
            source_type = "pdf"
        elif extension in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]:
            source_type = "image"
        elif extension == ".txt":
            source_type = "text"
        elif extension == ".md":
            source_type = "markdown"
        else:
            source_type = "document"
        
        # Créer le nom de la page
        timestamp = datetime.now().strftime("%Y%m%d")
        page_name = f"{timestamp}_{doc_id}.md"
        page_path = self.sources_dir / page_name
        
        # Créer le contenu de la page
        content = self._generate_source_content(file_path, text, metadata, source_type)
        
        # Sauvegarder la page
        with open(page_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Page source créée: {page_name}")
        return str(page_path)
    
    def _generate_source_content(
        self,
        file_path: Path,
        text: str,
        metadata: Dict[str, Any],
        source_type: str,
    ) -> str:
        """Générer le contenu d'une page source."""
        # Résumer le texte pour l'affichage
        summary = text[:1000] + "..." if len(text) > 1000 else text
        
        # Formater les métadonnées
        date_str = metadata.get("ingestion_date", "").split("T")[0]
        
        content = f"""---
type: source
source_type: {source_type}
original_path: {file_path}
title: {file_path.stem}
authors: []
date: {date_str}
url: 
summary: {summary[:200]}...
status: processed
tags: [ocr, {source_type}]
related: []
sources: []
created: {metadata.get('ingestion_date', '')}
updated: {metadata.get('ingestion_date', '')}
ingested: {metadata.get('ingestion_date', '')}
---

# {file_path.name}

## Métadonnées
- **Type:** {source_type}
- **Fichier original:** {file_path}
- **Date d'ingestion:** {date_str}
- **Langue:** {metadata.get('language', 'unknown')}
- **Nombre de caractères:** {metadata.get('char_count', 0)}
- **Nombre de tokens:** {metadata.get('token_count', 0)}

## Résumé
{summary[:500]}{'...' if len(text) > 500 else ''}

## Texte complet

```
{text}
```

## Liens
- [[index]]
"""
        return content
    
    def _update_index(self, file_path: Path, source_page: str, metadata: Dict[str, Any]) -> None:
        """Mettre à jour le fichier index.md."""
        if not self.index_file.exists():
            self._create_index_file()
        
        # Lire l'index existant
        with open(self.index_file, "r", encoding="utf-8") as f:
            index_content = f.read()
        
        # Ajouter la nouvelle source
        new_entry = f"- [{file_path.stem}]({source_page.relpath(self.wiki_dir)}) - {metadata.get('language', 'unknown')} - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Trouver la section Sources
        lines = index_content.split('\n')
        new_lines = []
        in_sources = False
        sources_added = False
        
        for line in lines:
            new_lines.append(line)
            
            if line.startswith('## Sources'):
                in_sources = True
            elif in_sources and line.startswith('##') and not sources_added:
                # Ajouter avant la prochaine section
                new_lines.append('')
                new_lines.append(new_entry)
                new_lines.append('')
                sources_added = True
        
        # Si la section Sources n'existe pas, l'ajouter
        if not sources_added:
            new_lines.append('')
            new_lines.append('## Sources')
            new_lines.append('')
            new_lines.append(new_entry)
        
        # Mettre à jour le compteur
        for i, line in enumerate(new_lines):
            if line.startswith('- **Total Sources:**'):
                new_lines[i] = f"- **Total Sources:** {len(list(self.sources_dir.glob('*.md')))}"
                break
        
        # Sauvegarder l'index
        with open(self.index_file, "w", encoding="utf-8") as f:
            f.write('\n'.join(new_lines))
        
        logger.info("Index mis à jour")
    
    def _create_index_file(self) -> None:
        """Créer le fichier index.md si inexistant."""
        index_content = f"""# Index du Vault - {self.vault_path.name}

## Statistiques
- **Total Pages:** 0
- **Sources:** 0
- **Entités:** 0
- **Concepts:** 0
- **Comparaisons:** 0
- **Synthèses:** 0

## Pages par Type

### Sources

### Entités

### Concepts

### Comparaisons

### Synthèses

## Dernières Mises à Jour
"""
        with open(self.index_file, "w", encoding="utf-8") as f:
            f.write(index_content)
    
    def _log_operation(self, operation: str, file_path: Path, metadata: Dict[str, Any]) -> None:
        """Logger une opération dans log.md."""
        log_entry = f"""- [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{operation.upper()}] {file_path.name}
  - source: {file_path}
  - doc_id: {metadata.get('doc_id', 'N/A')}
  - chunks: {metadata.get('chunks', 'N/A')}
  - language: {metadata.get('language', 'unknown')}
  - status: success
"""
        
        if not self.log_file.exists():
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write("# Log des Opérations\n\n")
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
        
        logger.info(f"Opération loggée: {operation} - {file_path.name}")
    
    async def ingest(
        self,
        input_path: Union[Path, str],
        vault: Optional[Union[Path, str]] = None,
        mode: str = "full",
        preprocess: bool = True,
    ) -> Dict[str, Any]:
        """
        Ingestion d'un fichier ou dossier.
        
        Args:
            input_path: Chemin du fichier ou dossier à ingérer.
            vault: Chemin du vault (par défaut: celui de l'agent).
            mode: Mode d'ingestion (full, text_only, metadata_only).
            preprocess: Prétraiter avant ingestion.
            
        Returns:
            Résultat de l'ingestion.
        """
        start_time = datetime.now()
        input_path = Path(input_path)
        
        # Définir le vault si spécifié
        if vault:
            self.vault_path = Path(vault) if isinstance(vault, str) else vault
            self._update_paths()
        
        # Initialiser le rapport
        report: Dict[str, Any] = {
            "success": True,
            "start_time": start_time.isoformat(),
            "input": str(input_path),
            "vault": str(self.vault_path),
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
                result = await self._process_file(input_path, preprocess)
                
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
                    self._process_file(f, preprocess)
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
            
            # Mettre à jour les statistiques de l'index
            report["index_stats"] = self.indexer.get_statistics()
            
            # Ajouter à l'historique
            self.history.append(report)
            
            logger.info(
                f"Ingestion terminée: {report['files_processed']} fichiers, "
                f"{report['files_successful']} réussis, "
                f"{report['files_failed']} échoués"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ingestion: {e}")
            return {
                "success": False,
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
            }
    
    def _update_paths(self) -> None:
        """Mettre à jour les chemins après changement de vault."""
        self.cleaned_dir = self.vault_path / "cleaned"
        self.wiki_dir = self.vault_path / "wiki"
        self.sources_dir = self.wiki_dir / "sources"
        self.entities_dir = self.wiki_dir / "entities"
        self.concepts_dir = self.wiki_dir / "concepts"
        self.index_file = self.wiki_dir / "index.md"
        self.log_file = self.wiki_dir / "log.md"
        
        self.cleaned_dir.mkdir(exist_ok=True)
        self.wiki_dir.mkdir(exist_ok=True)
        self.sources_dir.mkdir(exist_ok=True)
        self.entities_dir.mkdir(exist_ok=True)
        self.concepts_dir.mkdir(exist_ok=True)
        
        # Recharger l'indexer avec le nouveau vault
        self.indexer = ContentIndexer(
            index_dir=self.vault_path / "indexes",
            use_bm25=self.config.get("use_bm25", True),
            use_embeddings=self.config.get("use_embeddings", True),
            bm25_k1=self.config.get("bm25_k1", 1.5),
            bm25_b=self.config.get("bm25_b", 0.75),
            embedding_dimension=self.config.get("embedding_dimension", 1024),
        )
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Obtenir l'historique des ingestions."""
        return self.history
    
    def clear_history(self) -> None:
        """Effacer l'historique."""
        self.history = []
    
    async def close(self) -> None:
        """Fermer les ressources."""
        await self.embedder.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.run(self.close())


# Instance globale pour OpenWebUI
_ingestion_agent: Optional[IngestionAgent] = None


def get_ingestion_agent(
    vault_path: Union[Path, str] = Path("~/vaults/knowledge_base").expanduser(),
    api_key: Optional[str] = None,
) -> IngestionAgent:
    """Obtenir une instance globale de l'agent d'ingestion."""
    global _ingestion_agent
    
    if _ingestion_agent is None:
        _ingestion_agent = IngestionAgent(vault_path, api_key)
    
    return _ingestion_agent


def reset_ingestion_agent() -> None:
    """Réinitialiser l'instance globale."""
    global _ingestion_agent
    _ingestion_agent = None
