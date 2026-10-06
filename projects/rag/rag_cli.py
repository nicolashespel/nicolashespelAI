#!/usr/bin/env python3
"""
Interface CLI simplifiée pour le système RAG Wiki.

Ce script fournit une interface unifiée pour utiliser le système RAG Wiki
avec OpenWebUI, Claude Desktop, ou directement en ligne de commande.

Utilisation:
    python rag_cli.py /wiki-init
    python rag_cli.py /wiki-ingest chemin/vers/fichier.pdf
    python rag_cli.py /wiki-query "Qu'est-ce que l'IA ?"
    python rag_cli.py /wiki-lint
    python rag_cli.py /wiki-status
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ajouter le chemin src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.openwebui_agent import OpenWebUIAgent
from core.config import WikiConfig


class RAGCLI:
    """Interface CLI simplifiée pour le système RAG Wiki."""
    
    def __init__(
        self,
        vault_path: Optional[str] = None,
        config_path: Optional[str] = None,
    ) -> None:
        """
        Initialiser l'interface CLI.
        
        Args:
            vault_path: Chemin du vault. Par défaut: ~/vaults/knowledge_base
            config_path: Chemin du fichier de configuration. Par défaut: configs/mistral_config.json
        """
        # Déterminer le chemin du vault
        if vault_path:
            self.vault_path = Path(vault_path).expanduser()
        else:
            # Vérifier si un vault existe déjà
            default_vault = Path("~/vaults/knowledge_base").expanduser()
            if default_vault.exists():
                self.vault_path = default_vault
            else:
                self.vault_path = Path.cwd() / "vault"
        
        # Charger la configuration
        self.config = self._load_config(config_path)
        
        # Initialiser l'agent OpenWebUI
        self.agent = OpenWebUIAgent(
            vault_path=self.vault_path,
            config=self.config,
        )
    
    def _load_config(self, config_path: Optional[str] = None) -> WikiConfig:
        """Charger la configuration."""
        if config_path:
            config_file = Path(config_path).expanduser()
            if config_file.exists():
                return WikiConfig.load_from_file(config_file)
        
        # Vérifier les chemins par défaut
        default_configs = [
            Path(__file__).parent / "configs" / "mistral_config.json",
            Path(__file__).parent / "configs" / "openwebui_config.json",
            self.vault_path / "configs" / "mistral_config.json",
        ]
        
        for config_file in default_configs:
            if config_file.exists():
                return WikiConfig.load_from_file(config_file)
        
        # Retourner la configuration par défaut
        return WikiConfig(
            vault_path=self.vault_path,
            llm_model="mistral-large-latest",
            embedding_model="mistral-embed",
        )
    
    async def run_command(self, command: str) -> Dict[str, Any]:
        """Exécuter une commande."""
        return await self.agent.handle_command(command)
    
    def print_result(self, result: Dict[str, Any]) -> None:
        """Afficher le résultat d'une commande."""
        if result.get("success", False):
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
        
        # Afficher les données supplémentaires
        if result.get("data"):
            data = result["data"]
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        print(f"  {key}: {json.dumps(value, indent=2, ensure_ascii=False)}")
                    else:
                        print(f"  {key}: {value}")
            else:
                print(f"  Données: {data}")
        
        # Afficher les citations
        if result.get("citations"):
            print(f"  Citations: {', '.join(result['citations'])}")
        
        # Afficher les avertissements
        if result.get("warnings"):
            for warning in result["warnings"]:
                print(f"  ⚠️  {warning}")
        
        # Afficher les erreurs
        if result.get("errors"):
            for error in result["errors"]:
                print(f"  ❌ {error}")
    
    def print_help(self) -> None:
        """Afficher l'aide."""
        help_data = self.agent.get_command_help()
        
        print("\n" + "=" * 60)
        print("RAG Wiki - Interface CLI Simplifiée")
        print("=" * 60)
        print("\nCommandes disponibles:")
        print()
        
        for cmd, info in help_data["commands"].items():
            print(f"  {cmd}")
            print(f"    Description: {info['description']}")
            print(f"    Usage: {info['usage']}")
            if info.get("example"):
                print(f"    Exemple: {info['example']}")
            print()
        
        print("=" * 60)
        print("Configuration actuelle:")
        print(f"  Vault: {self.vault_path}")
        print(f"  Modèle LLM: mistral-large-latest")
        print(f"  Modèle Embeddings: mistral-embed")
        print("=" * 60)
    
    async def run_interactive(self) -> None:
        """Mode interactif."""
        print("\n" + "=" * 60)
        print("RAG Wiki - Mode Interactif")
        print("=" * 60)
        print("Tapez une commande ou 'help' pour l'aide, 'exit' pour quitter")
        print()
        
        while True:
            try:
                command = input("> ").strip()
                
                if not command:
                    continue
                
                if command.lower() in ['exit', 'quit', 'q']:
                    print("Au revoir !")
                    break
                
                if command.lower() in ['help', '?', '/wiki-help']:
                    self.print_help()
                    continue
                
                # Exécuter la commande
                result = await self.run_command(command)
                self.print_result(result)
                print()
                
            except KeyboardInterrupt:
                print("\nAu revoir !")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")
    
    def run(self, args: List[str]) -> None:
        """Exécuter avec les arguments fournis."""
        if not args:
            self.print_help()
            return
        
        # Joindre les arguments pour former une commande
        command = " ".join(args)
        
        # Exécuter la commande
        result = asyncio.run(self.run_command(command))
        self.print_result(result)


def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Interface CLI pour le système RAG Wiki",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python rag_cli.py /wiki-init
  python rag_cli.py /wiki-ingest raw/papers/article.pdf
  python rag_cli.py /wiki-query "Qu'est-ce que l'IA ?"
  python rag_cli.py /wiki-lint
  python rag_cli.py /wiki-status
  python rag_cli.py --interactive
        """,
    )
    
    parser.add_argument(
        "command",
        nargs="*",
        help="Commande à exécuter (ex: /wiki-init, /wiki-ingest fichier.pdf)",
    )
    
    parser.add_argument(
        "--vault",
        type=str,
        default=None,
        help="Chemin du vault (par défaut: ~/vaults/knowledge_base ou ./vault)",
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Chemin du fichier de configuration",
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Mode interactif",
    )
    
    parser.add_argument(
        "--help",
        action="store_true",
        help="Afficher l'aide",
    )
    
    args = parser.parse_args()
    
    # Initialiser l'interface CLI
    cli = RAGCLI(
        vault_path=args.vault,
        config_path=args.config,
    )
    
    if args.help or not args.command:
        cli.print_help()
    elif args.interactive:
        asyncio.run(cli.run_interactive())
    else:
        cli.run(args.command)


if __name__ == "__main__":
    main()
