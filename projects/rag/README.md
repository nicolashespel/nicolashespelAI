# RAG Wiki - Système de Connaissance Compounding

> **Un second cerveau pour Claude Code + Obsidian**
> Inspiré par [llm-wiki d'Andrej Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) et [llm-wiki-kit](https://github.com/MauricioPerera/llm-wiki-kit)

Transformez n'importe quel LLM CLI en un gestionnaire de wiki discipliné. Vous curatez les sources et posez des questions. Le LLM lit, classe, référence, signale les contradictions et maintient une synthèse vivante. La connaissance **s'accumule** au lieu d'être re-dérivée par RAG à chaque requête.

## L'idée en une phrase

La plupart des workflows LLM+docs sont du RAG : récupération de fragments au moment de la requête, synthèse à partir de zéro, puis oubli. Le wiki est **compounding**. Le LLM lit chaque source une fois et l'intègre dans un vault Obsidian persistant — mettant à jour les pages d'entités, révisant les pages de concepts, signalant les contradictions et renforçant la synthèse. Le wiki est l'artefact compilé ; le RAG est la récupération just-in-time. Ce système donne au LLM la discipline (SKILL.md), la délégation (sous-agents), les déclencheurs (commandes slash) et la gestion (outils Python) pour accomplir le travail.

## Ce qui est inclus

| Composant | Description |
|---|---|
| **SKILL.md** | Document de compétence principal — architecture, workflows, règles immuables, compatibilité multi-outils |
| **3 sous-agents** | `wiki_ingestor`, `wiki_librarian`, `wiki_linter` |
| **5 commandes slash** | `/wiki-init`, `/wiki-ingest`, `/wiki-query`, `/wiki-lint`, `/wiki-log` |
| **8 scripts Python** | Bibliothèque standard uniquement : `init_vault`, `ingest_source`, `update_index`, `append_log`, `wiki_search` (BM25), `lint_wiki`, `graph_analyzer`, `export_marp` |
| **8 documents de référence** | Schéma, formats de pages, workflows ingest/query/lint, configuration Obsidian, configuration multi-outils, principes Memex |
| **Templates de vault** | `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `index.md`, `log.md`, plus 5 templates de pages (entité, concept, source, comparaison, synthèse) |
| **Vault exemple** | Un petit exemple fonctionnel sur "l'interprétabilité des LLM" |

## Architecture en trois couches de récupération

1. **Recherche dans les index** (grep) - Rapide, sur les fichiers index
2. **BM25 sur les pages** - Recherche textuelle avancée
3. **Embeddings sur les pages** - Recherche sémantique

## Quick Start

```bash
# 1. Initialiser un vault
python projects/rag/scripts/init_vault.py --path ~/vaults/recherche --topic "Interprétabilité des LLM" --tool all

# 2. Ouvrir dans Obsidian
open -a Obsidian ~/vaults/recherche

# 3. Déposer une source dans raw/ et l'ingérer
cp ~/Téléchargements/paper.pdf ~/vaults/recherche/raw/papers/
cd ~/vaults/recherche
# dans Claude Code:
> /wiki-ingest raw/papers/paper.pdf

# 4. Poser des questions
> /wiki-query "que dit le papier sur les features sparse ?"

# 5. Vérification de santé
> /wiki-lint
```

## Compatibilité multi-outils

Les scripts sont en Python stdlib pur — ils fonctionnent partout. Seul le **chargeur de schéma** change selon l'outil :

| Outil | Fichier de configuration |
|---|---|
| Claude Code | `CLAUDE.md` |
| Codex CLI (OpenAI) | `AGENTS.md` |
| Cursor (moderne) | `AGENTS.md` |
| Cursor (legacy) | `.cursorrules` |
| Antigravity (Google) | `AGENTS.md` |
| OpenCode / Pi | `AGENTS.md` |
| Gemini CLI | `AGENTS.md` |

`init_vault.py --tool all` installe tous les fichiers. Vous pouvez exécuter plusieurs CLIs contre le même vault.

Voir `projects/rag/docs/cross-tool-setup.md` pour les instructions par outil.

## Structure du Vault

```
<vault>/
├── raw/                    # Sources IMMUABLES (vous possédez)
├── wiki/                   # Base de connaissances gérée par le LLM
│   ├── index.md            # Catalogue de contenu
│   ├── log.md              # Timeline append-only
│   ├── entities/           # Personnes, organisations, lieux, produits
│   ├── concepts/           # Idées, théories, frameworks
│   ├── sources/            # Une page de résumé par source ingérée
│   ├── comparisons/        # Analyses inter-sources
│   └── synthesis/          # Vues d'ensemble et thèses de haut niveau
├── CLAUDE.md               # Schéma pour Claude Code
├── AGENTS.md               # Schéma pour Codex/Cursor/Antigravity
└── .cursorrules            # (optionnel) Cursor legacy
```

**Règle immuable :** Le LLM n'édite jamais `raw/`. Toutes les écritures vont dans `wiki/`.

## Trois opérations principales

- **Ingest** — Lire une source, discuter avec l'utilisateur, écrire une page de résumé, mettre à jour 5-15 pages référencées, mettre à jour l'index, la logger
- **Query** — Lire l'index en premier, approfondir dans 3-10 pages, synthétiser la réponse avec citations inline, proposer de la sauvegarder comme nouvelle page
- **Lint** — Vérification mécanique + sémantique ; surfacer les contradictions, orphelins, claims obsolètes, lacunes de références croisées

## Pourquoi pas juste du RAG ?

| RAG Classique | LLM Wiki |
|---|---|
| Redécouvre la connaissance à chaque requête | La connaissance s'accumule |
| Les références croisées sont re-calculées à chaque fois | Les références croisées sont pré-écrites et maintenues |
| Les contradictions n'apparaissent que si on demande | Les contradictions sont signalées pendant l'ingest |
| L'exploration disparaît dans l'historique de chat | Les bonnes réponses sont re-fichées comme nouvelles pages |
| Scale via l'infrastructure d'embeddings | Scale via markdown + `index.md` + recherche locale optionnelle |

Le wiki et le RAG ne sont pas opposés — le RAG peut s'asseoir sur le wiki une fois que vous dépassez la recherche index-first.

## Statut

**v0.1.0** — Version initiale. SKILL + 3 agents + 5 commandes + 8 scripts + 8 références + templates de vault complets + vault exemple.

## License

MIT.

## Liens

- [Gist original de Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — le pattern que ce système implémente
- Vannevar Bush, "As We May Think" (1945) — le Memex
- [qmd](https://github.com/tobi/qmd) — recherche hybride locale sur markdown (à utiliser avec ce système lorsque le wiki dépasse `index.md`)
