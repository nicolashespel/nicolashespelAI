# Architecture Technique du Projet RAG Wiki

## Vue d'ensemble

Le système RAG Wiki implémente une architecture en couches pour la gestion de connaissances compounding, combinant les avantages du RAG traditionnel avec une approche structurée de type wiki.

## Diagramme d'Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Interface Utilisateur                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐  │
│  │  Slash      │  │   Python    │  │   Obsidian  │  │  LLM    │  │
│  │  Commands   │  │   Scripts   │  │   Vault     │  │  CLI    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Couche Application                             │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Wiki Engine (Core)                          │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │ │
│  │  │   Ingest    │  │    Query     │  │       Lint           │  │ │
│  │  │   Pipeline   │  │   Pipeline   │  │      Pipeline        │  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Ingestor   │  │  Librarian   │  │   Linter    │              │
│  │   Agent     │  │   Agent      │  │   Agent     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Couche Services                              │
│  ┌─────────────────────┐  ┌─────────────────────┐                  │
│  │   Retrieval          │  │     Indexing         │                  │
│  │   Service            │  │     Service         │                  │
│  │  ┌─────────────┐    │  │  ┌─────────────┐    │                  │
│  │  │  BM25       │    │  │  │  Index      │    │                  │
│  │  └─────────────┘    │  │  │  Builder    │    │                  │
│  │  ┌─────────────┐    │  │  └─────────────┘    │                  │
│  │  │  Embedding  │    │  │                     │                  │
│  │  │  Search    │    │  │                     │                  │
│  │  └─────────────┘    │  │                     │                  │
│  └─────────────────────┘  └─────────────────────┘                  │
│                                                                      │
│  ┌─────────────────────┐  ┌─────────────────────┐                  │
│  │   Source             │  │     Storage          │                  │
│  │   Processing         │  │     Service         │                  │
│  │  ┌─────────────┐    │  │  ┌─────────────┐    │                  │
│  │  │  PDF        │    │  │  │  Vault      │    │                  │
│  │  │  Parser     │    │  │  │  Manager    │    │                  │
│  │  └─────────────┘    │  │  └─────────────┘    │                  │
│  │  ┌─────────────┐    │  │                     │                  │
│  │  │  HTML       │    │  │                     │                  │
│  │  │  Parser     │    │  │                     │                  │
│  │  └─────────────────────┘  └─────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Couche Données                               │
│  ┌─────────────────────┐  ┌─────────────────────┐                  │
│  │   Vault              │  │    Indexes           │                  │
│  │  ┌─────────────┐    │  │  ┌─────────────┐    │                  │
│  │  │  raw/       │    │  │  │  index.md    │    │                  │
│  │  │             │    │  │  └─────────────┘    │                  │
│  │  └─────────────┘    │  │  ┌─────────────┐    │                  │
│  │  ┌─────────────┐    │  │  │  log.md      │    │                  │
│  │  │  wiki/      │    │  │  └─────────────┘    │                  │
│  │  │  ┌─────────┐│    │  │  ┌─────────────┐    │                  │
│  │  │  │entities/││    │  │  │  BM25 index  │    │                  │
│  │  │  └─────────┘│    │  │  └─────────────┘    │                  │
│  │  │  ┌─────────┐│    │  │  ┌─────────────┐    │                  │
│  │  │  │concepts/││    │  │  │  Embedding  │    │                  │
│  │  │  └─────────┘│    │  │  │  Index     │    │                  │
│  │  │  ┌─────────┐│    │  │  └─────────────┘    │                  │
│  │  │  │sources/ ││    │  │                     │                  │
│  │  │  └─────────┘│    │  │                     │                  │
│  │  │  ┌─────────┐│    │  │                     │                  │
│  │  │  │comparisons/│    │  │                     │                  │
│  │  │  └──────────┘│    │  │                     │                  │
│  │  │  ┌─────────┐│    │  │                     │                  │
│  │  │  │synthesis/││    │  │                     │                  │
│  │  │  └─────────┘│    │  │                     │                  │
│  │  └─────────────┘    │  │                     │                  │
│  └─────────────────────┘  └─────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

## Structure des Modules

### 1. Module Core (`src/core/`)

Le cœur du système contient les pipelines principaux :

```
src/core/
├── __init__.py          # Exports principaux
├── wiki_engine.py       # Classe WikiEngine principale
├── ingest_pipeline.py   # Pipeline d'ingestion
├── query_pipeline.py    # Pipeline de requête
├── lint_pipeline.py     # Pipeline de linting
├── prompts.py           # Prompts système pour les agents
└── config.py            # Configuration centrale
```

**Responsabilités :**
- Orchestration des workflows
- Gestion des pipelines
- Coordination entre services
- Configuration centrale

### 2. Module Agents (`src/agents/`)

Les agents spécialisés pour différentes tâches :

```
src/agents/
├── __init__.py
├── base_agent.py        # Classe de base pour tous les agents
├── wiki_ingestor.py     # Agent d'ingestion
├── wiki_librarian.py    # Agent bibliothécaire
└── wiki_linter.py       # Agent de linting
```

**Responsabilités :**
- Implémentation des comportements spécifiques
- Interaction avec le LLM
- Exécution des tâches spécialisées

### 3. Module Retrieval (`src/retrieval/`)

Services de récupération d'information :

```
src/retrieval/
├── __init__.py
├── base_retriever.py    # Interface de base
├── bm25_retriever.py   # Implémentation BM25
├── embedding_retriever.py # Implémentation par embeddings
└── hybrid_retriever.py  # Combinaison des approches
```

**Responsabilités :**
- Recherche dans les index
- Recherche sémantique
- Fusion des résultats (RRF)

### 4. Module Indexes (`src/indexes/`)

Gestion des index :

```
src/indexes/
├── __init__.py
├── index_builder.py     # Construction des index
├── index_manager.py     # Gestion des index
├── bm25_index.py        # Index BM25
└── embedding_index.py    # Index d'embeddings
```

**Responsabilités :**
- Construction et mise à jour des index
- Maintenance des structures de données
- Optimisation des performances

### 5. Module Sources (`src/sources/`)

Traitement des sources :

```
src/sources/
├── __init__.py
├── base_parser.py       # Parser de base
├── pdf_parser.py        # Parser PDF
├── html_parser.py       # Parser HTML
├── md_parser.py         # Parser Markdown
└── txt_parser.py        # Parser texte brut
```

**Responsabilités :**
- Extraction de texte
- Nettoyage et normalisation
- Métadonnées des sources

### 6. Module Storage (`src/storage/`)

Gestion du stockage :

```
src/storage/
├── __init__.py
├── vault_manager.py     # Gestion du vault
├── file_manager.py      # Gestion des fichiers
└── git_manager.py       # Gestion Git (optionnelle)
```

**Responsabilités :**
- Accès aux fichiers
- Gestion des chemins
- Intégration Git (si disponible)

### 7. Module Pages (`src/pages/`)

Gestion des pages wiki :

```
src/pages/
├── __init__.py
├── page_factory.py      # Création de pages
├── page_parser.py       # Analyse des pages
├── templates.py         # Templates de pages
└── validators.py        # Validation des pages
```

**Responsabilités :**
- Création de pages structurées
- Analyse et parsing
- Validation des schémas

### 8. Module Types (`src/types/`)

Définitions des types :

```
src/types/
├── __init__.py
├── models.py            # Modèles de données
├── schemas.py           # Schémas Pydantic
└── enums.py             # Énumérations
```

**Responsabilités :**
- Définition des types de données
- Validation des structures
- Documentation des schémas

### 9. Module Utils (`src/utils/`)

Utilitaires divers :

```
src/utils/
├── __init__.py
├── logging.py           # Configuration du logging
├── text_utils.py        # Utilitaires texte
├── path_utils.py        # Utilitaires de chemins
└── date_utils.py        # Utilitaires de dates
```

## Flux de Données

### Pipeline d'Ingestion

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Source  │────▶│   Parser    │────▶│  Ingestor   │────▶│   Vault     │
│ (PDF/MD)│     │             │     │   Agent     │     │             │
└─────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                      │
                                                      ▼
┌─────────────────────────────────────────────────────────────┐
│                        Mises à jour                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Summary    │  │  Index       │  │    Cross-references   │  │
│  │  Page       │  │  Update      │  │    Update            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Pipeline de Requête

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Query     │────▶│  Retriever   │────▶│  Librarian  │
│              │     │             │     │   Agent     │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Synthèse                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Index      │  │  Pages      │  │    Answer with        │  │
│  │  Search     │  │  Search     │  │    Citations          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Pipeline de Linting

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Vault     │────▶│  Linter     │────▶│   Report    │
│             │     │   Agent     │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Vérifications                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Mechanical │  │  Semantic    │  │    Contradictions    │  │
│  │  Checks     │  │  Checks     │  │    Detection         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Intégration avec les Outils LLM

### Architecture des Adapters

```
┌─────────────────────────────────────────────────────────────┐
│                    Interface LLM Adapter                         │
├─────────────────────────────────────────────────────────────┤
│  + query(prompt: str, context: list) -> str                      │
│  + stream(prompt: str, context: list) -> Iterator[str]           │
│  + embed(text: str) -> list[float]                               │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Claude Code  │    │   Codex CLI   │    │   Cursor      │
│  Adapter      │    │   Adapter      │    │   Adapter     │
└───────────────┘    └───────────────┘    └───────────────┘
```

### Chargement des Schémas

Chaque outil utilise un fichier de configuration différent pour charger les schémas :

- **Claude Code** : `CLAUDE.md`
- **Codex/Cursor/Antigravity/OpenCode/Gemini** : `AGENTS.md`
- **Cursor (legacy)** : `.cursorrules`

Le système de configuration détecte automatiquement l'outil utilisé et charge le bon fichier.

## Gestion des Dépendances

### Dépendances Principales

- **Python 3.12+** : Langage principal
- **Bibliothèque standard** : Pas de dépendances externes pour le cœur
- **Optionnel** :
  - `pypdf` : Pour le parsing PDF
  - `beautifulsoup4` : Pour le parsing HTML
  - `rank-bm25` : Pour l'implémentation BM25
  - `sentence-transformers` : Pour les embeddings

### Structure des Requirements

```
projects/rag/requirements.txt          # Dépendances principales
projects/rag/requirements-dev.txt      # Dépendances de développement
projects/rag/requirements-optional.txt # Dépendances optionnelles
```

## Patterns de Conception

### 1. Pattern Strategy

Utilisé pour les différents parsers de sources et les méthodes de récupération.

### 2. Pattern Factory

Utilisé pour la création des pages et des index.

### 3. Pattern Observer

Utilisé pour les mises à jour des index et la notification des changements.

### 4. Pattern Singleton

Utilisé pour la configuration centrale et le gestionnaire de vault.

### 5. Pattern Adapter

Utilisé pour l'intégration avec différents outils LLM.

## Bonnes Pratiques

### 1. Gestion des Erreurs

- Utiliser des exceptions personnalisées
- Fournir des messages d'erreur clairs
- Logger toutes les erreurs

### 2. Logging

- Niveau DEBUG pour le développement
- Niveau INFO pour l'utilisation normale
- Niveau WARNING pour les problèmes
- Niveau ERROR pour les erreurs critiques

### 3. Tests

- Tests unitaires pour chaque module
- Tests d'intégration pour les pipelines
- Tests de bout en bout pour les workflows complets

### 4. Documentation

- Docstrings en français pour toutes les fonctions publiques
- Commentaires pour le code complexe
- Documentation dans le dossier `docs/`

## Performances

### Optimisations

- Cache des index en mémoire
- Lazy loading des embeddings
- Batch processing pour les opérations d'ingestion
- Parallel processing pour les recherches

### Benchmarks

- Mesures de temps d'exécution
- Mesures de consommation mémoire
- Tests de charge pour les grands vaults

## Sécurité

### Bonnes Pratiques

- Validation de toutes les entrées
- Sanitization des chemins de fichiers
- Gestion sécurisée des erreurs
- Pas de secrets dans le code

### Configuration

- Fichiers `.env` pour les secrets
- Validation des configurations
- Permissions minimales

## Évolutivité

### Scaling Horizontal

- Architecture modulaire
- Services indépendants
- Possibilité de distribution

### Scaling Vertical

- Optimisation des index
- Cache agressif
- Batch processing

## Maintenance

### Versioning

- Versioning sémantique
- Changelog détaillé
- Compatibilité ascendante

### Monitoring

- Métriques de performance
- Health checks
- Alertes pour les erreurs

### Documentation

- Documentation complète
- Exemples d'utilisation
- Guides de dépannage
