#!/usr/bin/env python3
"""
Script de mise à jour de l'index pour le système RAG Wiki.

Ce script met à jour manuellement l'index du vault.
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
        description="Mettre à jour l'index du vault RAG Wiki",
    )
    
    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="Chemin du vault",
    )
    
    args = parser.parse_args()
    
    # Convertir le chemin
    vault_path = Path(args.path).expanduser().resolve()
    
    print(f"Mise à jour de l'index du vault: {vault_path}")
    
    # Vérifier que le vault existe
    if not (vault_path / "wiki").exists():
        print(f"❌ Vault non trouvé: {vault_path}")
        sys.exit(1)
    
    # Créer la configuration
    config = WikiConfig(vault_path=vault_path)
    
    # Initialiser le WikiEngine
    engine = WikiEngine(config=config, vault_path=vault_path)
    
    # Mettre à jour l'index
    try:
        success = await engine.update_index()
        
        if success:
            print("\n✅ Index mis à jour avec succès!")
        else:
            print("\n❌ Échec de la mise à jour de l'index")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Erreur lors de la mise à jour de l'index: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
