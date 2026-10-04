"""
Agent Wiki Librarian pour le système RAG Wiki.

Cet agent gère les requêtes sur le vault et la génération de réponses.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import WikiConfig
from ..core.wiki_engine import WikiEngine
from ..storage import VaultManager
from .base_agent import BaseAgent


class WikiLibrarianAgent(BaseAgent):
    """
    Agent Wiki Librarian pour le système RAG Wiki.
    
    Cet agent est responsable des requêtes sur le vault :
    - Analyse des requêtes
    - Recherche en couches
    - Synthèse des réponses
    - Génération de citations
    - Offre de sauvegarde
    """
    
    def __init__(
        self,
        vault_path: Path,
        config: Optional[WikiConfig] = None,
    ) -> None:
        """
        Initialiser l'agent Wiki Librarian.
        
        Args:
            vault_path: Chemin du vault.
            config: Configuration du wiki.
        """
        super().__init__(
            name="WikiLibrarian",
            role="Recherche et réponse aux requêtes sur le vault",
            vault_manager=VaultManager(vault_path),
            config=config or WikiConfig(vault_path=vault_path),
        )
        
        self.wiki_engine = WikiEngine(config=self.config, vault_path=vault_path)
    
    async def execute(
        self,
        query: str,
        use_index: bool = True,
        use_bm25: bool = True,
        use_embeddings: bool = True,
        save_if_useful: bool = True,
    ) -> Dict[str, Any]:
        """
        Exécuter une requête sur le vault.
        
        Args:
            query: Requête à effectuer.
            use_index: Utiliser la recherche dans l'index.
            use_bm25: Utiliser BM25.
            use_embeddings: Utiliser les embeddings.
            save_if_useful: Sauvegarder la réponse si utile.
            
        Returns:
            Rapport de requête.
        """
        report: Dict[str, Any] = {
            "query": query,
            "use_index": use_index,
            "use_bm25": use_bm25,
            "use_embeddings": use_embeddings,
            "result": {},
            "saved": False,
            "save_path": "",
            "success": False,
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            # Effectuer la requête
            result = await self.wiki_engine.query(
                query_text=query,
                use_index=use_index,
                use_bm25=use_bm25,
                use_embeddings=use_embeddings,
            )
            
            report["result"] = {
                "success": result.success,
                "answer": result.answer,
                "cited_pages": result.cited_pages,
                "duration_seconds": result.duration_seconds,
                "error": result.error,
            }
            
            report["success"] = result.success
            
            # Proposer de sauvegarder si la réponse est utile
            if save_if_useful and result.success and self._is_useful_answer(result.answer):
                # Générer un nom de fichier
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                query_slug = self._slugify(query[:50])
                save_path = self.vault_path / "wiki" / "synthesis" / f"{timestamp}_{query_slug}.md"
                
                # Sauvegarder
                self._save_answer(result.answer, result.cited_pages, save_path)
                report["saved"] = True
                report["save_path"] = str(save_path)
            
            return report
            
        except Exception as e:
            report["error"] = str(e)
            report["success"] = False
            return report
    
    def _is_useful_answer(self, answer: str) -> bool:
        """
        Déterminer si une réponse est utile et doit être sauvegardée.
        
        Args:
            answer: Réponse à évaluer.
            
        Returns:
            True si la réponse est utile.
        """
        # Simple heuristique
        if not answer:
            return False
        
        # Vérifier la longueur
        if len(answer) < 100:
            return False
        
        # Vérifier la présence de contenu structuré
        if "##" in answer or "**" in answer or "- [" in answer:
            return True
        
        return False
    
    def _slugify(self, text: str) -> str:
        """
        Convertir un texte en slug.
        
        Args:
            text: Texte à convertir.
            
        Returns:
            Slug.
        """
        from ..utils.text_utils import normalize_name
        return normalize_name(text)
    
    def _save_answer(self, answer: str, cited_pages: List[str], save_path: Path) -> None:
        """
        Sauvegarder une réponse.
        
        Args:
            answer: Réponse à sauvegarder.
            cited_pages: Pages citées.
            save_path: Chemin de sauvegarde.
        """
        # Ajouter les métadonnées
        content = f"""---
type: synthesis
name: Réponse à une requête
description: Réponse générée par le Wiki Librarian
domain: query
scope: answer
tags:
  - query
  - auto-generated
related: {cited_pages}
sources: []
status: draft
confidence: medium
created: {datetime.now().isoformat()}
updated: {datetime.now().isoformat()}
---

{answer}

## Références
"""
        
        for page in cited_pages:
            content += f"- [[{page}]]\n"
        
        # Sauvegarder
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    async def query_batch(
        self,
        queries: List[str],
    ) -> Dict[str, Any]:
        """
        Effectuer plusieurs requêtes en batch.
        
        Args:
            queries: Liste des requêtes.
            
        Returns:
            Rapport global.
        """
        global_report: Dict[str, Any] = {
            "total_queries": len(queries),
            "successful": 0,
            "failed": 0,
            "queries": {},
            "timestamp": datetime.now().isoformat(),
        }
        
        for query in queries:
            try:
                report = await self.execute(query)
                
                if report["success"]:
                    global_report["successful"] += 1
                else:
                    global_report["failed"] += 1
                
                global_report["queries"][query] = report
                
            except Exception as e:
                global_report["failed"] += 1
                global_report["queries"][query] = {
                    "error": str(e),
                    "success": False,
                }
        
        return global_report
    
    def close(self) -> None:
        """Fermer les ressources."""
        self.wiki_engine.close()
        self.vault_manager.close()
