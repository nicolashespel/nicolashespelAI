#!/usr/bin/env python3
"""
Script CLI pour prétraiter les fichiers dans raw/ avant ingestion.

Ce script utilise le PreprocessingAgent pour nettoyer et structurer les documents.
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ajouter le chemin parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.preprocessing_agent import PreprocessingAgent
from src.core.config import WikiConfig


def parse_args():
    """Parser les arguments CLI."""
    parser = argparse.ArgumentParser(
        description="Prétraiter les fichiers pour le système RAG Wiki",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python preprocess_raw.py --input raw/documents/paper.pdf
  python preprocess_raw.py --input raw/documents/paper.pdf --output raw/clean/paper.md
  python preprocess_raw.py --input raw/documents/paper.pdf --no-confirm
  python preprocess_raw.py --batch raw/documents/*.pdf
  python preprocess_raw.py --batch raw/documents/paper1.pdf raw/documents/paper2.pdf
        """
    )
    
    # Arguments principaux
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        help="Chemin du fichier à prétraiter",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Chemin du fichier de sortie (optionnel)",
    )
    parser.add_argument(
        "--batch",
        "-b",
        type=str,
        nargs="+",
        help="Liste des fichiers à prétraiter en batch",
    )
    parser.add_argument(
        "--vault",
        "-v",
        type=str,
        default="~/vaults/research",
        help="Chemin du vault (par défaut: ~/vaults/research)",
    )
    
    # Options de traitement
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Ne pas demander confirmation pour les suppressions",
    )
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Désactiver la déduplication",
    )
    parser.add_argument(
        "--no-chunk",
        action="store_true",
        help="Désactiver le découpage en chunks",
    )
    
    # Options de sortie
    parser.add_argument(
        "--json",
        action="store_true",
        help="Sortie au format JSON",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Mode silencieux (seulement les erreurs)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mode verbeux",
    )
    
    return parser.parse_args()


async def preprocess_single_file(
    agent: PreprocessingAgent,
    input_path: Path,
    output_path: Optional[Path],
    ask_confirmation: bool,
) -> Dict[str, Any]:
    """Prétraiter un fichier unique."""
    success, output_path_result, report = await agent.preprocess(
        input_path=input_path,
        output_path=output_path,
        ask_for_confirmation=ask_confirmation,
    )
    
    return {
        "success": success,
        "input_path": str(input_path),
        "output_path": str(output_path_result) if output_path_result else "",
        "report": report,
    }


async def preprocess_batch(
    agent: PreprocessingAgent,
    input_paths: List[Path],
    output_dir: Optional[Path],
    ask_confirmation: bool,
) -> Dict[str, Any]:
    """Prétraiter plusieurs fichiers en batch."""
    results = {}
    
    for input_path in input_paths:
        if output_dir:
            output_path = output_dir / f"{input_path.stem}.md"
        else:
            output_path = None
        
        result = await preprocess_single_file(
            agent=agent,
            input_path=input_path,
            output_path=output_path,
            ask_confirmation=ask_confirmation,
        )
        results[str(input_path)] = result
    
    return {
        "total_files": len(input_paths),
        "successful": sum(1 for r in results.values() if r["success"]),
        "failed": sum(1 for r in results.values() if not r["success"]),
        "results": results,
    }


def print_result(result: Dict[str, Any], json_output: bool = False, verbose: bool = False) -> None:
    """Afficher le résultat."""
    if json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if result.get("success", False):
            print(f"✓ Fichier prétraité: {result.get('input_path', 'inconnu')}")
            print(f"  → Sortie: {result.get('output_path', 'inconnu')}")
            
            report = result.get("report", {})
            stats = report.get("stats", {})
            
            print(f"  Statistiques:")
            print(f"    - Taille originale: {stats.get('original_size', 0)} octets")
            print(f"    - Taille nettoyée: {stats.get('cleaned_size', 0)} octets")
            print(f"    - Redondances supprimées: {stats.get('redundant_removed', 0)}")
            print(f"    - Uniques conservés: {stats.get('unique_kept', 0)}")
            print(f"    - Chunks créés: {stats.get('chunks_created', 0)}")
            
            if verbose and report.get("operations"):
                print(f"  Opérations: {', '.join(report['operations'][:5])}")
            
            if report.get("warnings"):
                for warning in report["warnings"][:3]:  # Limiter à 3 avertissements
                    print(f"  ⚠ {warning}")
        else:
            print(f"✗ Échec du prétraitement: {result.get('input_path', 'inconnu')}")
            report = result.get("report", {})
            if report.get("errors"):
                for error in report["errors"]:
                    print(f"  ✗ {error}")


def print_batch_result(result: Dict[str, Any], json_output: bool = False) -> None:
    """Afficher le résultat d'un batch."""
    if json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Traitement en batch terminé")
        print(f"  Total: {result.get('total_files', 0)} fichiers")
        print(f"  Réussis: {result.get('successful', 0)}")
        print(f"  Échecs: {result.get('failed', 0)}")
        
        if result.get("failed", 0) > 0:
            print(f"\nFichiers en échec:")
            for path, data in result.get("results", {}).items():
                if not data.get("success", False):
                    print(f"  ✗ {path}")


def main():
    """Point d'entrée principal."""
    args = parse_args()
    
    # Résoudre les chemins
    vault_path = Path(args.vault).expanduser()
    
    # Initialiser l'agent
    try:
        agent = PreprocessingAgent(vault_path)
    except Exception as e:
        print(f"✗ Erreur lors de l'initialisation: {e}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Vérifier les arguments
        if args.input:
            # Traitement d'un fichier unique
            input_path = Path(args.input)
            
            # Vérifier si le chemin est relatif
            if not input_path.is_absolute():
                input_path = vault_path / input_path
            
            if not input_path.exists():
                print(f"✗ Fichier non trouvé: {input_path}", file=sys.stderr)
                sys.exit(1)
            
            # Déterminer le chemin de sortie
            if args.output:
                output_path = Path(args.output)
                if not output_path.is_absolute():
                    output_path = vault_path / output_path
            else:
                output_path = None
            
            # Exécuter le prétraitement
            result = asyncio.run(preprocess_single_file(
                agent=agent,
                input_path=input_path,
                output_path=output_path,
                ask_confirmation=not args.no_confirm,
            ))
            
            print_result(result, args.json, args.verbose)
            
        elif args.batch:
            # Traitement en batch
            input_paths = []
            for pattern in args.batch:
                pattern_path = Path(pattern)
                if not pattern_path.is_absolute():
                    pattern_path = vault_path / pattern_path
                
                # Développer les wildcards
                if "*" in str(pattern_path) or "?" in str(pattern_path):
                    input_paths.extend(pattern_path.parent.glob(pattern_path.name))
                elif pattern_path.exists():
                    input_paths.append(pattern_path)
            
            if not input_paths:
                print(f"✗ Aucun fichier trouvé pour les motifs: {args.batch}", file=sys.stderr)
                sys.exit(1)
            
            # Déterminer le dossier de sortie
            output_dir = None
            if args.output:
                output_dir = Path(args.output)
                if not output_dir.is_absolute():
                    output_dir = vault_path / output_dir
                output_dir.mkdir(parents=True, exist_ok=True)
            
            # Exécuter le prétraitement en batch
            result = asyncio.run(preprocess_batch(
                agent=agent,
                input_paths=input_paths,
                output_dir=output_dir,
                ask_confirmation=not args.no_confirm,
            ))
            
            print_batch_result(result, args.json)
            
        else:
            # Aucune commande spécifiée, afficher l'aide
            print("Erreur: Aucune entrée spécifiée")
            print("Utilisez --input pour un fichier unique ou --batch pour plusieurs fichiers")
            print("Exemple: python preprocess_raw.py --input raw/doc.pdf")
            print("        python preprocess_raw.py --batch raw/*.pdf")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nOpération annulée par l'utilisateur")
        sys.exit(130)
    except Exception as e:
        print(f"✗ Erreur: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        agent.close()


if __name__ == "__main__":
    main()
