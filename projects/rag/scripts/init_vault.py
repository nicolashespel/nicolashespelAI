#!/usr/bin/env python3
"""
Script d'initialisation du vault pour le système RAG Wiki.

Ce script crée la structure complète d'un nouveau vault.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import WikiConfig
from src.core.wiki_engine import WikiEngine


async def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Initialiser un nouveau vault RAG Wiki",
    )
    
    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="Chemin du vault à créer",
    )
    
    parser.add_argument(
        "--topic",
        type=str,
        default="Recherche",
        help="Sujet principal du vault",
    )
    
    parser.add_argument(
        "--tool",
        type=str,
        default="all",
        choices=["all", "claude", "codex", "cursor"],
        help="Outil LLM à configurer",
    )
    
    args = parser.parse_args()
    
    # Convertir le chemin
    vault_path = Path(args.path).expanduser().resolve()
    
    print(f"Initialisation du vault à: {vault_path}")
    print(f"Sujet: {args.topic}")
    print(f"Outil: {args.tool}")
    
    # Créer le dossier si nécessaire
    vault_path.mkdir(parents=True, exist_ok=True)
    
    # Créer la configuration
    config = WikiConfig(
        vault_path=vault_path,
        topic=args.topic,
        tool=args.tool,
    )
    
    # Initialiser le WikiEngine
    engine = WikiEngine(config=config, vault_path=vault_path)
    
    # Initialiser le vault
    try:
        success = await engine.initialize_vault(
            topic=args.topic,
            tool=args.tool,
        )
        
        if success:
            print("\n✅ Vault initialisé avec succès!")
            print(f"\nStructure créée dans: {vault_path}")
            print("\nPour commencer:")
            print(f"  1. Déposez vos sources dans {vault_path / 'raw'}")
            print(f"  2. Utilisez la commande: /wiki-ingest <chemin_vers_la_source>")
            print(f"  3. Ou exécutez: python {Path(__file__).parent / 'ingest_source.py'} --path {vault_path} --source <chemin>")
        else:
            print("\n❌ Échec de l'initialisation du vault")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
