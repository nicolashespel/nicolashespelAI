# RAG Wiki - Guide Simplifié

> **Système de Connaissance Compounding avec Mistral**
> Une version simplifiée et optimisée pour OpenWebUI et les interfaces graphiques.

## 🎯 Objectif

Ce guide vous permet de configurer et utiliser rapidement le système RAG Wiki avec **Mistral** (LLM + Embeddings) via des interfaces comme OpenWebUI, sans avoir besoin d'utiliser le terminal.

## 🚀 Installation Rapide

### 1. Prérequis
- Python 3.12+
- Une clé API Mistral (à placer dans la variable d'environnement `MISTRAL_API_KEY`)

### 2. Installation des dépendances
```bash
cd projects/rag
pip install -r requirements.txt
```

### 3. Initialisation du Vault

#### Option A: Utiliser le script simplifié
```bash
python scripts/simple_init.py --path ~/vaults/ma_base --topic "Mon Sujet"
```

#### Option B: Initialisation manuelle
1. Créez un dossier pour votre vault: `mkdir -p ~/vaults/ma_base/{raw,wiki/{entities,concepts,sources,comparisons,synthesis},configs}`
2. Copiez les fichiers de configuration: `cp configs/mistral_config.json ~/vaults/ma_base/configs/`
3. Créez les fichiers initiaux: `index.md` et `log.md` dans `wiki/`

## 📁 Structure du Vault

```
ma_base/
├── raw/                    # Sources IMMUABLES (PDF, documents, etc.)
│   └── papers/             # Exemple: vos articles
├── wiki/                   # Base de connaissances gérée par le LLM
│   ├── index.md            # Catalogue de tout le contenu
│   ├── log.md              # Historique des opérations
│   ├── entities/           # Personnes, organisations, lieux
│   ├── concepts/           # Idées, théories, frameworks
│   ├── sources/            # Résumés des sources ingérées
│   ├── comparisons/        # Analyses entre sources
│   └── synthesis/          # Vues d'ensemble
├── configs/                # Configurations
│   ├── mistral_config.json # Configuration Mistral
│   └── openwebui_config.json # Configuration simplifiée
├── CLAUDE.md               # Pour Claude Code
└── AGENTS.md               # Pour Codex, Cursor, etc.
```

## 🎮 Utilisation avec OpenWebUI

### Configuration dans OpenWebUI

1. **Ajoutez un nouvel outil personnalisé:**
   - Nom: `RAG Wiki`
   - Commande: `python /chemin/vers/projects/rag/rag_cli.py`
   - Arguments: `{query}`

2. **Ou utilisez les commandes directement:**
   - `/wiki-init` - Initialiser un vault
   - `/wiki-ingest chemin/vers/fichier.pdf` - Ingest une source
   - `/wiki-query "Votre question"` - Poser une question
   - `/wiki-lint` - Vérifier la cohérence du vault
   - `/wiki-status` - Voir les statistiques
   - `/wiki-log` - Voir l'historique

### Exemples de commandes

```
/wiki-init
/wiki-ingest ~/vaults/ma_base/raw/papers/article.pdf
/wiki-query "Quels sont les principaux concepts de l'article ?"
/wiki-lint
/wiki-status
```

## 🔧 Configuration

### Modèles utilisés
- **LLM Principal:** `mistral-large-latest`
- **Embeddings:** `mistral-embed` (1024 dimensions)
- **Modèle Économique:** `mistral-small-latest` (pour le linting)

### Fichier de configuration principal

Le fichier `configs/mistral_config.json` contient toute la configuration:

```json
{
  "global": {
    "api_base_url": "https://api.mistral.ai/v1",
    "timeout_seconds": 120,
    "max_retries": 3
  },
  "llm": {
    "default": {
      "model": "mistral-large-latest",
      "temperature": 0.3,
      "max_tokens": 8192
    }
  },
  "embeddings": {
    "model": "mistral-embed",
    "dimension": 1024,
    "batch_size": 32
  }
}
```

### Variables d'environnement

Créez un fichier `.env` dans le dossier du projet:

```bash
# Clé API Mistral
MISTRAL_API_KEY=votre_cle_api_ici

# Configuration optionnelle
WIKI_VAULT_PATH=~/vaults/knowledge_base
WIKI_LLM_MODEL=mistral-large-latest
WIKI_EMBEDDING_MODEL=mistral-embed
```

## 📚 Workflows Principaux

### 1. Ingestion d'une nouvelle source

1. Placez votre fichier (PDF, document, etc.) dans `raw/`
2. Exécutez: `/wiki-ingest raw/votre_fichier.pdf`
3. Le système:
   - Extrait le texte
   - Crée une page source dans `wiki/sources/`
   - Met à jour les entités et concepts
   - Met à jour l'index
   - Ajoute une entrée dans le log

### 2. Poser une question

1. Exécutez: `/wiki-query "Votre question ici"`
2. Le système:
   - Cherche dans l'index
   - Effectue une recherche BM25
   - Effectue une recherche sémantique avec embeddings
   - Fusionne les résultats
   - Génère une réponse avec citations

### 3. Vérification de cohérence

1. Exécutez: `/wiki-lint`
2. Le système vérifie:
   - La validité du frontmatter
   - Les liens internes
   - Les références
   - Les contradictions
   - Les pages orphelines

## 🎯 Bonnes Pratiques

### Organisation des fichiers
- **Une source = un fichier** dans `raw/`
- **Une page wiki = un concept/entité**
- **Toujours citer les sources** avec `[[nom_de_la_page]]`

### Nommage des pages
- **Sources:** `source_YYYY_MM_DD_NNN_titre.md`
- **Entités:** `nom_entite.md`
- **Concepts:** `nom_concept.md`
- **Comparaisons:** `comparaison_sujet1_sujet2.md`
- **Synthèses:** `synthese_sujet.md`

### Frontmatter minimal

Toutes les pages wiki doivent commencer par un frontmatter YAML:

```yaml
---
type: concept  # ou: source, entity, comparison, synthesis
title: Titre de la page
description: Description courte
tags: [tag1, tag2]
related: [page1, page2]  # Pages liées
sources: [source1, source2]  # Sources de référence
created: 2024-01-01
updated: 2024-01-01
---
```

## 🔄 Mise à jour et Maintenance

### Ajouter un nouveau type de source
1. Placez le fichier dans `raw/`
2. Le système le traitera automatiquement

### Mettre à jour la configuration
1. Modifiez `configs/mistral_config.json`
2. Redémarrez votre interface

### Nettoyer le vault
1. Exécutez `/wiki-lint` pour identifier les problèmes
2. Corrigé les liens brisés
3. Supprimez les pages orphelines

## 📊 Commandes de base

| Commande | Description | Exemple |
|----------|-------------|---------|
| `/wiki-init` | Initialiser un vault | `/wiki-init` |
| `/wiki-ingest` | Ingest une source | `/wiki-ingest raw/article.pdf` |
| `/wiki-query` | Poser une question | `/wiki-query "Qu'est-ce que X ?"` |
| `/wiki-lint` | Vérifier le vault | `/wiki-lint` |
| `/wiki-log` | Voir l'historique | `/wiki-log` |
| `/wiki-status` | Voir les stats | `/wiki-status` |
| `/wiki-preprocess` | Prétraiter un fichier | `/wiki-preprocess raw/doc.pdf` |
| `/wiki-batch` | Ingest plusieurs fichiers | `/wiki-batch raw/file1.pdf raw/file2.pdf` |
| `/wiki-help` | Aide | `/wiki-help` |

## 🛠️ Dépannage

### Problème: La commande n'est pas reconnue
- Vérifiez que le chemin vers `rag_cli.py` est correct
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

## 📚 Documentation Complète

Pour plus de détails, consultez:
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Architecture technique
- [SCHEMA.md](./SCHEMA.md) - Schéma des données
- [docs/](./docs/) - Documentation détaillée

## 🎉 Exemple Complet

### 1. Initialisation
```bash
python scripts/simple_init.py --path ~/vaults/recherche_ia --topic "Recherche en IA"
```

### 2. Ajout d'une source
```bash
cp ~/Téléchargements/article_ia.pdf ~/vaults/recherche_ia/raw/
python rag_cli.py /wiki-ingest raw/article_ia.pdf
```

### 3. Poser une question
```bash
python rag_cli.py /wiki-query "Quels sont les principaux défis de l'IA selon l'article ?"
```

### 4. Vérification
```bash
python rag_cli.py /wiki-lint
python rag_cli.py /wiki-status
```

## 📝 Notes Importantes

1. **Ne modifiez jamais** les fichiers dans `raw/` - ils doivent rester immuables
2. **Toujours citez** vos sources dans le contenu wiki
3. **Mettez à jour** régulièrement l'index et le log
4. **Vérifiez** la cohérence avec `/wiki-lint`

## 🔗 Liens Utiles

- [Mistral AI](https://mistral.ai/)
- [Documentation Mistral API](https://docs.mistral.ai/)
- [OpenWebUI](https://github.com/open-webui/open-webui)

---

**Version:** 1.0.0  
**Modèles:** Mistral Large (LLM) + Mistral Embed (Embeddings)  
**Licence:** MIT
