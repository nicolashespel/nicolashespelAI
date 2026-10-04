#!/usr/bin/env python3
"""
Exemple de création d'un vault RAG Wiki.

Ce script montre comment créer et utiliser un vault RAG Wiki.
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config import WikiConfig
from core.wiki_engine import WikiEngine


async def main():
    """Fonction principale."""
    print("=" * 60)
    print("EXEMPLE DE CRÉATION D'UN VAULT RAG WIKI")
    print("=" * 60)
    
    # 1. Créer la configuration
    print("\n1. Création de la configuration...")
    config = WikiConfig(
        vault_path=Path("~/vaults/exemple").expanduser(),
        topic="Exemple RAG Wiki",
        tool="all",
    )
    print(f"   ✓ Configuration créée pour: {config.vault_path}")
    
    # 2. Initialiser le WikiEngine
    print("\n2. Initialisation du WikiEngine...")
    engine = WikiEngine(config=config, vault_path=config.vault_path)
    print("   ✓ WikiEngine initialisé")
    
    # 3. Initialiser le vault
    print("\n3. Initialisation du vault...")
    success = await engine.initialize_vault(
        topic="Exemple RAG Wiki",
        tool="all",
    )
    if success:
        print("   ✓ Vault initialisé avec succès")
    else:
        print("   ✗ Échec de l'initialisation")
        return
    
    # 4. Obtenir les statistiques du vault
    print("\n4. Statistiques du vault...")
    stats = engine.get_vault_stats()
    print(f"   - Total pages: {stats.get('total_pages', 0)}")
    print(f"   - Entités: {stats.get('pages_by_type', {}).get('entity', 0)}")
    print(f"   - Concepts: {stats.get('pages_by_type', {}).get('concept', 0)}")
    print(f"   - Sources: {stats.get('pages_by_type', {}).get('source', 0)}")
    
    print("\n" + "=" * 60)
    print("EXEMPLE TERMINÉ")
    print("=" * 60)
    print("\nProchaines étapes:")
    print("  1. Déposez vos sources dans ~/vaults/exemple/raw/")
    print("  2. Utilisez: python scripts/ingest_source.py --path ~/vaults/exemple --source <chemin>")
    print("  3. Effectuez des requêtes avec: python scripts/query_wiki.py --path ~/vaults/exemple --query <requête>")


if __name__ == "__main__":
    asyncio.run(main())
