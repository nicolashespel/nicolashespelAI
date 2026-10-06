#!/usr/bin/env python3
"""
Script de setup pour OpenWebUI.

Ce script configure automatiquement OpenWebUI pour utiliser
les 4 agents du système RAG Wiki.

Utilisation:
    python openwebui/setup.py [--vault CHEMIN] [--output DIR]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ajouter le chemin du projet
sys.path.insert(0, str(Path(__file__).parent.parent))

from .config import OpenWebUIConfig


class OpenWebUISetup:
    """
    Setup pour OpenWebUI.
    
    Ce script:
    1. Génère la configuration des agents
    2. Crée les scripts nécessaires
    3. Génère la documentation
    4. Configure l'environnement
    """
    
    def __init__(
        self,
        vault_path: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> None:
        """
        Initialiser le setup.
        
        Args:
            vault_path: Chemin du vault par défaut.
            output_dir: Dossier de sortie pour les fichiers générés.
        """
        self.vault_path = vault_path or os.getenv("WIKI_VAULT_PATH", "~/vaults/knowledge_base")
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "openwebui_config"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialiser la configuration
        self.config = OpenWebUIConfig(self.vault_path)
    
    def generate_all(self) -> None:
        """Générer tous les fichiers de configuration."""
        print("=" * 60)
        print("Setup OpenWebUI pour RAG Wiki")
        print("=" * 60)
        print()
        
        # Générer la configuration principale
        self._generate_main_config()
        
        # Générer les scripts d'agents
        self._generate_agent_scripts()
        
        # Générer le wrapper CLI
        self._generate_cli_wrapper()
        
        # Générer le fichier .env
        self._generate_env_file()
        
        # Générer la documentation
        self._generate_documentation()
        
        print()
        print("=" * 60)
        print("Setup terminé avec succès!")
        print("=" * 60)
        print()
        print("Fichiers générés dans:", self.output_dir)
        print()
        print("Prochaines étapes:")
        print("1. Définissez MISTRAL_API_KEY dans votre environnement")
        print("2. Initialisez un vault: python scripts/simple_init.py")
        print("3. Dans OpenWebUI, ajoutez un outil personnalisé:")
        print(f"   - Commande: python {self.output_dir / 'openwebui_cli.py'}")
        print("   - Arguments: {{query}}")
        print()
        print("4. Utilisez les commandes:")
        print("   /clean <fichier> - Nettoyer")
        print("   /ingest <fichier> - Ingest")
        print("   /search <requête> - Rechercher")
        print("   /health - Vérifier la santé")
        print("=" * 60)
    
    def _generate_main_config(self) -> None:
        """Générer la configuration principale."""
        print("Génération de la configuration principale...")
        
        config = self.config.generate_openwebui_config()
        config_path = self.output_dir / "openwebui_config.json"
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Configuration: {config_path}")
    
    def _generate_agent_scripts(self) -> None:
        """Générer les scripts pour chaque agent."""
        print("Génération des scripts d'agents...")
        
        agents = ["cleanup", "ingestion", "search", "health"]
        
        for agent in agents:
            script = self.config.generate_agent_script(agent)
            script_path = self.output_dir / f"{agent}_agent.py"
            
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script)
            
            # Rendre exécutable
            script_path.chmod(0o755)
            print(f"  ✓ Script: {script_path}")
    
    def _generate_cli_wrapper(self) -> None:
        """Générer le wrapper CLI."""
        print("Génération du wrapper CLI...")
        
        wrapper = self.config.generate_cli_wrapper()
        wrapper_path = self.output_dir / "openwebui_cli.py"
        
        with open(wrapper_path, "w", encoding="utf-8") as f:
            f.write(wrapper)
        
        # Rendre exécutable
        wrapper_path.chmod(0o755)
        print(f"  ✓ Wrapper CLI: {wrapper_path}")
    
    def _generate_env_file(self) -> None:
        """Générer le fichier .env."""
        print("Génération du fichier .env...")
        
        env_path = self.output_dir / ".env"
        
        env_content = f"""# Configuration pour OpenWebUI - RAG Wiki

# Clé API Mistral (OBLIGATOIRE)
MISTRAL_API_KEY=votre_clé_api_ici

# Chemin du vault
WIKI_VAULT_PATH={self.vault_path}

# Configuration des modèles (optionnel)
WIKI_LLM_MODEL=mistral-large-latest
WIKI_EMBEDDING_MODEL=mistral-embed

# Configuration de la recherche (optionnel)
WIKI_USE_BM25=true
WIKI_USE_EMBEDDINGS=true
WIKI_BM25_K=50
WIKI_EMBEDDING_K=10
WIKI_RRF_K=60

# Configuration du logging (optionnel)
WIKI_LOG_LEVEL=INFO
"""
        
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content)
        
        print(f"  ✓ Fichier .env: {env_path}")
    
    def _generate_documentation(self) -> None:
        """Générer la documentation."""
        print("Génération de la documentation...")
        
        doc_path = self.output_dir / "README.md"
        
        doc_content = f"""# Configuration OpenWebUI pour RAG Wiki

> **Intégration des 4 agents avec OpenWebUI**
> Version 1.0.0 - Système RAG Wiki avec Mistral

## 🎯 Vue d'ensemble

Ce dossier contient la configuration complète pour intégrer le système RAG Wiki avec OpenWebUI.
Les 4 agents principaux sont disponibles via des commandes simples.

## 📁 Structure

```
openwebui_config/
├── openwebui_config.json    # Configuration complète des agents
├── cleanup_agent.py         # Script pour l'agent de nettoyage
├── ingestion_agent.py      # Script pour l'agent d'ingestion
├── search_agent.py         # Script pour l'agent de recherche
├── health_agent.py         # Script pour l'agent de santé
├── openwebui_cli.py        # Wrapper CLI principal
├── .env                    # Variables d'environnement
└── README.md               # Documentation (ce fichier)
```

## 🚀 Installation

### 1. Prérequis
- Python 3.12+
- OpenWebUI installé et en cours d'exécution
- Une clé API Mistral

### 2. Configuration

#### Définir la clé API

Dans le fichier `.env` de ce dossier, définissez votre clé API:

```bash
MISTRAL_API_KEY=votre_clé_api_ici
```

Ou définissez-la dans votre environnement:

```bash
export MISTRAL_API_KEY=votre_clé_api_ici
```

#### Configurer le vault

Par défaut, le vault est situé dans: `{self.vault_path}`

Vous pouvez le changer dans le fichier `.env`:

```bash
WIKI_VAULT_PATH=~/vaults/ma_base
```

### 3. Initialiser le vault

Avant d'utiliser les agents, initialisez un vault:

```bash
python projects/rag/scripts/simple_init.py --path ~/vaults/ma_base --topic "Mon Sujet"
```

## 🎮 Utilisation avec OpenWebUI

### Configuration dans OpenWebUI

1. **Ouvrez OpenWebUI** dans votre navigateur
2. **Allez dans Settings > Tools**
3. **Ajoutez un nouvel outil personnalisé:**
   - **Name:** RAG Wiki
   - **Command:** `python {self.output_dir / 'openwebui_cli.py'}`
   - **Arguments:** `{query}`
   - **Working Directory:** `{self.output_dir.parent}`
4. **Enregistrez**

### Commandes disponibles

| Commande | Description | Exemple |
|----------|-------------|---------|
| `/clean <chemin>` | Nettoyer un fichier ou dossier | `/clean raw/documents/article.pdf` |
| `/ingest <chemin>` | Ingest un fichier ou dossier | `/ingest cleaned/article.txt` |
| `/search <requête>` | Rechercher dans le RAG | `/search "Qu'est-ce que l'IA ?"` |
| `/health` | Vérifier la santé du RAG | `/health` |

### Exemples complets

#### Workflow complet

1. **Nettoyer un document:**
   ```
   /clean raw/documents/article.pdf
   ```

2. **Ingest le document nettoyé:**
   ```
   /ingest cleaned/article.txt
   ```

3. **Rechercher dans le RAG:**
   ```
   /search "Quels sont les principaux concepts de l'article ?"
   ```

4. **Vérifier la santé:**
   ```
   /health
   ```

#### Options avancées

- **Nettoyage avec mode OCR uniquement:**
  ```
  /clean raw/images/scan.jpg --mode ocr_only
  ```

- **Ingestion avec vault spécifique:**
  ```
  /ingest cleaned/ --vault ~/vaults/projet_x
  ```

- **Recherche avec mode hybride:**
  ```
  /search "mécanisme d'attention" --mode hybrid --top_k 10
  ```

- **Vérification de santé avec corrections:**
  ```
  /health --checks all --fix true
  ```

## 📚 Description des Agents

### 1. Cleanup Agent (Nettoyage)

**Commande:** `/clean`

**Fonctionnalités:**
- Extraction de texte via Mistral OCR (PDF, images)
- Nettoyage du texte (en-têtes, pieds de page, numéros de page)
- Structuration du texte pour l'ingestion RAG
- Détection automatique de la langue

**Modèles utilisés:**
- OCR: `mistral-ocr-latest`
- Nettoyage: `mistral-small-latest`

**Exemple:**
```
/clean raw/documents/article.pdf --mode both --language fr
```

### 2. Ingestion Agent (Gestion)

**Commande:** `/ingest`

**Fonctionnalités:**
- Découpage intelligent des documents en chunks
- Génération d'embeddings avec Mistral Embed
- Indexation dans BM25 et l'index hybride
- Création de pages wiki structurées
- Mise à jour automatique de l'index et du log

**Modèles utilisés:**
- LLM: `mistral-large-latest`
- Embeddings: `mistral-embed`

**Exemple:**
```
/ingest cleaned/article.txt --mode full --preprocess true
```

### 3. Search Agent (Recherche)

**Commande:** `/search`

**Fonctionnalités:**
- Recherche hybride (BM25 + Embeddings)
- Reclassement des résultats avec Mistral Small
- Synthèse des réponses avec Mistral Large
- Ajout de citations automatiques
- Sauvegarde des réponses utiles

**Modèles utilisés:**
- Recherche: `mistral-embed`
- Reclassement: `mistral-small-latest`
- Synthèse: `mistral-large-latest`

**Exemple:**
```
/search "Qu'est-ce que le mécanisme d'attention ?" --top_k 5 --save true
```

### 4. Health Agent (Santé)

**Commande:** `/health`

**Fonctionnalités:**
- Vérification du frontmatter
- Validation des liens internes
- Détection des références manquantes
- Analyse des contradictions
- Détection des pages orphelines
- Statistiques complètes du vault

**Modèles utilisés:**
- Analyse: `mistral-small-latest`
- Modération: `shieldstral-latest`

**Exemple:**
```
/health --checks all --format full
```

## 🔧 Configuration Avancée

### Personnaliser les modèles

Vous pouvez personnaliser les modèles utilisés par chaque agent dans le fichier `openwebui_config.json`.

### Personnaliser les paramètres

Les paramètres de chaque agent peuvent être ajustés:

- **Cleanup Agent:**
  - `remove_headers`: Supprimer les en-têtes
  - `remove_footers`: Supprimer les pieds de page
  - `remove_page_numbers`: Supprimer les numéros de page
  - `enhance_quality`: Améliorer la qualité OCR

- **Ingestion Agent:**
  - `chunk_size`: Taille des chunks
  - `chunk_overlap`: Chevauchement entre chunks
  - `use_bm25`: Utiliser BM25
  - `use_embeddings`: Utiliser les embeddings

- **Search Agent:**
  - `bm25_top_k`: Nombre de résultats BM25
  - `embedding_top_k`: Nombre de résultats embeddings
  - `rrf_k`: Nombre de résultats RRF final

- **Health Agent:**
  - `check_frontmatter`: Vérifier le frontmatter
  - `check_links`: Vérifier les liens
  - `check_references`: Vérifier les références

## 🛠️ Dépannage

### Problème: La commande n'est pas reconnue
- Vérifiez que le chemin vers `openwebui_cli.py` est correct
- Vérifiez que Python 3.12+ est installé
- Vérifiez que les dépendances sont installées

### Problème: Erreur d'API Mistral
- Vérifiez que `MISTRAL_API_KEY` est correct
- Vérifiez que votre clé a assez de crédits
- Vérifiez que l'URL de l'API est correcte

### Problème: Le vault n'est pas trouvé
- Vérifiez que le chemin du vault est correct
- Vérifiez que la structure du vault existe
- Essayez d'utiliser un chemin absolu

## 📊 Statistiques et Monitoring

Vous pouvez obtenir des statistiques sur l'utilisation:

```bash
/health --format full
```

Cela affichera:
- Nombre total de pages
- Nombre de sources, entités, concepts
- Statut des index
- Problèmes détectés

## 🎉 Exemple Complet

### 1. Initialisation

```bash
# Créer un vault
python projects/rag/scripts/simple_init.py --path ~/vaults/recherche_ia --topic "Recherche en IA"

# Définir la clé API
export MISTRAL_API_KEY=votre_clé_api_ici
```

### 2. Nettoyage

```
/clean ~/vaults/recherche_ia/raw/papers/article.pdf
```

### 3. Ingestion

```
/ingest ~/vaults/recherche_ia/cleaned/article.txt
```

### 4. Recherche

```
/search "Quels sont les principaux défis de l'IA selon l'article ?"
```

### 5. Vérification

```
/health
```

## 🔗 Liens Utiles

- [Mistral AI](https://mistral.ai/)
- [Documentation Mistral API](https://docs.mistral.ai/)
- [OpenWebUI GitHub](https://github.com/open-webui/open-webui)
- [RAG Wiki Documentation](../README_SIMPLIFIE.md)

---

**Version:** 1.0.0  
**Modèles:** Mistral Large (LLM) + Mistral Embed (Embeddings)  
**Licence:** MIT
"""
        
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(doc_content)
        
        print(f"  ✓ Documentation: {doc_path}")


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Setup OpenWebUI pour RAG Wiki",
    )
    
    parser.add_argument(
        "--vault",
        type=str,
        default=None,
        help="Chemin du vault par défaut",
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Dossier de sortie pour les fichiers générés",
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Écraser les fichiers existants",
    )
    
    args = parser.parse_args()
    
    # Initialiser le setup
    setup = OpenWebUISetup(
        vault_path=args.vault,
        output_dir=args.output,
    )
    
    # Générer tout
    setup.generate_all()


if __name__ == "__main__":
    main()
