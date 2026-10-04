#!/usr/bin/env python3
"""
Script de linting pour le système RAG Wiki.

Ce script effectue un linting du vault.
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
        description="Effectuer un linting du vault RAG Wiki",
    )
    
    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="Chemin du vault",
    )
    
    parser.add_argument(
        "--mechanical",
        action="store_true",
        default=True,
        help="Vérifier les aspects mécaniques",
    )
    
    parser.add_argument(
        "--semantic",
        action="store_true",
        default=True,
        help="Vérifier les aspects sémantiques",
    )
    
    parser.add_argument(
        "--health",
        action="store_true",
        default=True,
        help="Vérifier la santé globale",
    )
    
    args = parser.parse_args()
    
    # Convertir le chemin
    vault_path = Path(args.path).expanduser().resolve()
    
    print(f"Linting du vault: {vault_path}")
    
    # Vérifier que le vault existe
    if not (vault_path / "wiki").exists():
        print(f"❌ Vault non trouvé: {vault_path}")
        sys.exit(1)
    
    # Créer la configuration
    config = WikiConfig(vault_path=vault_path)
    
    # Initialiser le WikiEngine
    engine = WikiEngine(config=config, vault_path=vault_path)
    
    # Effectuer le linting
    try:
        result = await engine.lint(
            check_mechanical=args.mechanical,
            check_semantic=args.semantic,
            check_health=args.health,
        )
        
        if result.success:
            print("\n" + "=" * 60)
            print("RAPPORT DE LINTING")
            print("=" * 60)
            
            # Statistiques
            print(f"\nStatistiques:")
            print(f"  - Durée: {result.duration_seconds:.2f} secondes")
            print(f"  - Erreurs: {len(result.errors)}")
            print(f"  - Avertissements: {len(result.warnings)}")
            print(f"  - Informations: {len(result.issues)}")
            
            # Erreurs
            if result.errors:
                print(f"\n❌ ERREURS CRITIQUES ({len(result.errors)}):")
                for i, error in enumerate(result.errors, 1):
                    print(f"\n{i}. {error.get('message', 'Erreur inconnue')}")
                    print(f"   Type: {error.get('type', 'unknown')}")
                    if 'file' in error:
                        print(f"   Fichier: {error['file']}")
                    if 'files' in error:
                        print(f"   Fichiers: {', '.join(error['files'])}")
            
            # Avertissements
            if result.warnings:
                print(f"\n⚠️  AVERTISSEMENTS ({len(result.warnings)}):")
                for i, warning in enumerate(result.warnings, 1):
                    print(f"\n{i}. {warning.get('message', 'Avertissement inconnu')}")
                    print(f"   Type: {warning.get('type', 'unknown')}")
                    if 'file' in warning:
                        print(f"   Fichier: {warning['file']}")
                    if 'files' in warning:
                        print(f"   Fichiers: {', '.join(warning['files'])}")
            
            # Informations
            if result.issues:
                print(f"\nℹ️  INFORMATIONS ({len(result.issues)}):")
                for i, issue in enumerate(result.issues, 1):
                    print(f"\n{i}. {issue.get('message', 'Information inconnue')}")
                    print(f"   Type: {issue.get('type', 'unknown')}")
                    if 'file' in issue:
                        print(f"   Fichier: {issue['file']}")
                    if 'files' in issue:
                        print(f"   Fichiers: {', '.join(issue['files'])}")
            
            # Résumé
            if result.errors:
                status = "❌ Requiert attention urgente"
            elif result.warnings:
                status = "⚠️  Requiert attention"
            else:
                status = "✅ Sain"
            
            print(f"\n{'=' * 60}")
            print(f"STATUT GLOBAL: {status}")
            print("=" * 60)
        else:
            print(f"\n❌ Échec du linting: {result.error}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Erreur lors du linting: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
