#!/usr/bin/env python3
"""
Script de requête pour le système RAG Wiki.

Ce script effectue une requête sur le vault.
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
        description="Effectuer une requête sur le vault RAG Wiki",
    )
    
    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="Chemin du vault",
    )
    
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Requête à effectuer",
    )
    
    parser.add_argument(
        "--index",
        action="store_true",
        default=True,
        help="Utiliser la recherche dans l'index",
    )
    
    parser.add_argument(
        "--bm25",
        action="store_true",
        default=True,
        help="Utiliser la recherche BM25",
    )
    
    parser.add_argument(
        "--embeddings",
        action="store_true",
        default=True,
        help="Utiliser la recherche par embeddings",
    )
    
    args = parser.parse_args()
    
    # Convertir le chemin
    vault_path = Path(args.path).expanduser().resolve()
    
    print(f"Requête sur le vault: {vault_path}")
    print(f"Requête: {args.query}")
    
    # Vérifier que le vault existe
    if not (vault_path / "wiki").exists():
        print(f"❌ Vault non trouvé: {vault_path}")
        sys.exit(1)
    
    # Créer la configuration
    config = WikiConfig(vault_path=vault_path)
    
    # Initialiser le WikiEngine
    engine = WikiEngine(config=config, vault_path=vault_path)
    
    # Effectuer la requête
    try:
        result = await engine.query(
            query_text=args.query,
            use_index=args.index,
            use_bm25=args.bm25,
            use_embeddings=args.embeddings,
        )
        
        if result.success:
            print("\n" + "=" * 60)
            print("RÉSULTAT DE LA REQUÊTE")
            print("=" * 60)
            print(f"\nRequête: {result.query}")
            print(f"\nRéponse:\n{result.answer}")
            if result.cited_pages:
                print(f"\nPages citées ({len(result.cited_pages)}):")
                for page in result.cited_pages:
                    print(f"  - [[{page}]]")
            print(f"\nDurée: {result.duration_seconds:.2f} secondes")
            print("=" * 60)
        else:
            print(f"\n❌ Échec de la requête: {result.error}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Erreur lors de la requête: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
