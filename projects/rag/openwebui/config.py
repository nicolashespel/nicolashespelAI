"""
Configuration pour OpenWebUI.

Ce module contient la configuration complète pour intégrer
les 4 agents avec OpenWebUI.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class OpenWebUIConfig:
    """
    Configuration pour OpenWebUI.
    
    Ce module génère la configuration nécessaire pour intégrer
    les 4 agents avec OpenWebUI.
    """
    
    def __init__(
        self,
        vault_path: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """
        Initialiser la configuration.
        
        Args:
            vault_path: Chemin du vault par défaut.
            api_key: Clé API Mistral.
        """
        self.vault_path = vault_path or os.getenv("WIKI_VAULT_PATH", "~/vaults/knowledge_base")
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY", "")
    
    def generate_agents_config(self) -> Dict[str, Any]:
        """
        Générer la configuration des agents pour OpenWebUI.
        
        Returns:
            Configuration complète des agents.
        """
        return {
            "agents": {
                "cleanup_agent": {
                    "name": "RAG Cleanup Agent",
                    "description": "Nettoie les documents avec Mistral OCR et prépare pour l'ingestion RAG",
                    "icon": "🧹",
                    "color": "#4CAF50",
                    "command": "clean",
                    "parameters": [
                        {
                            "name": "input",
                            "type": "string",
                            "required": True,
                            "description": "Chemin du fichier ou dossier à nettoyer",
                        },
                        {
                            "name": "output",
                            "type": "string",
                            "required": False,
                            "description": "Dossier de sortie (par défaut: cleaned/)",
                        },
                        {
                            "name": "mode",
                            "type": "string",
                            "required": False,
                            "default": "auto",
                            "enum": ["auto", "ocr_only", "cleanup_only", "both"],
                            "description": "Mode de traitement",
                        },
                        {
                            "name": "language",
                            "type": "string",
                            "required": False,
                            "default": "auto",
                            "description": "Langue du document",
                        },
                    ],
                    "examples": [
                        "clean raw/documents/article.pdf",
                        "clean raw/images/scan.jpg --mode ocr_only",
                        "clean raw/ --output cleaned_texts/",
                    ],
                },
                "ingestion_agent": {
                    "name": "RAG Ingestion Agent",
                    "description": "Intègre les documents nettoyés dans le système RAG avec Mistral Embed",
                    "icon": "📚",
                    "color": "#2196F3",
                    "command": "ingest",
                    "parameters": [
                        {
                            "name": "input",
                            "type": "string",
                            "required": True,
                            "description": "Chemin du fichier ou dossier à ingérer",
                        },
                        {
                            "name": "vault",
                            "type": "string",
                            "required": False,
                            "description": f"Chemin du vault (par défaut: {self.vault_path})",
                        },
                        {
                            "name": "mode",
                            "type": "string",
                            "required": False,
                            "default": "full",
                            "enum": ["full", "text_only", "metadata_only"],
                            "description": "Mode d'ingestion",
                        },
                        {
                            "name": "preprocess",
                            "type": "boolean",
                            "required": False,
                            "default": True,
                            "description": "Prétraiter avant ingestion",
                        },
                    ],
                    "examples": [
                        "ingest cleaned/article.txt",
                        f"ingest cleaned/ --vault {self.vault_path}",
                        "ingest cleaned/article.txt --mode text_only",
                    ],
                },
                "search_agent": {
                    "name": "RAG Search Agent",
                    "description": "Recherche optimisée dans le RAG avec Mistral Large et Embed",
                    "icon": "🔍",
                    "color": "#FF9800",
                    "command": "search",
                    "parameters": [
                        {
                            "name": "query",
                            "type": "string",
                            "required": True,
                            "description": "Requête de recherche",
                        },
                        {
                            "name": "vault",
                            "type": "string",
                            "required": False,
                            "description": f"Chemin du vault (par défaut: {self.vault_path})",
                        },
                        {
                            "name": "top_k",
                            "type": "integer",
                            "required": False,
                            "default": 5,
                            "min": 1,
                            "max": 20,
                            "description": "Nombre de résultats",
                        },
                        {
                            "name": "mode",
                            "type": "string",
                            "required": False,
                            "default": "hybrid",
                            "enum": ["hybrid", "bm25", "embeddings", "index"],
                            "description": "Mode de recherche",
                        },
                        {
                            "name": "save",
                            "type": "boolean",
                            "required": False,
                            "default": True,
                            "description": "Sauvegarder la réponse",
                        },
                    ],
                    "examples": [
                        "search \"Qu'est-ce que l'interprétabilité des LLM ?\"",
                        "search \"mécanisme d'attention\" --top_k 10",
                        "search \"comparaison transformers\" --mode hybrid --save false",
                    ],
                },
                "health_agent": {
                    "name": "RAG Health Agent",
                    "description": "Vérifie la santé du système RAG et signale les problèmes",
                    "icon": "🏥",
                    "color": "#F44336",
                    "command": "health",
                    "parameters": [
                        {
                            "name": "vault",
                            "type": "string",
                            "required": False,
                            "description": f"Chemin du vault à analyser (par défaut: {self.vault_path})",
                        },
                        {
                            "name": "checks",
                            "type": "string",
                            "required": False,
                            "default": "all",
                            "enum": ["all", "validation", "analysis", "statistics", "moderation"],
                            "description": "Types de vérifications",
                        },
                        {
                            "name": "fix",
                            "type": "boolean",
                            "required": False,
                            "default": False,
                            "description": "Corriger automatiquement les problèmes",
                        },
                        {
                            "name": "format",
                            "type": "string",
                            "required": False,
                            "default": "full",
                            "enum": ["full", "summary", "json"],
                            "description": "Format du rapport",
                        },
                    ],
                    "examples": [
                        "health",
                        f"health --vault {self.vault_path}",
                        "health --checks validation --fix true",
                        "health --format summary",
                    ],
                },
            },
            "workflows": {
                "full_pipeline": {
                    "name": "Pipeline Complet",
                    "description": "Nettoyage → Ingestion → Recherche en une seule commande",
                    "steps": [
                        {"agent": "cleanup_agent", "command": "clean {input}"},
                        {"agent": "ingestion_agent", "command": "ingest cleaned/{input}"},
                        {"agent": "search_agent", "command": "search \"{query}\""},
                    ],
                    "command": "process",
                },
                "quick_search": {
                    "name": "Recherche Rapide",
                    "description": "Recherche directe sans ingestion",
                    "steps": [
                        {"agent": "search_agent", "command": "search \"{query}\" --mode index"},
                    ],
                    "command": "quick",
                },
            },
            "global": {
                "api_key": self.api_key[:8] + "..." if self.api_key else "MISTRAL_API_KEY",
                "vault_path": self.vault_path,
                "timeout": 120,
                "max_retries": 3,
            },
        }
    
    def generate_openwebui_config(self) -> Dict[str, Any]:
        """
        Générer la configuration complète pour OpenWebUI.
        
        Returns:
            Configuration complète pour OpenWebUI.
        """
        config = self.generate_agents_config()
        
        # Ajouter des informations spécifiques à OpenWebUI
        config["openwebui"] = {
            "version": "1.0.0",
            "description": "Configuration RAG Wiki pour OpenWebUI",
            "setup_instructions": [
                "1. Assurez-vous que Python 3.12+ est installé",
                "2. Installez les dépendances: pip install -r requirements.txt",
                "3. Définissez la variable MISTRAL_API_KEY avec votre clé API",
                "4. Initialisez un vault: python scripts/simple_init.py",
                "5. Ajoutez les commandes personnalisées dans OpenWebUI",
                "6. Utilisez les commandes /clean, /ingest, /search, /health",
            ],
            "environment_variables": {
                "MISTRAL_API_KEY": "Votre clé API Mistral",
                "WIKI_VAULT_PATH": self.vault_path,
            },
        }
        
        return config
    
    def save_config(self, output_path: Union[Path, str]) -> None:
        """
        Sauvegarder la configuration dans un fichier.
        
        Args:
            output_path: Chemin du fichier de sortie.
        """
        output_path = Path(output_path)
        config = self.generate_openwebui_config()
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"Configuration sauvegardée: {output_path}")
    
    def generate_agent_script(self, agent_name: str) -> str:
        """
        Générer un script pour un agent spécifique.
        
        Args:
            agent_name: Nom de l'agent (cleanup, ingestion, search, health).
            
        Returns:
            Script Python pour l'agent.
        """
        agent_configs = {
            "cleanup": {
                "module": "agents.cleanup_agent",
                "class": "CleanupAgent",
                "command": "clean",
            },
            "ingestion": {
                "module": "agents.ingestion_agent",
                "class": "IngestionAgent",
                "command": "ingest",
            },
            "search": {
                "module": "agents.search_agent",
                "class": "SearchAgent",
                "command": "search",
            },
            "health": {
                "module": "agents.health_agent",
                "class": "HealthAgent",
                "command": "health",
            },
        }
        
        if agent_name not in agent_configs:
            raise ValueError(f"Agent inconnu: {agent_name}")
        
        config = agent_configs[agent_name]
        
        script = f"""#!/usr/bin/env python3
\"\"\"
Script pour l'agent {config['class']} - OpenWebUI
\"\"\"

import asyncio
import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from {config['module']} import {config['class']}


async def main():
    # Récupérer les arguments
    args = sys.argv[1:]
    
    if not args:
        print("Usage: python {config['command']}_agent.py <arguments>")
        print(f"Command: /{config['command']} <arguments>")
        return
    
    # Initialiser l'agent
    vault_path = os.getenv("WIKI_VAULT_PATH", "~/vaults/knowledge_base")
    api_key = os.getenv("MISTRAL_API_KEY", None)
    
    agent = {config['class']}(vault_path, api_key)
    
    try:
        # Parser les arguments
        input_arg = args[0] if args else ""
        kwargs = {}
        
        for arg in args[1:]:
            if "=" in arg:
                key, value = arg.split("=", 1)
                kwargs[key] = value
        
        # Exécuter la commande
        if config['command'] == 'clean':
            result = await agent.cleanup(input_arg, **kwargs)
        elif config['command'] == 'ingest':
            result = await agent.ingest(input_arg, **kwargs)
        elif config['command'] == 'search':
            result = await agent.search(input_arg, **kwargs)
        elif config['command'] == 'health':
            result = await agent.health(input_arg, **kwargs)
        else:
            result = {{"error": f"Commande inconnue: {config['command']}"}}
        
        # Afficher le résultat
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
"""
        
        return script
    
    def generate_cli_wrapper(self) -> str:
        """
        Générer un wrapper CLI pour OpenWebUI.
        
        Returns:
            Script Python pour le wrapper CLI.
        """
        return """#!/usr/bin/env python3
\"\"\"
Wrapper CLI pour OpenWebUI - RAG Wiki System

Ce script permet d'exécuter les 4 agents directement depuis OpenWebUI
ou depuis la ligne de commande.
\"\"\"

import asyncio
import json
import sys
import os
from pathlib import Path

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.cleanup_agent import CleanupAgent
from agents.ingestion_agent import IngestionAgent
from agents.search_agent import SearchAgent
from agents.health_agent import HealthAgent


# Instances globales
_agents = {}


def get_agent(agent_name: str, vault_path: str = None, api_key: str = None):
    \"\"\"Obtenir une instance d'agent.\"\"\"
    vault_path = vault_path or os.getenv("WIKI_VAULT_PATH", "~/vaults/knowledge_base")
    api_key = api_key or os.getenv("MISTRAL_API_KEY", None)
    
    if agent_name not in _agents:
        if agent_name == "cleanup":
            _agents[agent_name] = CleanupAgent(vault_path, api_key)
        elif agent_name == "ingestion":
            _agents[agent_name] = IngestionAgent(vault_path, api_key)
        elif agent_name == "search":
            _agents[agent_name] = SearchAgent(vault_path, api_key)
        elif agent_name == "health":
            _agents[agent_name] = HealthAgent(vault_path, api_key)
    
    return _agents[agent_name]


async def process_command(command: str, args: list) -> dict:
    \"\"\"Traiter une commande.\"\"\"
    # Parser la commande
    parts = command.split("-")
    if len(parts) < 2:
        return {"error": f"Commande invalide: {command}. Format: /<agent>-<action>"}
    
    agent_name = parts[1]
    
    # Vérifier que l'agent existe
    if agent_name not in ["clean", "ingest", "search", "health"]:
        return {"error": f"Agent inconnu: {agent_name}"}
    
    # Mapper les noms d'agents
    agent_map = {
        "clean": "cleanup",
        "ingest": "ingestion",
        "search": "search",
        "health": "health",
    }
    
    agent_type = agent_map[agent_name]
    
    # Obtenir l'agent
    vault_path = os.getenv("WIKI_VAULT_PATH", "~/vaults/knowledge_base")
    api_key = os.getenv("MISTRAL_API_KEY", None)
    agent = get_agent(agent_type, vault_path, api_key)
    
    # Parser les arguments
    kwargs = {}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            kwargs[key] = value
    
    # Exécuter la commande
    try:
        if agent_type == "cleanup":
            if not args:
                return {"error": "Chemin requis pour clean"}
            result = await agent.cleanup(args[0], **kwargs)
        elif agent_type == "ingestion":
            if not args:
                return {"error": "Chemin requis pour ingest"}
            result = await agent.ingest(args[0], **kwargs)
        elif agent_type == "search":
            if not args:
                return {"error": "Requête requise pour search"}
            result = await agent.search(" ".join(args), **kwargs)
        elif agent_type == "health":
            result = await agent.health(args[0] if args else None, **kwargs)
        else:
            result = {"error": f"Agent inconnu: {agent_type}"}
        
        return result
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        await agent.close()


async def main():
    \"\"\"Point d'entrée principal.\"\"\"
    # Récupérer la commande et les arguments
    all_args = sys.argv[1:]
    
    if not all_args:
        print("Usage: python openwebui_cli.py /<command> <args>")
        print("\\nCommandes disponibles:")
        print("  /clean <input> - Nettoyer un fichier ou dossier")
        print("  /ingest <input> - Ingest un fichier ou dossier")
        print("  /search <query> - Rechercher dans le RAG")
        print("  /health - Vérifier la santé du RAG")
        return
    
    # La première partie est la commande
    command = all_args[0]
    args = all_args[1:]
    
    # Traiter la commande
    result = await process_command(command, args)
    
    # Afficher le résultat
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
"""
