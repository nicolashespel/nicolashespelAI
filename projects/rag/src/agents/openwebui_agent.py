"""
Agent Open WebUI pour le système RAG Wiki.

Cet agent permet d'intégrer le système RAG Wiki avec Open WebUI via des commandes shell.
Il est également compatible avec d'autres outils comme Claude Desktop et ChatGPT Desktop.
"""

import asyncio
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .preprocessing_agent import PreprocessingAgent
from .wiki_ingestor import WikiIngestorAgent
from .wiki_librarian import WikiLibrarianAgent
from .wiki_linter import WikiLinterAgent
from ..core.config import WikiConfig
from ..storage import VaultManager
from ..utils.path_utils import get_file_type


class OpenWebUIAgent:
    """
    Agent pour intégrer le système RAG Wiki avec Open WebUI.
    
    Cet agent expose des commandes au format compatible avec Open WebUI
    et d'autres outils comme Claude Desktop et ChatGPT Desktop.
    
    Commandes disponibles :
    - /wiki-init : Initialiser un vault
    - /wiki-ingest <path> : Ingest une source
    - /wiki-query <question> : Poser une question
    - /wiki-lint : Lancer le linting
    - /wiki-log : Afficher le log
    - /wiki-status : Statut du système
    - /wiki-preprocess <path> : Prétraiter un fichier
    - /wiki-batch <path1> <path2> ... : Ingest multiple sources
    """
    
    def __init__(
        self,
        vault_path: Union[Path, str],
        config: Optional[WikiConfig] = None,
    ) -> None:
        """
        Initialiser l'agent Open WebUI.
        
        Args:
            vault_path: Chemin du vault.
            config: Configuration du wiki.
        """
        self.vault_path = Path(vault_path) if isinstance(vault_path, str) else vault_path
        self.config = config or WikiConfig(vault_path=self.vault_path)
        
        # Initialiser les agents
        self.vault_manager = VaultManager(self.vault_path)
        self.preprocessing_agent = PreprocessingAgent(self.vault_path, self.config)
        self.wiki_ingestor = WikiIngestorAgent(self.vault_path, self.config)
        self.wiki_librarian = WikiLibrarianAgent(self.vault_path, self.config)
        self.wiki_linter = WikiLinterAgent(self.vault_path, self.config)
        
        # Charger la configuration Mistral
        self.mistral_config = self._load_mistral_config()
        
        # Historique des commandes
        self.command_history: List[Dict[str, Any]] = []
    
    def _load_mistral_config(self) -> Dict[str, Any]:
        """Charger la configuration Mistral."""
        config_path = self.vault_path / "configs" / "mistral_config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return {
                "agents": {
                    "OpenWebUIAgent": {
                        "llm_model": "mistral-large-latest",
                        "temperature": 0.3,
                        "max_tokens": 8192,
                    }
                }
            }
    
    def _format_response(
        self,
        success: bool,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        citations: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Formater une réponse au format compatible Open WebUI.
        
        Args:
            success: Si l'opération a réussi.
            message: Message principal.
            data: Données supplémentaires.
            citations: Liste des citations.
            warnings: Avertissements.
            errors: Erreurs.
            
        Returns:
            Réponse formatée.
        """
        response = {
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        
        if data:
            response["data"] = data
        if citations:
            response["citations"] = citations
        if warnings:
            response["warnings"] = warnings
        if errors:
            response["errors"] = errors
        
        return response
    
    def _parse_command(self, command: str) -> Tuple[str, List[str], Dict[str, Any]]:
        """
        Parser une commande.
        
        Args:
            command: Commande à parser.
            
        Returns:
            Tuple avec (nom_commande, arguments, options).
        """
        # Nettoyer la commande
        command = command.strip()
        
        # Vérifier si c'est une commande wiki
        if not command.startswith("/wiki-"):
            return "", [], {}
        
        # Extraire le nom de la commande
        parts = command.split()
        cmd_name = parts[0][1:]  # Supprimer le /
        args = parts[1:] if len(parts) > 1 else []
        
        # Parser les options
        options: Dict[str, Any] = {}
        for arg in args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                options[key] = value
        
        return cmd_name, args, options
    
    async def handle_command(
        self,
        command: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Exécuter une commande.
        
        Args:
            command: Commande à exécuter.
            context: Contexte supplémentaire.
            
        Returns:
            Réponse formatée.
        """
        start_time = datetime.now()
        
        # Parser la commande
        cmd_name, args, options = self._parse_command(command)
        
        if not cmd_name:
            return self._format_response(
                success=False,
                message="Commande invalide. Les commandes doivent commencer par '/wiki-'",
                errors=["Commande non reconnue"]
            )
        
        # Enregistrer dans l'historique
        command_record = {
            "command": cmd_name,
            "args": args,
            "options": options,
            "timestamp": start_time.isoformat(),
        }
        self.command_history.append(command_record)
        
        try:
            # Exécuter la commande
            if cmd_name == "wiki-init":
                return await self._handle_init(args, options)
            elif cmd_name == "wiki-ingest":
                return await self._handle_ingest(args, options)
            elif cmd_name == "wiki-query":
                return await self._handle_query(args, options)
            elif cmd_name == "wiki-lint":
                return await self._handle_lint(args, options)
            elif cmd_name == "wiki-log":
                return await self._handle_log(args, options)
            elif cmd_name == "wiki-status":
                return await self._handle_status(args, options)
            elif cmd_name == "wiki-preprocess":
                return await self._handle_preprocess(args, options)
            elif cmd_name == "wiki-batch":
                return await self._handle_batch(args, options)
            else:
                return self._format_response(
                    success=False,
                    message=f"Commande inconnue: {cmd_name}",
                    errors=[f"Commande '{cmd_name}' non implémentée"]
                )
        except Exception as e:
            return self._format_response(
                success=False,
                message=f"Erreur lors de l'exécution de {cmd_name}",
                errors=[str(e)]
            )
        finally:
            # Calculer la durée
            duration = (datetime.now() - start_time).total_seconds()
            command_record["duration_seconds"] = duration
    
    async def _handle_init(
        self,
        args: List[str],
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Gérer la commande /wiki-init."""
        # Créer le vault si nécessaire
        if not self.vault_path.exists():
            self.vault_path.mkdir(parents=True, exist_ok=True)
            
            # Créer les dossiers de base
            (self.vault_path / "raw").mkdir(exist_ok=True)
            (self.vault_path / "wiki").mkdir(exist_ok=True)
            (self.vault_path / "configs").mkdir(exist_ok=True)
            
            # Créer les sous-dossiers wiki
            (self.vault_path / "wiki" / "entities").mkdir(exist_ok=True)
            (self.vault_path / "wiki" / "concepts").mkdir(exist_ok=True)
            (self.vault_path / "wiki" / "sources").mkdir(exist_ok=True)
            (self.vault_path / "wiki" / "comparisons").mkdir(exist_ok=True)
            (self.vault_path / "wiki" / "synthesis").mkdir(exist_ok=True)
            
            # Copier la configuration Mistral
            config_src = self.vault_path.parent / "configs" / "mistral_config.json"
            config_dst = self.vault_path / "configs" / "mistral_config.json"
            if config_src.exists():
                with open(config_src, "r", encoding="utf-8") as src_f:
                    with open(config_dst, "w", encoding="utf-8") as dst_f:
                        dst_f.write(src_f.read())
            
            return self._format_response(
                success=True,
                message=f"Vault initialisé: {self.vault_path}",
                data={"vault_path": str(self.vault_path)}
            )
        else:
            return self._format_response(
                success=True,
                message=f"Vault déjà existant: {self.vault_path}",
                data={"vault_path": str(self.vault_path)},
                warnings=["Le vault existe déjà, aucune modification effectuée"]
            )
    
    async def _handle_ingest(
        self,
        args: List[str],
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Gérer la commande /wiki-ingest."""
        if not args:
            return self._format_response(
                success=False,
                message="Chemin de la source requis",
                errors=["Aucun chemin spécifié"]
            )
        
        source_path = Path(args[0])
        
        # Vérifier si le fichier existe
        if not source_path.exists():
            return self._format_response(
                success=False,
                message=f"Fichier non trouvé: {source_path}",
                errors=[f"Fichier introuvable: {source_path}"]
            )
        
        # Vérifier si c'est un chemin absolu ou relatif
        if not source_path.is_absolute():
            # Essayer de résoudre par rapport au vault
            source_path = self.vault_path / source_path
        
        # Exécuter l'ingestion
        preprocess = options.get("preprocess", "true").lower() != "false"
        ask_confirmation = options.get("confirm", "true").lower() != "false"
        
        report = await self.wiki_ingestor.execute(
            source_path=source_path,
            preprocess=preprocess,
            ask_for_confirmation=ask_confirmation,
        )
        
        if report["success"]:
            return self._format_response(
                success=True,
                message=f"Source ingérée: {source_path.name}",
                data={
                    "source_path": str(source_path),
                    "preprocessed": report.get("preprocessed", False),
                    "summary_page": report.get("ingestion_report", {}).get("summary_page", ""),
                    "updated_pages": report.get("ingestion_report", {}).get("updated_pages", []),
                    "cross_references": report.get("ingestion_report", {}).get("cross_references", []),
                }
            )
        else:
            return self._format_response(
                success=False,
                message=f"Échec de l'ingestion: {source_path.name}",
                errors=[report.get("error", "Erreur inconnue")]
            )
    
    async def _handle_query(
        self,
        args: List[str],
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Gérer la commande /wiki-query."""
        if not args:
            return self._format_response(
                success=False,
                message="Question requise",
                errors=["Aucune question spécifiée"]
            )
        
        query = " ".join(args)
        
        # Exécuter la requête
        result = await self.wiki_librarian.execute(
            query=query,
            top_k=options.get("top_k", 5),
            save_answer=options.get("save", "true").lower() != "false",
        )
        
        if result["success"]:
            return self._format_response(
                success=True,
                message=result["answer"],
                data={
                    "query": query,
                    "sources": result.get("sources", []),
                    "confidence": result.get("confidence", 0.0),
                    "answer_length": len(result["answer"]),
                },
                citations=result.get("citations", [])
            )
        else:
            return self._format_response(
                success=False,
                message=f"Échec de la requête: {query[:50]}...",
                errors=[result.get("error", "Erreur inconnue")]
            )
    
    async def _handle_lint(
        self,
        args: List[str],
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Gérer la commande /wiki-lint."""
        # Exécuter le linting
        report = await self.wiki_linter.execute(
            checks=options.get("checks", "all"),
            auto_fix=options.get("fix", "false").lower() == "true",
        )
        
        return self._format_response(
            success=report["success"],
            message=report["message"],
            data={
                "issues_found": report.get("issues_found", 0),
                "issues_fixed": report.get("issues_fixed", 0),
                "warnings": report.get("warnings", []),
                "details": report.get("details", {}),
            },
            warnings=report.get("warnings", []),
            errors=report.get("errors", [])
        )
    
    async def _handle_log(
        self,
        args: List[str],
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Gérer la commande /wiki-log."""
        # Lire le log
        log_path = self.vault_path / "wiki" / "log.md"
        
        if not log_path.exists():
            return self._format_response(
                success=True,
                message="Aucun log trouvé",
                warnings=["Le fichier log.md n'existe pas encore"]
            )
        
        with open(log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
        
        # Limiter la taille si nécessaire
        max_lines = options.get("lines", 100)
        lines = log_content.split('\n')
        if len(lines) > max_lines:
            log_content = '\n'.join(lines[-max_lines:])
        
        return self._format_response(
            success=True,
            message="Log du vault",
            data={
                "log": log_content,
                "total_lines": len(lines),
                "showing_lines": len(log_content.split('\n'))
            }
        )
    
    async def _handle_status(
        self,
        args: List[str],
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Gérer la commande /wiki-status."""
        # Récupérer les statistiques
        stats = {
            "vault_path": str(self.vault_path),
            "raw_files": len(list((self.vault_path / "raw").glob("**/*"))) if (self.vault_path / "raw").exists() else 0,
            "wiki_pages": len(list((self.vault_path / "wiki").glob("**/*.md"))) if (self.vault_path / "wiki").exists() else 0,
            "entities": len(list((self.vault_path / "wiki" / "entities").glob("*.md"))) if (self.vault_path / "wiki" / "entities").exists() else 0,
            "concepts": len(list((self.vault_path / "wiki" / "concepts").glob("*.md"))) if (self.vault_path / "wiki" / "concepts").exists() else 0,
            "sources": len(list((self.vault_path / "wiki" / "sources").glob("*.md"))) if (self.vault_path / "wiki" / "sources").exists() else 0,
            "synthesis": len(list((self.vault_path / "wiki" / "synthesis").glob("*.md"))) if (self.vault_path / "wiki" / "synthesis").exists() else 0,
            "config": self._get_config_summary(),
        }
        
        return self._format_response(
            success=True,
            message="Statut du système RAG Wiki",
            data=stats
        )
    
    async def _handle_preprocess(
        self,
        args: List[str],
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Gérer la commande /wiki-preprocess."""
        if not args:
            return self._format_response(
                success=False,
                message="Chemin du fichier requis",
                errors=["Aucun chemin spécifié"]
            )
        
        input_path = Path(args[0])
        
        # Vérifier si le fichier existe
        if not input_path.exists():
            return self._format_response(
                success=False,
                message=f"Fichier non trouvé: {input_path}",
                errors=[f"Fichier introuvable: {input_path}"]
            )
        
        # Vérifier si c'est un chemin absolu ou relatif
        if not input_path.is_absolute():
            input_path = self.vault_path / input_path
        
        # Exécuter le prétraitement
        ask_confirmation = options.get("confirm", "true").lower() != "false"
        success, output_path, report = await self.preprocessing_agent.preprocess(
            input_path=input_path,
            ask_for_confirmation=ask_confirmation,
        )
        
        if success:
            return self._format_response(
                success=True,
                message=f"Fichier prétraité: {input_path.name}",
                data={
                    "input_path": str(input_path),
                    "output_path": str(output_path),
                    "operations": report.get("operations", []),
                    "stats": report.get("stats", {}),
                    "warnings": report.get("warnings", []),
                },
                warnings=report.get("warnings", [])
            )
        else:
            return self._format_response(
                success=False,
                message=f"Échec du prétraitement: {input_path.name}",
                errors=report.get("errors", ["Erreur inconnue"])
            )
    
    async def _handle_batch(
        self,
        args: List[str],
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Gérer la commande /wiki-batch."""
        if not args:
            return self._format_response(
                success=False,
                message="Au moins un chemin requis",
                errors=["Aucun chemin spécifié"]
            )
        
        # Résoudre les chemins
        source_paths = []
        for arg in args:
            path = Path(arg)
            if not path.is_absolute():
                path = self.vault_path / path
            if path.exists():
                source_paths.append(path)
        
        if not source_paths:
            return self._format_response(
                success=False,
                message="Aucun fichier valide trouvé",
                errors=["Aucun fichier valide spécifié"]
            )
        
        # Exécuter l'ingestion en batch
        preprocess = options.get("preprocess", "true").lower() != "false"
        report = await self.wiki_ingestor.ingest_batch(
            source_paths=source_paths,
            preprocess=preprocess,
        )
        
        return self._format_response(
            success=True,
            message=f"Traitement en batch terminé: {len(source_paths)} fichiers",
            data={
                "total_sources": report.get("total_sources", 0),
                "successful": report.get("successful", 0),
                "failed": report.get("failed", 0),
                "sources": report.get("sources", {}),
            },
            warnings=[f"Échec pour {report.get('failed', 0)} fichiers"] if report.get("failed", 0) > 0 else []
        )
    
    def _get_config_summary(self) -> Dict[str, Any]:
        """Résumé de la configuration."""
        return {
            "vault_path": str(self.vault_path),
            "mistral_config": {
                "llm": self.mistral_config.get("llm", {}).get("default", {}).get("model", "unknown"),
                "embeddings": self.mistral_config.get("embeddings", {}).get("model", "unknown"),
            },
            "agents": list(self.mistral_config.get("agents", {}).keys()),
        }
    
    def get_command_help(self) -> Dict[str, Any]:
        """Retourner l'aide pour toutes les commandes."""
        commands = {
            "/wiki-init": {
                "description": "Initialiser un vault RAG Wiki",
                "usage": "/wiki-init",
                "options": [],
                "example": "/wiki-init"
            },
            "/wiki-ingest": {
                "description": "Ingérer une source dans le vault",
                "usage": "/wiki-ingest <chemin>",
                "options": [
                    {"name": "preprocess", "description": "Prétraiter avant ingestion (true/false)", "default": "true"},
                    {"name": "confirm", "description": "Demander confirmation pour les suppressions (true/false)", "default": "true"}
                ],
                "example": "/wiki-ingest raw/papers/article.pdf"
            },
            "/wiki-query": {
                "description": "Poser une question au vault",
                "usage": "/wiki-query <question>",
                "options": [
                    {"name": "top_k", "description": "Nombre de résultats à retourner", "default": "5"},
                    {"name": "save", "description": "Sauvegarder la réponse (true/false)", "default": "true"}
                ],
                "example": "/wiki-query Qu'est-ce que l'interprétabilité des LLM ?"
            },
            "/wiki-lint": {
                "description": "Lancer le linting du vault",
                "usage": "/wiki-lint",
                "options": [
                    {"name": "checks", "description": "Type de vérifications (all/mechanical/semantic/health)", "default": "all"},
                    {"name": "fix", "description": "Corriger automatiquement (true/false)", "default": "false"}
                ],
                "example": "/wiki-lint checks=all fix=true"
            },
            "/wiki-log": {
                "description": "Afficher le log du vault",
                "usage": "/wiki-log",
                "options": [
                    {"name": "lines", "description": "Nombre de lignes à afficher", "default": "100"}
                ],
                "example": "/wiki-log lines=50"
            },
            "/wiki-status": {
                "description": "Afficher le statut du système",
                "usage": "/wiki-status",
                "options": [],
                "example": "/wiki-status"
            },
            "/wiki-preprocess": {
                "description": "Prétraiter un fichier avant ingestion",
                "usage": "/wiki-preprocess <chemin>",
                "options": [
                    {"name": "confirm", "description": "Demander confirmation pour les suppressions (true/false)", "default": "true"}
                ],
                "example": "/wiki-preprocess raw/documents/report.pdf"
            },
            "/wiki-batch": {
                "description": "Ingérer plusieurs sources en batch",
                "usage": "/wiki-batch <chemin1> <chemin2> ...",
                "options": [
                    {"name": "preprocess", "description": "Prétraiter avant ingestion (true/false)", "default": "true"}
                ],
                "example": "/wiki-batch raw/papers/paper1.pdf raw/papers/paper2.pdf"
            }
        }
        
        return {
            "commands": commands,
            "total_commands": len(commands),
            "description": "Aide pour les commandes RAG Wiki"
        }
    
    def close(self) -> None:
        """Fermer les ressources."""
        self.wiki_ingestor.close()
        self.wiki_librarian.close()
        self.wiki_linter.close()
        self.preprocessing_agent.close()
        self.vault_manager.close()
    
    def run_cli(self) -> None:
        """Exécuter en mode CLI pour Open WebUI."""
        print("Agent Open WebUI pour RAG Wiki - Mode CLI")
        print("Tapez une commande (ex: /wiki-init, /wiki-query 'ma question') ou 'exit' pour quitter")
        print("Tapez '/wiki-help' pour l'aide")
        
        while True:
            try:
                command = input("> ")
                
                if command.lower() in ['exit', 'quit', 'q']:
                    print("Au revoir !")
                    break
                
                if command.lower() in ['/wiki-help', 'help', '?']:
                    help_data = self.get_command_help()
                    print("\nCommandes disponibles:")
                    for cmd, info in help_data["commands"].items():
                        print(f"\n{cmd}:")
                        print(f"  Description: {info['description']}")
                        print(f"  Usage: {info['usage']}")
                        if info.get("example"):
                            print(f"  Example: {info['example']}")
                    continue
                
                # Exécuter la commande
                result = asyncio.run(self.handle_command(command))
                
                # Afficher le résultat
                if result["success"]:
                    print(f"✓ {result['message']}")
                else:
                    print(f"✗ {result['message']}")
                
                # Afficher les données supplémentaires
                if result.get("data"):
                    print(f"  Données: {json.dumps(result['data'], indent=2, ensure_ascii=False)}")
                
                # Afficher les citations
                if result.get("citations"):
                    print(f"  Citations: {', '.join(result['citations'])}")
                
                # Afficher les avertissements
                if result.get("warnings"):
                    for warning in result["warnings"]:
                        print(f"  ⚠ {warning}")
                
                # Afficher les erreurs
                if result.get("errors"):
                    for error in result["errors"]:
                        print(f"  ✗ {error}")
                
            except KeyboardInterrupt:
                print("\nAu revoir !")
                break
            except Exception as e:
                print(f"Erreur: {e}")


def main():
    """Point d'entrée pour l'exécution CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Open WebUI pour RAG Wiki")
    parser.add_argument("--vault", type=str, default="~/vaults/research", help="Chemin du vault")
    parser.add_argument("--command", type=str, help="Commande à exécuter")
    parser.add_argument("--interactive", action="store_true", help="Mode interactif")
    
    args = parser.parse_args()
    
    # Initialiser l'agent
    vault_path = Path(args.vault).expanduser()
    agent = OpenWebUIAgent(vault_path)
    
    try:
        if args.command:
            # Exécuter une commande unique
            result = asyncio.run(agent.handle_command(args.command))
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.interactive:
            # Mode interactif
            agent.run_cli()
        else:
            # Afficher l'aide
            help_data = agent.get_command_help()
            print(json.dumps(help_data, indent=2, ensure_ascii=False))
    finally:
        agent.close()


if __name__ == "__main__":
    main()
