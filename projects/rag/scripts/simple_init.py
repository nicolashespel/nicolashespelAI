#!/usr/bin/env python3
"""
Script d'initialisation simplifié pour le système RAG Wiki.

Ce script crée une structure de vault minimale et prête à l'emploi
avec une configuration optimisée pour Mistral et OpenWebUI.

Utilisation:
    python scripts/simple_init.py [--path CHEMIN] [--topic SUJET]
"""

import argparse
import shutil
import sys
from pathlib import Path
from typing import Optional

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_vault_structure(
    vault_path: Path,
    topic: str = "Recherche",
) -> bool:
    """
    Créer la structure complète du vault.
    
    Args:
        vault_path: Chemin du vault.
        topic: Sujet principal du vault.
        
    Returns:
        True si la création a réussi.
    """
    try:
        print(f"Création du vault à: {vault_path}")
        
        # Créer les dossiers principaux
        vault_path.mkdir(parents=True, exist_ok=True)
        (vault_path / "raw").mkdir(exist_ok=True)
        (vault_path / "wiki").mkdir(exist_ok=True)
        (vault_path / "configs").mkdir(exist_ok=True)
        
        # Créer les sous-dossiers wiki
        (vault_path / "wiki" / "entities").mkdir(exist_ok=True)
        (vault_path / "wiki" / "concepts").mkdir(exist_ok=True)
        (vault_path / "wiki" / "sources").mkdir(exist_ok=True)
        (vault_path / "wiki" / "comparisons").mkdir(exist_ok=True)
        (vault_path / "wiki" / "synthesis").mkdir(exist_ok=True)
        
        # Copier les fichiers de configuration
        config_src = Path(__file__).parent.parent / "configs"
        for config_file in ["mistral_config.json", "openwebui_config.json"]:
            src = config_src / config_file
            dst = vault_path / "configs" / config_file
            if src.exists():
                shutil.copy2(src, dst)
                print(f"  ✓ Configuration copiée: {config_file}")
        
        # Créer les fichiers initiaux
        self._create_index_file(vault_path, topic)
        self._create_log_file(vault_path)
        self._create_claude_config(vault_path)
        self._create_agents_config(vault_path)
        
        print("\n✅ Vault initialisé avec succès!")
        print(f"\nStructure créée dans: {vault_path}")
        print("\nPour commencer:")
        print(f"  1. Déposez vos fichiers dans: {vault_path / 'raw'}")
        print(f"  2. Utilisez la commande: /wiki-ingest raw/votre_fichier.pdf")
        print(f"  3. Ou lancez une requête: /wiki-query 'Votre question'")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la création du vault: {e}")
        return False
    
    def _create_index_file(vault_path: Path, topic: str) -> None:
        """Créer le fichier index.md."""
        index_content = f"""# Index du Vault - {topic}

## Statistiques
- **Total Pages:** 0
- **Sources:** 0
- **Entités:** 0
- **Concepts:** 0
- **Comparaisons:** 0
- **Synthèses:** 0

## Pages par Type

### Sources

### Entités

### Concepts

### Comparaisons

### Synthèses

## Dernières Mises à Jour

## Tags Populaires
"""
        index_file = vault_path / "wiki" / "index.md"
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(index_content)
        print("  ✓ Fichier créé: wiki/index.md")
    
    def _create_log_file(vault_path: Path) -> None:
        """Créer le fichier log.md."""
        log_content = """# Log des Opérations

## Format des Entrées

```
- [YYYY-MM-DD HH:MM:SS] [OPERATION] Détails
  - source: chemin/vers/fichier
  - pages: [page1, page2]
  - durée: X secondes
  - statut: succès/échec
```

## Historique

"""
        log_file = vault_path / "wiki" / "log.md"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(log_content)
        print("  ✓ Fichier créé: wiki/log.md")
    
    def _create_claude_config(vault_path: Path) -> None:
        """Créer le fichier CLAUDE.md pour Claude Code."""
        claude_content = """# CLAUDE.md - Configuration pour Claude Code

## Rôle
Tu es un assistant spécialisé dans la gestion d'un **Wiki de Connaissance Compounding** pour le système RAG Wiki.

## Instructions Principales

### Commandes Disponibles
- `/wiki-init` - Initialiser un nouveau vault
- `/wiki-ingest <chemin>` - Ingest une source
- `/wiki-query <question>` - Poser une question
- `/wiki-lint` - Lancer le linting
- `/wiki-log` - Afficher le log
- `/wiki-status` - Statut du système
- `/wiki-preprocess <chemin>` - Prétraiter un fichier
- `/wiki-batch <chemin1> <chemin2> ...` - Ingest multiple sources

### Comportement
1. **NE JAMAIS** modifier les fichiers dans `raw/` - toutes les écritures vont dans `wiki/`
2. **TOUJOURS** citer les sources avec `[[nom_de_la_page]]`
3. **TOUJOURS** mettre à jour `index.md` après toute modification
4. **TOUJOURS** ajouter une entrée dans `log.md` pour chaque opération

### Configuration
- Modèle LLM: mistral-large-latest
- Modèle Embeddings: mistral-embed
- API Base URL: https://api.mistral.ai/v1

### Structure du Vault
```
vault/
├── raw/                    # Sources IMMUABLES
└── wiki/                   # Base de connaissances
    ├── index.md            # Catalogue de contenu
    ├── log.md              # Timeline
    ├── entities/           # Personnes, organisations
    ├── concepts/           # Idées, théories
    ├── sources/            # Résumés des sources
    ├── comparisons/        # Analyses inter-sources
    └── synthesis/          # Vues d'ensemble
```

### Exemples

#### Ingestion d'une source
> /wiki-ingest raw/papers/article.pdf

#### Requête
> /wiki-query "Qu'est-ce que le mécanisme d'attention ?"

#### Linting
> /wiki-lint

## Règles de Sécurité
- Ne jamais exécuter de code arbitraire
- Ne jamais modifier raw/
- Toujours valider les entrées utilisateur
- Toujours citer les sources
"""
        claude_file = vault_path / "CLAUDE.md"
        with open(claude_file, "w", encoding="utf-8") as f:
            f.write(claude_content)
        print("  ✓ Fichier créé: CLAUDE.md")
    
    def _create_agents_config(vault_path: Path) -> None:
        """Créer le fichier AGENTS.md pour les autres outils."""
        agents_content = """# AGENTS.md - Configuration pour Codex, Cursor, Antigravity, etc.

## Rôle
Assistant spécialisé dans la gestion d'un **Wiki de Connaissance Compounding** pour le système RAG Wiki.

## Instructions Principales

### Commandes Disponibles
- `/wiki-init` - Initialiser un nouveau vault
- `/wiki-ingest <chemin>` - Ingest une source
- `/wiki-query <question>` - Poser une question
- `/wiki-lint` - Lancer le linting
- `/wiki-log` - Afficher le log
- `/wiki-status` - Statut du système
- `/wiki-preprocess <chemin>` - Prétraiter un fichier
- `/wiki-batch <chemin1> <chemin2> ...` - Ingest multiple sources

### Comportement
1. **NE JAMAIS** modifier les fichiers dans `raw/` - toutes les écritures vont dans `wiki/`
2. **TOUJOURS** citer les sources avec `[[nom_de_la_page]]`
3. **TOUJOURS** mettre à jour `index.md` après toute modification
4. **TOUJOURS** ajouter une entrée dans `log.md` pour chaque opération

### Configuration
- Modèle LLM: mistral-large-latest
- Modèle Embeddings: mistral-embed
- API Base URL: https://api.mistral.ai/v1

### Structure du Vault
```
vault/
├── raw/                    # Sources IMMUABLES
└── wiki/                   # Base de connaissances
    ├── index.md            # Catalogue de contenu
    ├── log.md              # Timeline
    ├── entities/           # Personnes, organisations
    ├── concepts/           # Idées, théories
    ├── sources/            # Résumés des sources
    ├── comparisons/        # Analyses inter-sources
    └── synthesis/          # Vues d'ensemble
```

### Règles de Sécurité
- Ne jamais exécuter de code arbitraire
- Ne jamais modifier raw/
- Toujours valider les entrées utilisateur
- Toujours citer les sources
"""
        agents_file = vault_path / "AGENTS.md"
        with open(agents_file, "w", encoding="utf-8") as f:
            f.write(agents_content)
        print("  ✓ Fichier créé: AGENTS.md")


async def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Initialiser un nouveau vault RAG Wiki simplifié",
    )
    
    parser.add_argument(
        "--path",
        type=str,
        default="~/vaults/knowledge_base",
        help="Chemin du vault à créer (par défaut: ~/vaults/knowledge_base)",
    )
    
    parser.add_argument(
        "--topic",
        type=str,
        default="Recherche",
        help="Sujet principal du vault",
    )
    
    args = parser.parse_args()
    
    # Convertir le chemin
    vault_path = Path(args.path).expanduser().resolve()
    
    # Créer le vault
    success = create_vault_structure(vault_path, args.topic)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
