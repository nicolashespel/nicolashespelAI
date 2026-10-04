#!/usr/bin/env python3
"""
Script d'ingestion de source pour le système RAG Wiki.

Ce script ingère une source dans le vault.
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
        description="Ingérer une source dans le vault RAG Wiki",
    )
    
    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="Chemin du vault",
    )
    
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="Chemin de la source à ingérer",
    )
    
    parser.add_argument(
        "--discuss",
        action="store_true",
        default=False,
        help="Discuter avec l'utilisateur avant l'ingestion",
    )
    
    args = parser.parse_args()
    
    # Convertir les chemins
    vault_path = Path(args.path).expanduser().resolve()
    source_path = Path(args.source).expanduser().resolve()
    
    print(f"Ingestion de: {source_path}")
    print(f"Dans le vault: {vault_path}")
    
    # Vérifier que la source existe
    if not source_path.exists():
        print(f"❌ Source non trouvée: {source_path}")
        sys.exit(1)
    
    # Vérifier que le vault existe
    if not (vault_path / "wiki").exists():
        print(f"❌ Vault non trouvé: {vault_path}")
        print("Utilisez d'abord init_vault.py pour créer le vault.")
        sys.exit(1)
    
    # Créer la configuration
    config = WikiConfig(vault_path=vault_path)
    
    # Initialiser le WikiEngine
    engine = WikiEngine(config=config, vault_path=vault_path)
    
    # Ingestion de la source
    try:
        result = await engine.ingest_source(
            source_path=source_path,
            discuss_with_user=args.discuss,
        )
        
        if result.success:
            print("\n✅ Ingestion terminée avec succès!")
            print(f"\nDétails:")
            print(f"  - Source: {result.source_path}")
            print(f"  - Page de résumé: {result.summary_page}")
            print(f"  - Pages mises à jour: {len(result.updated_pages)}")
            if result.updated_pages:
                for page in result.updated_pages:
                    print(f"    - {page}")
            print(f"  - Références croisées: {len(result.cross_references)}")
            print(f"  - Durée: {result.duration_seconds:.2f} secondes")
        else:
            print(f"\n❌ Échec de l'ingestion: {result.error}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Erreur lors de l'ingestion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
