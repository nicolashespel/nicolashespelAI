# SKILL.md - Compétences Principales du RAG Wiki

> **Document de compétence maître pour le système RAG Wiki**
> Version: 1.0.0
> Dernière mise à jour: 2024-01-20

Ce document définit les compétences, workflows, règles immuables et principes de base pour le système RAG Wiki. Il sert de référence centrale pour tous les agents et sous-systèmes.

---

## Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture des Compétences](#architecture-des-compétences)
3. [Règles Immuables](#règles-immuables)
4. [Workflows Principaux](#workflows-principaux)
5. [Compétences des Agents](#compétences-des-agents)
6. [Principes de Conception](#principes-de-conception)
7. [Bonnes Pratiques](#bonnes-pratiques)
8. [Gestion des Erreurs](#gestion-des-erreurs)
9. [Compatibilité Multi-Outils](#compatibilité-multi-outils)

---

## Vue d'ensemble

Le système RAG Wiki implémente une approche **compounding** de la gestion des connaissances, où chaque interaction enrichit la base de connaissances existante plutôt que de redériver les informations à partir de zéro.

### Philosophie

- **Connaissance Accumulée** : La connaissance s'accumule avec le temps
- **Références Pré-établies** : Les connexions sont maintenues explicitement
- **Contradictions Visibles** : Les conflits sont signalés et documentés
- **Exploration Persistante** : Les bonnes réponses sont sauvegardées pour référence future

### Objectifs Principaux

1. **Maintenir une base de connaissances structurée et cohérente**
2. **Faciliter la découverte et la récupération d'informations**
3. **Assurer la traçabilité et la provenance des informations**
4. **Permettre l'évolution et la maintenance à long terme**

---

## Architecture des Compétences

### Hiérarchie des Compétences

```
RAG Wiki System
├── WikiEngine (Core)
│   ├── IngestPipeline
│   │   ├── SourceParser
│   │   ├── EntityExtractor
│   │   ├── ConceptExtractor
│   │   └── CrossReferencer
│   │
│   ├── QueryPipeline
│   │   ├── QueryAnalyzer
│   │   ├── LayeredRetriever
│   │   └── AnswerSynthesizer
│   │
│   └── LintPipeline
│       ├── MechanicalChecker
│       ├── SemanticChecker
│       └── HealthChecker
│
├── WikiIngestor (Agent)
│   ├── SourceReader
│   ├── MetadataExtractor
│   ├── SummaryGenerator
│   └── IntegrationManager
│
├── WikiLibrarian (Agent)
│   ├── QueryUnderstander
│   ├── SearchExecutor
│   ├── AnswerGenerator
│   └── CitationManager
│
└── WikiLinter (Agent)
    ├── FrontmatterValidator
    ├── LinkChecker
    ├── ReferenceValidator
    ├── ContradictionDetector
    └── ReportGenerator
```

### Interactions entre Compétences

```
┌─────────────────────────────────────────────────────────────┐
│                     WikiEngine (Core)                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    Orchestration                           │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  IngestPipeline   │ │  QueryPipeline    │ │   LintPipeline    │
│                  │ │                  │ │                  │
│  1. Parse source │ │  1. Analyze query│ │  1. Check all    │
│  2. Extract info │ │  2. Layered search│ │     pages       │
│  3. Create pages │ │  3. Select pages │ │  2. Validate     │
│  4. Update refs  │ │  4. Synthesize   │ │     structure   │
│  5. Update index │ │  5. Generate ans │ │  3. Detect       │
│  6. Log op      │ │  6. Offer save  │ │     issues      │
└──────────────────┘ └──────────────────┘ └──────────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  WikiIngestor     │ │  WikiLibrarian    │ │   WikiLinter     │
│  (Agent)          │ │  (Agent)         │ │  (Agent)        │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Règles Immuables

### 📋 Liste Complète des Règles

#### Règle 1: IMMUTABLE_RAW
**NE JAMAIS modifier les fichiers dans le dossier `raw/`**

- **Raison :** Le dossier `raw/` contient les sources originales et immuables
- **Conséquence :** Toute modification violerait l'intégrité des données sources
- **Action :** Toujours écrire dans `wiki/` uniquement

#### Règle 2: UPDATE_INDEX
**TOUJOURS mettre à jour `index.md` après toute modification**

- **Raison :** L'index doit refléter l'état actuel du vault
- **Conséquence :** Un index obsolète rend la recherche inefficace
- **Action :** Mettre à jour après chaque création, modification ou suppression

#### Règle 3: LOG_OPERATIONS
**TOUJOURS ajouter une entrée dans `log.md` pour chaque opération**

- **Raison :** Le journal permet de tracer toutes les modifications
- **Conséquence :** L'absence de logging rend le dépannage impossible
- **Action :** Logger chaque opération avec timestamp, type, détails et statut

#### Règle 4: CROSS_REFERENCE
**TOUJOURS lier vers les pages existantes quand c'est pertinent**

- **Raison :** Les références croisées améliorent la navigabilité
- **Conséquence :** L'absence de liens rend le vault fragmenté
- **Action :** Utiliser la syntaxe `[[nom_de_la_page]]` pour les références

#### Règle 5: FLAG_CONTRADICTIONS
**TOUJOURS signaler explicitement les contradictions**

- **Raison :** Les contradictions doivent être visibles pour l'utilisateur
- **Conséquence :** Ignorer les contradictions peut mener à des erreurs
- **Action :** Documenter les sources en conflit et proposer une résolution

#### Règle 6: CITE_SOURCES
**TOUJOURS citer les sources pour toutes les affirmations**

- **Raison :** La traçabilité est essentielle pour la crédibilité
- **Conséquence :** Les affirmations non sourcées sont suspectes
- **Action :** Utiliser les références dans le frontmatter et citer dans le contenu

### Priorités des Règles

1. **Critique (Bloquante)** : IMMUTABLE_RAW, UPDATE_INDEX, LOG_OPERATIONS
2. **Importante** : CROSS_REFERENCE, FLAG_CONTRADICTIONS, CITE_SOURCES
3. **Recommandée** : Toutes les autres bonnes pratiques

---

## Workflows Principaux

### Workflow 1: Ingestion de Source

```
┌─────────────────────────────────────────────────────────────┐
│                    WORKFLOW D'INGESTION                          │
├─────────────────────────────────────────────────────────────┤
│  1. RÉCEPTION                                                   │
│     ├── Vérifier que la source existe dans raw/               │
│     ├── Identifier le type de source                           │
│     └── Vérifier qu'elle n'a pas déjà été ingérée                │
│                                                                 │
│  2. PARSING                                                     │
│     ├── Extraire le texte brut                                  │
│     ├── Nettoyer le contenu                                    │
│     └── Extraire les métadonnées                               │
│                                                                 │
│  3. DISCUSSION (Optionnelle)                                    │
│     ├── Présenter un résumé initial                            │
│     ├── Demander des clarifications                            │
│     └── Obtenir l'approbation de l'utilisateur                 │
│                                                                 │
│  4. CRÉATION DE LA PAGE SOURCE                                 │
│     ├── Générer un identifiant unique                          │
│     ├── Créer la page dans wiki/sources/                       │
│     ├── Ajouter toutes les métadonnées                         │
│     └── Générer un résumé complet                               │
│                                                                 │
│  5. EXTRACTION DES ENTITÉS ET CONCEPTS                        │
│     ├── Identifier les personnes, organisations, etc.         │
│     ├── Identifier les concepts, théories, etc.                │
│     └── Extraire les citations importantes                      │
│                                                                 │
│  6. CRÉATION/MISE À JOUR DES PAGES                              │
│     ├── Créer de nouvelles pages pour les entités/concepts    │
│     ├── Mettre à jour les pages existantes                     │
│     └── Établir les références croisées                        │
│                                                                 │
│  7. MISE À JOUR DE L'INDEX                                     │
│     ├── Mettre à jour index.md                                 │
│     ├── Ajouter les nouvelles pages aux listes                 │
│     └── Mettre à jour les statistiques                          │
│                                                                 │
│  8. LOGGING                                                     │
│     ├── Ajouter une entrée dans log.md                         │
│     └── Documenter toutes les modifications                    │
└─────────────────────────────────────────────────────────────┘
```

### Workflow 2: Requête

```
┌─────────────────────────────────────────────────────────────┐
│                      WORKFLOW DE REQUÊTE                         │
├─────────────────────────────────────────────────────────────┤
│  1. ANALYSE DE LA REQUÊTE                                       │
│     ├── Identifier les mots-clés                               │
│     ├── Déterminer l'intention                                 │
│     └── Déterminer le type de requête                          │
│                                                                 │
│  2. RECHERCHE EN COUCHES                                       │
│     ├── Rechercher dans index.md                               │
│     ├── Effectuer une recherche BM25 sur toutes les pages    │
│     └── Effectuer une recherche par embeddings (si disponible)│
│                                                                 │
│  3. FUSION DES RÉSULTATS                                       │
│     ├── Combiner les résultats des différentes méthodes       │
│     ├── Éliminer les doublons                                  │
│     └── Trier par pertinence                                   │
│                                                                 │
│  4. SÉLECTION DES PAGES                                        │
│     ├── Sélectionner les 3-10 pages les plus pertinentes        │
│     └── Vérifier que les pages existent                         │
│                                                                 │
│  5. SYNTHÈSE DE LA RÉPONSE                                     │
│     ├── Lire les pages sélectionnées                          │
│     ├── Extraire les informations pertinentes                 │
│     └── Générer une réponse cohérente                          │
│                                                                 │
│  6. AJOUT DES CITATIONS                                        │
│     ├── Ajouter des citations inline avec [[nom_de_la_page]]  │
│     └── Vérifier que toutes les affirmations sont sourcées     │
│                                                                 │
│  7. VÉRIFICATION                                               │
│     ├── Vérifier la cohérence de la réponse                    │
│     └── Signaler les contradictions ou incertitudes            │
│                                                                 │
│  8. OFFRE DE SAUVEGARDE                                       │
│     └── Proposer de sauvegarder la réponse comme nouvelle page │
└─────────────────────────────────────────────────────────────┘
```

### Workflow 3: Linting

```
┌─────────────────────────────────────────────────────────────┐
│                       WORKFLOW DE LINTING                         │
├─────────────────────────────────────────────────────────────┤
│  1. VÉRIFICATIONS MÉCANIQUES                                    │
│     ├── Valider le frontmatter de toutes les pages             │
│     ├── Vérifier les liens wiki                               │
│     ├── Vérifier les références                                │
│     └── Vérifier les types de pages                             │
│                                                                 │
│  2. VÉRIFICATIONS SÉMANTIQUES                                   │
│     ├── Détecter les pages orphelines                          │
│     ├── Détecter les contradictions                            │
│     ├── Détecter les affirmations obsolètes                    │
│     └── Détecter les lacunes de références                      │
│                                                                 │
│  3. VÉRIFICATIONS DE SANTÉ                                      │
│     ├── Vérifier que index.md est à jour                       │
│     ├── Vérifier que log.md est valide                          │
│     └── Vérifier les performances du vault                      │
│                                                                 │
│  4. GÉNÉRATION DU RAPPORT                                      │
│     ├── Résumer tous les problèmes détectés                    │
│     ├── Classer les problèmes par gravité                     │
│     └── Proposer des actions correctives                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Compétences des Agents

### WikiIngestor Agent

#### Compétences Principales

1. **Lecture de Sources**
   - Lire les fichiers PDF, HTML, Markdown, texte brut
   - Extraire le texte et les métadonnées
   - Nettoyer et normaliser le contenu

2. **Extraction d'Information**
   - Identifier les entités (personnes, organisations, etc.)
   - Identifier les concepts (idées, théories, etc.)
   - Extraire les citations et références
   - Identifier les relations entre les entités et concepts

3. **Création de Pages**
   - Créer des pages de résumé pour les sources
   - Créer des pages d'entités
   - Créer des pages de concepts
   - Créer des pages de comparaison
   - Créer des pages de synthèse

4. **Gestion des Références**
   - Établir les références croisées
   - Mettre à jour les pages existantes
   - Vérifier la cohérence des références

5. **Intégration**
   - Mettre à jour l'index
   - Logger les opérations
   - Vérifier l'intégrité du vault

#### Niveaux de Compétence

| Niveau | Description | Capacités |
|--------|-------------|-----------|
| 1 | Débutant | Lecture basique, extraction simple |
| 2 | Intermédiaire | Extraction avancée, création de pages |
| 3 | Avancé | Gestion complète des références |
| 4 | Expert | Intégration complète, validation |

### WikiLibrarian Agent

#### Compétences Principales

1. **Compréhension des Requêtes**
   - Analyser les requêtes utilisateur
   - Identifier les mots-clés et l'intention
   - Déterminer le type de réponse attendu

2. **Recherche**
   - Rechercher dans l'index
   - Effectuer des recherches BM25
   - Effectuer des recherches par embeddings
   - Fusionner les résultats

3. **Sélection des Pages**
   - Sélectionner les pages les plus pertinentes
   - Éliminer les doublons
   - Prioriser par pertinence

4. **Synthèse**
   - Lire et comprendre les pages sélectionnées
   - Extraire les informations pertinentes
   - Générer une réponse cohérente
   - Ajouter des citations appropriées

5. **Vérification**
   - Vérifier la cohérence de la réponse
   - Signaler les contradictions
   - Proposer des clarifications

#### Niveaux de Compétence

| Niveau | Description | Capacités |
|--------|-------------|-----------|
| 1 | Débutant | Compréhension basique, recherche simple |
| 2 | Intermédiaire | Recherche avancée, sélection de pages |
| 3 | Avancé | Synthèse cohérente, citations |
| 4 | Expert | Vérification complète, gestion des contradictions |

### WikiLinter Agent

#### Compétences Principales

1. **Vérifications Mécaniques**
   - Valider le frontmatter
   - Vérifier les liens
   - Vérifier les références
   - Vérifier les types de pages
   - Vérifier les tags

2. **Vérifications Sémantiques**
   - Détecter les pages orphelines
   - Détecter les contradictions
   - Détecter les affirmations obsolètes
   - Détecter les lacunes de références

3. **Vérifications de Santé**
   - Vérifier l'index
   - Vérifier le log
   - Vérifier les performances

4. **Génération de Rapports**
   - Résumer les problèmes
   - Classer par gravité
   - Proposer des actions

#### Niveaux de Compétence

| Niveau | Description | Capacités |
|--------|-------------|-----------|
| 1 | Débutant | Vérifications basiques |
| 2 | Intermédiaire | Vérifications avancées |
| 3 | Avancé | Détection de contradictions |
| 4 | Expert | Génération de rapports complets |

---

## Principes de Conception

### 1. Principe de Compounding

La connaissance doit s'accumuler avec le temps. Chaque nouvelle information doit enrichir la base existante plutôt que de remplacer ou de redériver.

**Implémentation :**
- Chaque source est lue une fois
- Les informations sont intégrées dans le vault
- Les connexions sont établies explicitement
- Les contradictions sont signalées

### 2. Principe de Traçabilité

Toute information doit être traçable jusqu'à sa source.

**Implémentation :**
- Toutes les pages ont des métadonnées de source
- Toutes les affirmations sont citées
- Toutes les modifications sont loggées

### 3. Principe de Cohérence

Le vault doit toujours être dans un état cohérent.

**Implémentation :**
- Validation automatique du frontmatter
- Vérification des liens
- Détection des contradictions
- Mise à jour atomique de l'index

### 4. Principe de Navigabilité

Le vault doit être facilement navigable.

**Implémentation :**
- Références croisées explicites
- Index complet
- Recherche efficace
- Organisation hiérarchique

### 5. Principe de Maintenabilité

Le vault doit être facile à maintenir.

**Implémentation :**
- Structure claire
- Documentation complète
- Outils de linting
- Journal des opérations

---

## Bonnes Pratiques

### Pour les Développeurs

1. **Code**
   - Suivre les conventions de nommage
   - Documenter toutes les fonctions publiques
   - Utiliser les types de données appropriés
   - Gérer les erreurs de manière appropriée

2. **Tests**
   - Écrire des tests unitaires pour chaque fonction
   - Tester les cas limites
   - Vérifier les invariants
   - Maintenir une bonne couverture

3. **Documentation**
   - Documenter toutes les décisions de conception
   - Maintenir la documentation à jour
   - Utiliser des exemples clairs
   - Documenter les limitations

### Pour les Utilisateurs

1. **Organisation**
   - Utiliser une structure de dossiers logique
   - Utiliser des noms de fichiers descriptifs
   - Utiliser des tags cohérents
   - Maintenir les références à jour

2. **Ingestion**
   - Vérifier les sources avant ingestion
   - Discuter avec l'agent pour clarification
   - Vérifier les pages générées
   - Corriger les erreurs

3. **Requêtes**
   - Formuler des requêtes claires
   - Utiliser des mots-clés spécifiques
   - Vérifier les citations
   - Sauvegarder les bonnes réponses

4. **Maintenance**
   - Effectuer un linting régulier
   - Corriger les problèmes rapidement
   - Mettre à jour l'index
   - Maintenir le log à jour

---

## Gestion des Erreurs

### Types d'Erreurs

1. **Erreurs Critiques**
   - Violation des règles immuables
   - Problèmes de structure du vault
   - Erreurs de parsing

2. **Erreurs de Validation**
   - Frontmatter invalide
   - Liens brisés
   - Références manquantes

3. **Avertissements**
   - Pages orphelines
   - Contradictions non résolues
   - Affirmations obsolètes

4. **Informations**
   - Suggestions d'amélioration
   - Opportunités de références croisées
   - Optimisations possibles

### Gestion des Erreurs

1. **Détection**
   - Détecter les erreurs dès que possible
   - Classer par gravité
   - Documenter le contexte

2. **Signalement**
   - Signaler clairement à l'utilisateur
   - Fournir des informations de dépannage
   - Proposer des actions correctives

3. **Récupération**
   - Proposer des solutions automatiques quand possible
   - Permettre la récupération manuelle
   - Maintenir l'intégrité du vault

---

## Compatibilité Multi-Outils

### Outils Supportés

| Outil | Fichier de Configuration | Statut |
|-------|------------------------|--------|
| Claude Code | `CLAUDE.md` | ✅ Support complet |
| Codex CLI | `AGENTS.md` | ✅ Support complet |
| Cursor (moderne) | `AGENTS.md` | ✅ Support complet |
| Cursor (legacy) | `.cursorrules` | ✅ Support complet |
| Antigravity | `AGENTS.md` | ✅ Support complet |
| OpenCode | `AGENTS.md` | ✅ Support complet |
| Pi | `AGENTS.md` | ✅ Support complet |
| Gemini CLI | `AGENTS.md` | ✅ Support complet |

### Adaptation par Outil

#### Claude Code
- Utilise les slash commands (`/wiki-init`, `/wiki-ingest`, etc.)
- Configuration dans `CLAUDE.md`
- Intégration native avec les projets Claude

#### Codex CLI
- Utilise les commandes sous forme de messages
- Configuration dans `AGENTS.md`
- Nécessite une configuration spécifique de l'API

#### Cursor
- Utilise les slash commands ou les messages
- Configuration dans `AGENTS.md` ou `.cursorrules`
- Intégration avec l'interface Cursor

### Configuration Multi-Outils

Pour permettre l'utilisation de plusieurs outils sur le même vault :

1. Créer tous les fichiers de configuration
   ```bash
   python scripts/init_vault.py --path ~/vaults/recherche --tool all
   ```

2. Chaque outil chargera son fichier de configuration approprié

3. Tous les outils utiliseront la même structure de vault

---

## Annexes

### Glossaire

| Terme | Définition |
|-------|------------|
| Vault | Dossier racine contenant toutes les données |
| Raw | Dossier contenant les sources originales immuables |
| Wiki | Dossier contenant la base de connaissances |
| Entité | Personne, organisation, lieu, produit, projet ou événement |
| Concept | Idée, théorie, framework ou méthodologie |
| Source | Document original ingéré dans le système |
| Index | Catalogue complet de toutes les pages |
| Log | Journal des opérations effectuées |

### Références

- [README.md](../README.md) - Documentation principale
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Architecture technique
- [SCHEMA.md](../SCHEMA.md) - Schémas et structures de données
- [ROADMAP.md](../ROADMAP.md) - Feuille de route

---

**Note :** Ce document est la source de vérité pour toutes les compétences et règles du système RAG Wiki. Toute modification doit être réfléchie et documentée.
