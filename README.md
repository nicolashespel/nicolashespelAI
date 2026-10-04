# nicolashespelAI

Espace de travail pour mes projets liés à l'IA : RAG, agents, skills et expérimentations.

## Structure

- `docs/` — notes et documentations
- `experiments/` — prototypes et expérimentations
- `projects/` — projets complets
  - [`projects/rag/`](projects/rag/README.md) — **RAG Wiki System** : Système de gestion de connaissances compounding inspiré d'Andrej Karpathy et llm-wiki-kit

## Utilisation avec Vibe

Ce dépôt est accessible directement depuis Vibe Work : lecture et modification des fichiers, commits, branches, pull requests et issues se gèrent en conversation.

## Projets Principaux

### 🚀 RAG Wiki System

**Description :** Système de gestion de connaissances compounding pour LLM, inspiré par [llm-wiki d'Andrej Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) et [llm-wiki-kit](https://github.com/MauricioPerera/llm-wiki-kit).

**Fonctionnalités :**
- Ingestion de sources (PDF, HTML, Markdown, texte)
- Requêtes avec récupération en couches (index → BM25 → embeddings)
- Linting et validation du vault
- Gestion de connaissances structurée avec Obsidian
- Compatibilité multi-outils (Claude Code, Codex, Cursor, etc.)

**Structure :**
```
projects/rag/
├── README.md              # Documentation principale
├── ARCHITECTURE.md        # Architecture technique
├── SCHEMA.md              # Schémas et structures
├── docs/                 # Documentation complète
│   ├── CLAUDE.md          # Configuration pour Claude Code
│   ├── AGENTS.md          # Configuration pour autres outils
│   ├── SKILL.md           # Compétences et règles
│   └── ROADMAP.md         # Feuille de route
├── src/                  # Code source Python
│   ├── core/              # Moteur principal
│   ├── agents/            # Agents spécialisés
│   ├── storage/           # Gestion du stockage
│   ├── retrieval/         # Services de récupération
│   ├── indexes/           # Gestion des index
│   ├── sources/           # Parsers de sources
│   ├── pages/             # Gestion des pages
│   ├── types/             # Types et modèles
│   └── utils/             # Utilitaires
├── scripts/              # Scripts CLI
│   ├── init_vault.py      # Initialisation du vault
│   ├── ingest_source.py   # Ingestion de sources
│   ├── query_wiki.py      # Requêtes sur le vault
│   └── lint_wiki.py       # Linting du vault
├── templates/           # Templates Obsidian
│   └── vault/             # Structure de vault exemple
├── tests/                # Tests
└── examples/             # Exemples
```

**Statut :** v0.1.0 - Version initiale complète

---
Maintenu par [Nicolas Hespel](https://github.com/nicolashespel)
