"""
Search Agent - Agent de recherche pour le système RAG Wiki.

Cet agent utilise:
- Recherche hybride (BM25 + Mistral Embed)
- Reclassement avec Mistral Small
- Synthèse avec Mistral Large
- Citations automatiques
- Formatage optimisé pour les résultats
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .retriever import HybridRetriever
from .reranker import ResultReranker
from .synthesizer import ResponseSynthesizer

logger = logging.getLogger(__name__)


class SearchAgent:
    """
    Agent de recherche pour le système RAG Wiki.
    
    Cet agent est responsable de:
    1. La recherche dans le RAG (hybride BM25 + embeddings)
    2. Le reclassement des résultats avec Mistral Small
    3. La synthèse de la réponse avec Mistral Large
    4. L'ajout de citations automatiques
    5. La sauvegarde des réponses utiles
    
    Commande OpenWebUI: `/search` ou `/query`
    """
    
    def __init__(
        self,
        vault_path: Union[Path, str],
        api_key: Optional[str] = None,
        config_path: Optional[str] = None,
    ) -> None:
        """
        Initialiser l'agent de recherche.
        
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
        self.retriever = HybridRetriever(
            index_dir=self.vault_path / "indexes",
            use_bm25=self.config.get("use_bm25", True),
            use_embeddings=self.config.get("use_embeddings", True),
            bm25_k1=self.config.get("bm25_k1", 1.5),
            bm25_b=self.config.get("bm25_b", 0.75),
            embedding_dimension=self.config.get("embedding_dimension", 1024),
            bm25_top_k=self.config.get("bm25_top_k", 50),
            embedding_top_k=self.config.get("embedding_top_k", 10),
            rrf_k=self.config.get("rrf_k", 60),
        )
        
        self.reranker = ResultReranker(
            api_key=api_key,
            api_base_url=self.config.get("api_base_url", "https://api.mistral.ai/v1"),
            model=self.config.get("reranker_model", "mistral-small-latest"),
            temperature=self.config.get("reranker_temperature", 0.1),
            max_tokens=self.config.get("reranker_max_tokens", 1024),
            timeout=self.config.get("reranker_timeout", 30),
            max_retries=self.config.get("reranker_max_retries", 3),
        )
        
        self.synthesizer = ResponseSynthesizer(
            api_key=api_key,
            api_base_url=self.config.get("api_base_url", "https://api.mistral.ai/v1"),
            model=self.config.get("synthesizer_model", "mistral-large-latest"),
            temperature=self.config.get("synthesizer_temperature", 0.4),
            max_tokens=self.config.get("synthesizer_max_tokens", 4096),
            timeout=self.config.get("synthesizer_timeout", 120),
            max_retries=self.config.get("synthesizer_max_retries", 3),
        )
        
        # Chemins
        self.wiki_dir = self.vault_path / "wiki"
        self.synthesis_dir = self.wiki_dir / "synthesis"
        self.log_file = self.wiki_dir / "log.md"
        
        self.wiki_dir.mkdir(exist_ok=True)
        self.synthesis_dir.mkdir(exist_ok=True)
        
        # Historique
        self.history: List[Dict[str, Any]] = []
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Charger la configuration."""
        default_config = {
            "api_base_url": "https://api.mistral.ai/v1",
            "timeout": 120,
            "max_retries": 3,
            "use_bm25": True,
            "use_embeddings": True,
            "bm25_k1": 1.5,
            "bm25_b": 0.75,
            "embedding_dimension": 1024,
            "bm25_top_k": 50,
            "embedding_top_k": 10,
            "rrf_k": 60,
            "reranker_model": "mistral-small-latest",
            "reranker_temperature": 0.1,
            "reranker_max_tokens": 1024,
            "reranker_timeout": 30,
            "reranker_max_retries": 3,
            "synthesizer_model": "mistral-large-latest",
            "synthesizer_temperature": 0.4,
            "synthesizer_max_tokens": 4096,
            "synthesizer_timeout": 120,
            "synthesizer_max_retries": 3,
        }
        
        # Charger depuis le fichier si spécifié
        if config_path:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                default_config.update(file_config.get("search_agent", {}))
        
        # Charger depuis le vault
        vault_config = self.vault_path / "configs" / "agents_config.json"
        if vault_config.exists():
            with open(vault_config, "r", encoding="utf-8") as f:
                file_config = json.load(f)
            agent_config = file_config.get("agents", {}).get("search_agent", {})
            default_config.update(agent_config.get("features", {}).get("retrieval", {}))
            default_config.update(agent_config.get("features", {}).get("synthesis", {}))
        
        return default_config
    
    def _log_operation(
        self,
        operation: str,
        query: str,
        results: List[Dict[str, Any]],
        answer: str,
    ) -> None:
        """Logger une opération dans log.md."""
        log_entry = f"""- [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{operation.upper()}] {query[:50]}
  - results: {len(results)}
  - answer_length: {len(answer)}
  - confidence: {self._calculate_confidence(results, answer):.2f}
  - status: success
"""
        
        if not self.log_file.exists():
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write("# Log des Opérations\n\n")
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
        
        logger.info(f"Opération loggée: {operation} - {query[:50]}")
    
    def _calculate_confidence(
        self,
        results: List[Dict[str, Any]],
        answer: str,
    ) -> float:
        """Calculer un score de confiance."""
        if not results:
            return 0.0
        
        # Score de base
        confidence = 0.5
        
        # Ajouter pour le nombre de résultats
        num_results = min(len(results), 5)
        confidence += num_results * 0.1
        
        # Ajouter pour les scores
        total_score = sum(
            result.get("combined_score", 0) or
            result.get("score", 0) or
            result.get("similarity", 0)
            for result in results
        )
        avg_score = total_score / len(results) if results else 0
        confidence += avg_score * 0.2
        
        # Ajouter pour les citations
        import re
        citations = re.findall(r'\[\[(.*?)\]\]', answer)
        confidence += min(len(citations) * 0.05, 0.2)
        
        # Clamper entre 0 et 1
        return min(max(confidence, 0.0), 1.0)
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        mode: str = "hybrid",
        use_reranker: bool = True,
        use_synthesizer: bool = True,
        save_answer: bool = True,
        format: str = "detailed",
        page_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Effectuer une recherche.
        
        Args:
            query: Requête de recherche.
            top_k: Nombre de résultats.
            mode: Mode de recherche (hybrid, bm25, embeddings, index).
            use_reranker: Utiliser le reclassement.
            use_synthesizer: Utiliser le synthétiseur.
            save_answer: Sauvegarder la réponse.
            format: Format de la réponse (simple, detailed).
            page_types: Filtrer par types de pages.
            tags: Filtrer par tags.
            
        Returns:
            Résultat de la recherche.
        """
        start_time = datetime.now()
        
        # Initialiser le rapport
        report: Dict[str, Any] = {
            "success": True,
            "start_time": start_time.isoformat(),
            "query": query,
            "mode": mode,
            "results": [],
            "answer": "",
            "sources": [],
            "citations": [],
            "confidence": 0.0,
            "duration_seconds": 0.0,
        }
        
        try:
            # Étape 1: Recherche dans le RAG
            logger.info(f"Recherche: {query[:50]} (mode: {mode})")
            
            if mode == "bm25":
                results = self.retriever.search_bm25(query, top_k, page_types, tags)
            elif mode == "embeddings":
                # Obtenir l'embedding de la requête
                query_embedding = await self.retriever.get_query_embedding(query)
                results = self.retriever.search_embeddings(query_embedding, top_k, 0, page_types, tags)
            elif mode == "index":
                results = self.retriever.search_index_only(query, top_k)
            else:  # hybrid
                results = await self.retriever.search_hybrid(query, top_k, page_types=page_types, tags=tags)
            
            report["retrieval_results"] = results
            report["results_count"] = len(results)
            
            logger.info(f"Résultats de la recherche: {len(results)} documents")
            
            # Étape 2: Reclassement (optionnel)
            if use_reranker and results:
                results = await self.reranker.rerank_results(query, results, top_k)
                report["reranked_results"] = results
            
            # Étape 3: Synthèse (optionnel)
            if use_synthesizer and results:
                synthesis_result = await self.synthesizer.synthesize(
                    query,
                    results,
                    include_citations=True,
                    include_sources=True,
                    format=format,
                )
                
                report.update(synthesis_result)
                
                # Sauvegarder la réponse si demandé
                if save_answer and synthesis_result.get("success", False):
                    saved_path = await self.synthesizer.save_response(
                        query,
                        synthesis_result["answer"],
                        self.vault_path,
                    )
                    report["saved_path"] = saved_path
            else:
                # Si pas de synthèse, formater les résultats manuellement
                report["answer"] = self._format_results_manually(query, results, format)
                report["sources"] = [r.get("doc_id", "") for r in results]
                report["citations"] = report["sources"]
            
            # Calculer la confiance
            report["confidence"] = self._calculate_confidence(results, report["answer"])
            
            # Logger l'opération
            self._log_operation("search", query, results, report["answer"])
            
            # Calculer la durée
            report["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            report["end_time"] = datetime.now().isoformat()
            
            # Ajouter à l'historique
            self.history.append(report)
            
            logger.info(f"Recherche terminée: {len(results)} résultats, confiance: {report['confidence']:.2f}")
            
            return report
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
            }
    
    def _format_results_manually(
        self,
        query: str,
        results: List[Dict[str, Any]],
        format: str,
    ) -> str:
        """Formater les résultats manuellement."""
        if not results:
            return "Aucun résultat trouvé pour cette requête."
        
        if format == "simple":
            # Format simple
            lines = [f"**Réponse à:** {query}"]
            lines.append("")
            
            for i, result in enumerate(results[:3]):  # Top 3
                doc_id = result.get("doc_id", f"doc_{i}")
                score = result.get("combined_score", 0) or result.get("score", 0)
                preview = result.get("text", "")[:200] + "..."
                
                lines.append(f"{i+1}. [[{doc_id}]] (Score: {score:.2f})")
                lines.append(f"   {preview}")
                lines.append("")
            
            return "\n".join(lines)
        else:
            # Format détaillé
            lines = [f"# Résultats pour: {query}"]
            lines.append("")
            lines.append(f"**Nombre de résultats:** {len(results)}")
            lines.append("")
            
            for i, result in enumerate(results):
                doc_id = result.get("doc_id", f"doc_{i}")
                score = result.get("combined_score", 0) or result.get("score", 0)
                preview = result.get("text", "")[:300] + "..."
                metadata = result.get("metadata", {})
                
                lines.append(f"## Résultat {i+1}: [[{doc_id}]]")
                lines.append(f"- **Score:** {score:.2f}")
                lines.append(f"- **Type:** {metadata.get('type', 'unknown')}")
                lines.append(f"- **Langue:** {metadata.get('language', 'unknown')}")
                lines.append("")
                lines.append(f"{preview}")
                lines.append("")
            
            return "\n".join(lines)
    
    async def query(
        self,
        query: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Méthode alias pour search (compatibilité OpenWebUI).
        """
        return await self.search(query, **kwargs)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Obtenir l'historique des recherches."""
        return self.history
    
    def clear_history(self) -> None:
        """Effacer l'historique."""
        self.history = []
    
    async def close(self) -> None:
        """Fermer les ressources."""
        await self.reranker.close()
        await self.synthesizer.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.run(self.close())


# Instance globale pour OpenWebUI
_search_agent: Optional[SearchAgent] = None


def get_search_agent(
    vault_path: Union[Path, str] = Path("~/vaults/knowledge_base").expanduser(),
    api_key: Optional[str] = None,
) -> SearchAgent:
    """Obtenir une instance globale de l'agent de recherche."""
    global _search_agent
    
    if _search_agent is None:
        _search_agent = SearchAgent(vault_path, api_key)
    
    return _search_agent


def reset_search_agent() -> None:
    """Réinitialiser l'instance globale."""
    global _search_agent
    _search_agent = None
