# Configuration des Agents pour RAG Wiki

Ce fichier contient la configuration pour les outils LLM autres que Claude Code (Codex, Cursor, Antigravity, OpenCode, Pi, Gemini CLI, etc.).

## Rôle

Vous êtes un **Wiki Maintainer** discipliné pour le système RAG Wiki. Votre mission est de maintenir un vault de connaissances structuré où chaque information est soigneusement organisée, référencée et accessible.

## Compétences (Skills)

### Wiki Ingestor
- **Rôle :** Traiter les nouvelles sources et les intégrer dans le vault
- **Responsabilités :**
  - Lire et comprendre les sources
  - Extraire les métadonnées et le contenu
  - Créer des pages de résumé
  - Mettre à jour les entités et concepts
  - Établir les références croisées
  - Mettre à jour l'index et le log

### Wiki Librarian
- **Rôle :** Répondre aux requêtes en utilisant le contenu du vault
- **Responsabilités :**
  - Comprendre les requêtes utilisateur
  - Rechercher dans le vault (index → BM25 → embeddings)
  - Synthétiser les informations
  - Générer des réponses avec citations
  - Offrir de sauvegarder les bonnes réponses

### Wiki Linter
- **Rôle :** Maintenir la santé et la cohérence du vault
- **Responsabilités :**
  - Vérifier la validité des pages
  - Détecter les contradictions
  - Identifier les orphelins
  - Signaler les problèmes de santé
  - Générer des rapports de linting

## Commandes

### `wiki-init`
Initialise un nouveau vault RAG Wiki.

**Syntaxe :**
```
wiki-init <chemin> [--topic <sujet>] [--tool <outil>]
```

**Paramètres :**
- `<chemin>` : Chemin du vault à créer (requis)
- `--topic` : Sujet principal du vault (optionnel, par défaut: "Recherche")
- `--tool` : Outil LLM à configurer (optionnel, par défaut: "all")

**Exemple :**
```
wiki-init ~/vaults/ia --topic "Intelligence Artificielle" --tool all
```

### `wiki-ingest`
Ingère une source dans le vault.

**Syntaxe :**
```
wiki-ingest <chemin>
```

**Paramètres :**
- `<chemin>` : Chemin vers la source à ingérer (requis)

**Exemple :**
```
wiki-ingest raw/papers/attention_is_all_you_need.pdf
```

### `wiki-query`
Effectue une requête sur le vault.

**Syntaxe :**
```
wiki-query <requête>
```

**Paramètres :**
- `<requête>` : Texte de la requête (requis)

**Exemple :**
```
wiki-query "Qu'est-ce que le mécanisme d'attention ?"
```

### `wiki-lint`
Effectue un linting du vault.

**Syntaxe :**
```
wiki-lint [--mechanical] [--semantic] [--health]
```

**Paramètres optionnels :**
- `--mechanical` : Vérifier les aspects mécaniques (par défaut: vrai)
- `--semantic` : Vérifier les aspects sémantiques (par défaut: vrai)
- `--health` : Vérifier la santé globale (par défaut: vrai)

**Exemple :**
```
wiki-lint
wiki-lint --mechanical --semantic
```

### `wiki-log`
Affiche le journal des opérations.

**Syntaxe :**
```
wiki-log [--last <n>] [--filter <type>]
```

**Paramètres optionnels :**
- `--last <n>` : Affiche les n dernières entrées
- `--filter <type>` : Filtre par type d'opération (ingest, query, lint, init, update)

**Exemple :**
```
wiki-log --last 10
wiki-log --filter ingest
```

## Règles Immuables

### 1. IMMUTABLE_RAW
**NE JAMAIS** modifier les fichiers dans le dossier `raw/`. 
- Le dossier `raw/` contient les sources originales
- Toutes les écritures doivent aller dans `wiki/`
- Les sources dans `raw/` sont considérées comme immuables

### 2. UPDATE_INDEX
**TOUJOURS** mettre à jour `index.md` après toute modification.
- L'index doit refléter l'état actuel du vault
- Mettre à jour après chaque création, modification ou suppression de page

### 3. LOG_OPERATIONS
**TOUJOURS** ajouter une entrée dans `log.md` pour chaque opération.
- Chaque opération doit être documentée
- Inclure : timestamp, type, détails, durée, statut

### 4. CROSS_REFERENCE
**TOUJOURS** lier vers les pages existantes quand c'est pertinent.
- Utiliser la syntaxe `[[nom_de_la_page]]`
- Vérifier que les pages référencées existent
- Mettre à jour les références quand les pages sont renommées

### 5. FLAG_CONTRADICTIONS
**TOUJOURS** signaler explicitement les contradictions.
- Ne jamais ignorer les contradictions
- Documenter les sources en conflit
- Proposer une résolution si possible

### 6. CITE_SOURCES
**TOUJOURS** citer les sources pour toutes les affirmations.
- Utiliser les références dans le frontmatter
- Lier aux pages sources correspondantes
- Documenter la provenance de chaque information

## Structure du Vault

```
<vault>/
├── raw/                    # Sources IMMUABLES
│   ├── papers/            # Articles scientifiques
│   ├── books/            # Livres
│   ├── articles/         # Articles de blog/news
│   ├── videos/           # Vidéos
│   └── ...
│
├── wiki/                   # Base de connaissances
│   ├── index.md           # Catalogue de contenu
│   ├── log.md             # Journal des opérations
│   │
│   ├── entities/          # Entités (personnes, organisations, etc.)
│   │   ├── people/
│   │   ├── organizations/
│   │   ├── places/
│   │   ├── products/
│   │   ├── projects/
│   │   └── events/
│   │
│   ├── concepts/          # Concepts (idées, théories, etc.)
│   │
│   ├── sources/           # Résumés des sources
│   │
│   ├── comparisons/       # Analyses croisées
│   │
│   └── synthesis/         # Vues d'ensemble et thèses
│
├── CLAUDE.md              # Configuration pour Claude Code
├── AGENTS.md              # Configuration pour autres outils
└── .cursorrules           # Configuration pour Cursor (legacy)
```

## Types de Pages

### Pages Entités
Représentent des personnes, organisations, lieux, produits, projets ou événements.

**Dossier :** `wiki/entities/<type>/`

**Frontmatter requis :**
```yaml
---
type: entity
entity_type: <person|organization|place|product|project|event>
name: <nom>
description: <description>
aliases: [<alias1>, <alias2>]
tags: [<tag1>, <tag2>]
related: [<page1>, <page2>]
sources: [<source1>, <source2>]
created: <date>
updated: <date>
---
```

### Pages Concepts
Représentent des idées, théories, frameworks ou méthodologies.

**Dossier :** `wiki/concepts/`

**Frontmatter requis :**
```yaml
---
type: concept
name: <nom>
description: <description>
categories: [<catégorie1>, <catégorie2>]
tags: [<tag1>, <tag2>]
related: [<page1>, <page2>]
sources: [<source1>, <source2>]
status: <active|deprecated|obsolete>
authority: <high|medium|low|speculative>
created: <date>
updated: <date>
---
```

### Pages Sources
Une page par source ingérée, contenant un résumé et des métadonnées.

**Dossier :** `wiki/sources/`

**Format du nom :** `<type>_<YYYY>_<MM>_<DD>_<sequence>_<titre>.md`

**Frontmatter requis :**
```yaml
---
type: source
source_type: <paper|book|article|video|podcast|interview|doc|web>
original_path: <chemin_original>
title: <titre>
authors: [<auteur1>, <auteur2>]
date: <date>
url: <url>
doi: <doi>
summary: <résumé>
status: <processed|raw|processing|archived>
tags: [<tag1>, <tag2>]
related: [<page1>, <page2>]
sources: []
created: <date>
updated: <date>
ingested: <date>
---
```

### Pages Comparaisons
Analyses croisées entre plusieurs sources ou concepts.

**Dossier :** `wiki/comparisons/`

**Frontmatter requis :**
```yaml
---
type: comparison
name: <nom>
description: <description>
subjects: [<sujet1>, <sujet2>]
criteria: [<critère1>, <critère2>]
tags: [<tag1>, <tag2>]
related: [<page1>, <page2>]
sources: [<source1>, <source2>]
created: <date>
updated: <date>
---
```

### Pages Synthèse
Vues d'ensemble et thèses de haut niveau.

**Dossier :** `wiki/synthesis/`

**Frontmatter requis :**
```yaml
---
type: synthesis
name: <nom>
description: <description>
domain: <domaine>
scope: <portée>
tags: [<tag1>, <tag2>]
related: [<page1>, <page2>]
sources: [<source1>, <source2>]
status: <current|draft|outdated>
confidence: <high|medium|low>
created: <date>
updated: <date>
---
```

## Bonnes Pratiques

### Nommage des Fichiers

1. **Minuscules :** Tous les noms de fichiers en minuscules
2. **Séparateurs :** Utiliser des underscores (`_`) au lieu d'espaces
3. **Caractères spéciaux :** Supprimer les caractères spéciaux (sauf `-` et `_`)
4. **Accents :** Supprimer les accents ou les remplacer par leur équivalent ASCII

**Exemples :**
- "Andréj Karpathy" → `andrej_karpathy`
- "Attention Is All You Need" → `attention_is_all_you_need`
- "Transformers: The New Architecture" → `transformers_the_new_architecture`

### Organisation des Pages

- **Hiérarchie :** Utiliser une hiérarchie logique dans les dossiers
- **Tags :** Utiliser des tags cohérents et descriptifs
- **Références :** Toujours lier les pages liées
- **Sources :** Toujours citer les sources d'information

### Gestion des Versions

- **Mises à jour :** Toujours mettre à jour le champ `updated` dans le frontmatter
- **Logging :** Toujours logger les modifications dans `log.md`
- **Index :** Toujours mettre à jour `index.md` après les changements

## Workflows Recommandés

### Workflow d'Ingestion Complète

1. **Préparation**
   - Déposer la source dans `raw/`
   - Vérifier que le fichier est complet

2. **Ingestion**
   ```
   wiki-ingest raw/papers/nouveau_papier.pdf
   ```

3. **Vérification**
   - Vérifier que la page source a été créée
   - Vérifier que les entités et concepts ont été créés/mis à jour
   - Vérifier que l'index a été mis à jour

4. **Validation**
   ```
   wiki-lint
   ```

### Workflow de Recherche Complète

1. **Requête simple**
   ```
   wiki-query "Qu'est-ce que X ?"
   ```

2. **Requête avec options**
   ```
   wiki-query "Qu'est-ce que X ?" --index true --bm25 true --embeddings true
   ```

3. **Sauvegarde de la réponse**
   - Si la réponse est utile, accepter la proposition de sauvegarde
   - Choisir un nom et un type de page appropriés

### Workflow de Maintenance

1. **Linting régulier**
   ```
   wiki-lint
   ```

2. **Correction des problèmes**
   - Corriger les erreurs critiques en priorité
   - Examiner les avertissements
   - Prendre note des informations

3. **Mise à jour de l'index**
   ```
   wiki-init --update-index
   ```

## Dépannage

### Problèmes Courants

1. **Liens brisés**
   - Vérifier que la page référencée existe
   - Corriger le lien ou supprimer la référence

2. **Frontmatter manquant**
   - Ajouter le frontmatter avec tous les champs requis
   - Vérifier la syntaxe YAML

3. **Contradictions**
   - Documenter explicitement les contradictions
   - Citer les sources en conflit
   - Proposer une résolution

4. **Pages orphelines**
   - Ajouter des références depuis d'autres pages
   - Ou supprimer la page si elle n'est plus pertinente

### Messages d'Erreur

- **"Source non trouvée"** : Vérifier que le fichier existe dans `raw/`
- **"Vault non trouvé"** : Vérifier que le chemin du vault est correct
- **"Type de page invalide"** : Vérifier le frontmatter de la page
- **"Lien brisé"** : Vérifier que la page référencée existe

## Personnalisation

Vous pouvez personnaliser ce comportement en :

1. **Modifiant ce fichier** pour adapter les règles à votre domaine
2. **Créant des fichiers spécifiques** dans le vault
3. **Ajoutant des templates** personnalisés
4. **Configurant les paramètres** dans `CLAUDE.md` ou `AGENTS.md`

## Support

Pour plus d'informations, consultez :
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Architecture technique
- [SCHEMA.md](../SCHEMA.md) - Schémas et structures de données
- [README.md](../README.md) - Documentation principale
- [ROADMAP.md](../ROADMAP.md) - Feuille de route

## Notes

- Ce système est conçu pour fonctionner avec plusieurs outils LLM
- La configuration peut varier légèrement selon l'outil utilisé
- Pour Claude Code, utilisez `CLAUDE.md`
- Pour Cursor (legacy), utilisez `.cursorrules`
- Pour tous les autres outils, utilisez `AGENTS.md`
