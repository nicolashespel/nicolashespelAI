# Schémas et Structures de Données

## Vue d'ensemble

Ce document décrit tous les schémas, formats de pages, chemins et règles de nommage utilisés dans le système RAG Wiki. Tous les fichiers dans le vault suivent ces conventions strictes.

## Types de Pages

### 1. Pages Entités (`wiki/entities/`)

Représentent des personnes, organisations, lieux, produits, etc.

**Format du nom de fichier :**
```
wiki/entities/<type>/<nom_normalisé>.md
```

**Types d'entités :**
- `people/` - Personnes
- `organizations/` - Organisations
- `places/` - Lieux
- `products/` - Produits
- `projects/` - Projets
- `events/` - Événements

**Exemple de chemin :**
```
wiki/entities/people/andrej_karpathy.md
wiki/entities/organizations/openai.md
```

**Frontmatter requis :**
```yaml
---
type: entity
entity_type: person  # ou organization, place, product, project, event
name: Andrej Karpathy
description: Directeur de l'IA chez Tesla, ancien chercheur chez OpenAI
aliases:
  - Andrey Karpathy
  - Andrej K.
tags:
  - ai
  - research
  - deep-learning
related:
  - organizations/openai
  - organizations/tesla
  - concepts/transformers
created: 2024-01-15T10:30:00Z
updated: 2024-01-20T14:45:00Z
sources:
  - sources/paper_2024_001
  - sources/interview_2023_045
---
```

**Structure du contenu :**
```markdown
# Andrej Karpathy

## Description
[Description détaillée de l'entité]

## Contexte
[Contexte historique et importance]

## Relations
- **Affiliation actuelle :** [[Tesla]]
- **Ancienne affiliation :** [[OpenAI]]
- **Domaines de recherche :** [[Transformers]], [[Computer Vision]]

## Contributions majeures
- [Liste des contributions]

## Références
- [[paper_2024_001]]
- [[interview_2023_045]]
```

### 2. Pages Concepts (`wiki/concepts/`)

Représentent des idées, théories, frameworks, méthodologies.

**Format du nom de fichier :**
```
wiki/concepts/<nom_normalisé>.md
```

**Exemple de chemin :**
```
wiki/concepts/transformers.md
wiki/concepts/reinforcement_learning.md
```

**Frontmatter requis :**
```yaml
---
type: concept
name: Transformers
description: Architecture de réseau de neurones basée sur l'attention
categories:
  - deep-learning
  - nlp
tags:
  - attention
  - neural-networks
  - nlp
related:
  - concepts/attention_mechanism
  - concepts/self_attention
  - entities/people/vaswani_ashish
  - sources/paper_attention_is_all_you_need
status: active  # active, deprecated, obsolete
authority: high  # high, medium, low, speculative
created: 2024-01-15T10:30:00Z
updated: 2024-01-20T14:45:00Z
sources:
  - sources/paper_attention_is_all_you_need
  - sources/tutorial_transformers_2023
---
```

**Structure du contenu :**
```markdown
# Transformers

## Définition
[Définition claire et concise]

## Contexte
[Contexte historique et développement]

## Fonctionnement
[Explication du fonctionnement interne]

### Architecture
[Description de l'architecture]

### Mécanisme d'attention
[Explication détaillée]

## Applications
- [Liste des applications]

## Avantages
- [Liste des avantages]

## Limites
- [Liste des limites]

## Variantes
- [[Attention Is All You Need]]
- [[BERT]]
- [[GPT]]

## Références
- [[paper_attention_is_all_you_need]]
- [[tutorial_transformers_2023]]
```

### 3. Pages Sources (`wiki/sources/`)

Une page par source ingérée, contenant un résumé et des métadonnées.

**Format du nom de fichier :**
```
wiki/sources/<type>_<date>_<identifiant>.md
```

**Types de sources :**
- `paper_` - Articles scientifiques
- `book_` - Livres
- `article_` - Articles de blog/news
- `video_` - Vidéos
- `podcast_` - Podcasts
- `interview_` - Interviews
- `doc_` - Documentation
- `web_` - Pages web

**Exemple de chemin :**
```
wiki/sources/paper_2024_001_attention_is_all_you_need.md
wiki/sources/article_2023_045_karpathy_llm_wiki.md
```

**Frontmatter requis :**
```yaml
---
type: source
source_type: paper  # paper, book, article, video, podcast, interview, doc, web
original_path: raw/papers/attention_is_all_you_need.pdf
title: Attention Is All You Need
authors:
  - entities/people/vaswani_ashish
  - entities/people/shazeer_noam
date: 2017-06-12
url: https://arxiv.org/abs/1706.03762
doi: 10.5555/12345678
summary: Résumé généré par LLM
status: processed  # raw, processing, processed, archived
tags:
  - nlp
  - transformers
  - attention
related:
  - concepts/transformers
  - concepts/attention_mechanism
  - entities/people/vaswani_ashish
ingested: 2024-01-15T10:30:00Z
updated: 2024-01-20T14:45:00Z
---
```

**Structure du contenu :**
```markdown
# Attention Is All You Need

## Métadonnées
- **Auteurs :** [[Ashish Vaswani]], [[Noam Shazeer]], et al.
- **Date :** 12 juin 2017
- **Type :** Article scientifique
- **URL :** [Lien vers l'article](https://arxiv.org/abs/1706.03762)

## Résumé
[Résumé détaillé généré par LLM]

## Points clés
- [Liste des points clés extraits]

## Citations
[Extraits importants avec citations de page/section]

## Analyse
[Analyse et interprétation par le LLM]

## Connexions
- **Concepts liés :** [[Transformers]], [[Attention Mechanism]]
- **Entités liées :** [[Ashish Vaswani]], [[Noam Shazeer]]
- **Sources connexes :** [[paper_2018_012_bert]], [[paper_2019_034_gpt2]]

## Notes
[Notes supplémentaires et réflexions]
```

### 4. Pages Comparaisons (`wiki/comparisons/`)

Analyses croisées entre plusieurs sources ou concepts.

**Format du nom de fichier :**
```
wiki/comparisons/<sujet>_vs_<sujet>.md
wiki/comparisons/<sujet>_comparison.md
```

**Exemple de chemin :**
```
wiki/comparisons/transformers_vs_rnns.md
wiki/comparisons/llm_providers_comparison.md
```

**Frontmatter requis :**
```yaml
---
type: comparison
name: Transformers vs RNNs
description: Comparaison des architectures Transformers et RNNs
subjects:
  - concepts/transformers
  - concepts/recurrent_neural_networks
criteria:
  - performance
  - training_efficiency
  - parallelization
  - memory_usage
tags:
  - deep-learning
  - architecture
  - comparison
created: 2024-01-15T10:30:00Z
updated: 2024-01-20T14:45:00Z
sources:
  - sources/paper_2024_001
  - sources/paper_2023_045
---
```

**Structure du contenu :**
```markdown
# Transformers vs RNNs

## Introduction
[Introduction au sujet de la comparaison]

## Critères de comparaison

### Performance
| Critère | Transformers | RNNs |
|---------|--------------|------|
| Vitesse d'inférence | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Précision | ⭐⭐⭐⭐ | ⭐⭐⭐ |

### Efficacité d'entraînement
[Analyse détaillée]

### Parallélisation
[Analyse détaillée]

### Utilisation mémoire
[Analyse détaillée]

## Avantages et inconvénients

### Transformers
**Avantages:**
- [Liste]

**Inconvénients:**
- [Liste]

### RNNs
**Avantages:**
- [Liste]

**Inconvénients:**
- [Liste]

## Conclusion
[Conclusion et recommandations]

## Références
- [[sources/paper_2024_001]]
- [[sources/paper_2023_045]]
```

### 5. Pages Synthèse (`wiki/synthesis/`)

Vues d'ensemble et thèses de haut niveau.

**Format du nom de fichier :**
```
wiki/synthesis/<domaine>_<sujet>.md
```

**Exemple de chemin :**
```
wiki/synthesis/ai_interpretability_overview.md
wiki/synthesis/ml_trends_2024.md
```

**Frontmatter requis :**
```yaml
---
type: synthesis
name: AI Interpretability Overview
description: Vue d'ensemble des approches d'interprétabilité en IA
domain: ai
scope: overview
tags:
  - interpretability
  - ai
  - overview
related:
  - concepts/transformers
  - concepts/attention_mechanism
  - sources/paper_2024_001
  - sources/paper_2023_045
status: current  # current, draft, outdated
confidence: high  # high, medium, low
created: 2024-01-15T10:30:00Z
updated: 2024-01-20T14:45:00Z
sources:
  - sources/paper_2024_001
  - sources/paper_2023_045
---
```

**Structure du contenu :**
```markdown
# AI Interpretability Overview

## Executive Summary
[Résumé exécutif]

## Contexte
[Contexte et importance du sujet]

## État de l'art
[Vue d'ensemble de l'état actuel]

### Approches principales
- [[Interpretability via Attention]]
- [[Feature Visualization]]
- [[Counterfactual Analysis]]

### Défis actuels
- [Liste des défis]

## Tendances
[Analyse des tendances]

## Prédictions
[Prédictions pour l'avenir]

## Recommandations
[Recommandations stratégiques]

## Références
- [[sources/paper_2024_001]]
- [[sources/paper_2023_045]]
- [[concepts/transformers]]
```

### 6. Fichiers Spéciaux

#### index.md

Catalogue de tout le contenu du vault.

**Frontmatter requis :**
```yaml
---
type: index
name: Vault Index
description: Catalogue complet du vault
generated: 2024-01-20T14:45:00Z
version: 1.0.0
---
```

**Structure du contenu :**
```markdown
# Vault Index

## Statistiques
- **Total pages :** 156
- **Entités :** 45
- **Concepts :** 32
- **Sources :** 23
- **Comparaisons :** 8
- **Synthèses :** 5
- **Dernière mise à jour :** 2024-01-20T14:45:00Z

## Par Type

### Entités (45)
- [[entities/people/andrej_karpathy]]
- [[entities/organizations/openai]]
- [Liste complète...]

### Concepts (32)
- [[concepts/transformers]]
- [[concepts/attention_mechanism]]
- [Liste complète...]

### Sources (23)
- [[sources/paper_2024_001_attention_is_all_you_need]]
- [[sources/article_2023_045_karpathy_llm_wiki]]
- [Liste complète...]

### Comparaisons (8)
- [[comparisons/transformers_vs_rnns]]
- [Liste complète...]

### Synthèses (5)
- [[synthesis/ai_interpretability_overview]]
- [Liste complète...]

## Par Tag

### AI (56)
- [[concepts/transformers]]
- [[entities/people/andrej_karpathy]]
- [Liste...]

### Deep Learning (42)
- [Liste...]

## Par Date

### Janvier 2024 (23)
- [Liste...]

### Décembre 2023 (15)
- [Liste...]

## Recherche
Utilisez les commandes `/wiki-query` ou `/wiki-search` pour trouver du contenu.
```

#### log.md

Journal append-only de toutes les opérations.

**Frontmatter requis :**
```yaml
---
type: log
name: Vault Log
description: Journal des opérations du vault
created: 2024-01-15T10:30:00Z
---
```

**Structure du contenu :**
```markdown
# Vault Log

## 2024-01-20

### 14:45:00 - Ingestion de source
- **Source :** raw/papers/attention_is_all_you_need.pdf
- **Pages créées :**
  - wiki/sources/paper_2024_001_attention_is_all_you_need.md
- **Pages mises à jour :**
  - wiki/entities/people/vaswani_ashish.md
  - wiki/concepts/transformers.md
  - wiki/index.md
- **Pages référencées :**
  - wiki/concepts/attention_mechanism.md
- **Durée :** 2m 34s
- **Status :** ✅ Success

### 14:30:00 - Requête
- **Requête :** "Qu'est-ce que le mécanisme d'attention ?"
- **Pages consultées :**
  - wiki/concepts/attention_mechanism.md
  - wiki/concepts/transformers.md
- **Réponse :** [Lien vers la réponse]
- **Durée :** 12s

## 2024-01-19

[Autres entrées...]
```

## Schémas des Fichiers de Configuration

### CLAUDE.md

Fichier de configuration pour Claude Code.

```markdown
# Claude Code Configuration for RAG Wiki

## Instructions
You are a disciplined wiki maintainer. Follow the SKILL.md rules strictly.

## Commands

### /wiki-init
Initialize a new wiki vault.

### /wiki-ingest <path>
Ingest a source file and update the wiki.

### /wiki-query <query>
Query the wiki and return a synthesized answer.

### /wiki-lint
Run health checks on the wiki.

### /wiki-log
Show the operation log.

## Rules
1. Never edit files in raw/
2. Always update index.md
3. Always log operations in log.md
4. Cross-reference everything
5. Flag contradictions explicitly
```

### AGENTS.md

Fichier de configuration pour Codex, Cursor, Antigravity, etc.

```markdown
# LLM Wiki Configuration

## Role
You are a disciplined wiki maintainer for the RAG Wiki system.

## Skills
- Wiki Ingestor
- Wiki Librarian  
- Wiki Linter

## Commands

### wiki-init
Initialize a new wiki vault with the specified parameters.

### wiki-ingest
Ingest a source file, create summary, update cross-references, update index, log operation.

### wiki-query
Search the wiki using layered retrieval (index -> BM25 -> embeddings), synthesize answer with citations.

### wiki-lint
Run mechanical and semantic health checks, surface contradictions, orphans, stale claims.

### wiki-log
Display the operation log from log.md.

## Rules
1. IMMUTABLE_RAW: Never modify files in the raw/ directory
2. UPDATE_INDEX: Always update index.md after any change
3. LOG_OPERATIONS: Always append to log.md
4. CROSS_REFERENCE: Link to existing pages when relevant
5. FLAG_CONTRADICTIONS: Explicitly mark contradictions
6. CITE_SOURCES: Always cite sources for claims
```

### .cursorrules

Fichier de configuration pour Cursor (legacy).

```
# Cursor Rules for RAG Wiki

## System
You are a wiki maintainer. Follow SKILL.md strictly.

## Commands
- /wiki-init: Initialize vault
- /wiki-ingest <path>: Ingest source
- /wiki-query <query>: Query wiki
- /wiki-lint: Health check
- /wiki-log: Show log

## Rules
- NEVER edit raw/
- ALWAYS update index.md
- ALWAYS log to log.md
- Cross-reference everything
- Flag contradictions
```

## Règles de Nommage

### Normalisation des Noms

1. **Minuscules** : Tous les noms de fichiers en minuscules
2. **Séparateurs** : Utiliser des underscores (`_`) au lieu d'espaces
3. **Caractères spéciaux** : Supprimer les caractères spéciaux (sauf `-` et `_`)
4. **Accents** : Supprimer les accents ou les remplacer par leur équivalent ASCII

**Exemples :**
- "Andréj Karpathy" → `andrej_karpathy`
- "Attention Is All You Need" → `attention_is_all_you_need`
- "Transformers: The New Architecture" → `transformers_the_new_architecture`

### Identifiants de Sources

Format : `<type>_<YYYY>_<MM>_<DD>_<sequence>_<titre_normalisé>`

**Exemples :**
- `paper_2024_01_15_001_attention_is_all_you_need`
- `article_2023_12_20_001_karpathy_llm_wiki`

### Identifiants dans les Références

Dans le frontmatter, les références utilisent le chemin sans extension :

```yaml
sources:
  - sources/paper_2024_01_15_001_attention_is_all_you_need
```

Dans le contenu, utiliser les liens wiki :

```markdown
- [[paper_2024_01_15_001_attention_is_all_you_need]]
```

## Validation des Schémas

### Validation du Frontmatter

Tous les fichiers doivent avoir un frontmatter YAML valide avec les champs requis pour leur type.

### Validation des Liens

- Tous les liens wiki (`[[...]]`) doivent pointer vers des fichiers existants
- Les liens doivent utiliser la casse correcte
- Les liens doivent être normalisés

### Validation des Références

- Toutes les références dans le frontmatter doivent exister
- Les références doivent être cohérentes avec les liens dans le contenu

## Gestion des Versions

### Historique des Pages

Chaque modification d'une page doit :
1. Mettre à jour le champ `updated` dans le frontmatter
2. Ajouter une entrée dans `log.md`
3. Mettre à jour `index.md`

### Supersession

Quand une page est remplacée :
1. Créer une nouvelle version avec un timestamp dans le nom
2. Ajouter un champ `superseded_by` dans l'ancienne version
3. Ajouter un champ `supersedes` dans la nouvelle version
4. Logger la supersession

**Exemple :**
```yaml
# Dans l'ancienne version
superseded_by: concepts/transformers_2024_02_01

# Dans la nouvelle version  
supersedes: concepts/transformers_2024_01_15
```

## Indexation

### Structure de l'Index

L'`index.md` contient :
1. Statistiques globales
2. Liste complète de toutes les pages par type
3. Liste par tags
4. Liste par date

### Mise à jour de l'Index

L'index doit être mis à jour après chaque :
- Création de page
- Suppression de page
- Changement de type de page
- Ajout/suppression de tags

### Recherche dans l'Index

L'index permet :
- Recherche par type
- Recherche par tag
- Recherche par date
- Recherche par nom

## Règles Immuables

1. **IMMUTABLE_RAW** : Le contenu de `raw/` ne doit JAMAIS être modifié par le LLM
2. **UPDATE_INDEX** : L'`index.md` doit TOUJOURS être mis à jour après un changement
3. **LOG_OPERATIONS** : Toutes les opérations doivent être loggées dans `log.md`
4. **CROSS_REFERENCE** : Les pages doivent TOUJOURS être référencées quand c'est pertinent
5. **FLAG_CONTRADICTIONS** : Les contradictions doivent TOUJOURS être signalées explicitement
6. **CITE_SOURCES** : Toutes les affirmations doivent TOUJOURS citer leurs sources

## Exemples Complets

### Exemple de Page Entité

**Fichier :** `wiki/entities/people/andrej_karpathy.md`

```markdown
---
type: entity
entity_type: person
name: Andrej Karpathy
description: Directeur de l'IA chez Tesla, ancien chercheur chez OpenAI
aliases:
  - Andrey Karpathy
  - Andrej K.
tags:
  - ai
  - research
  - deep-learning
  - computer-vision
related:
  - organizations/openai
  - organizations/tesla
  - concepts/transformers
  - concepts/computer_vision
created: 2024-01-15T10:30:00Z
updated: 2024-01-20T14:45:00Z
sources:
  - sources/paper_2024_001_attention_is_all_you_need
  - sources/article_2023_045_karpathy_llm_wiki
  - sources/interview_2023_120_tesla_ai_day
---

# Andrej Karpathy

## Description
Andrej Karpathy est un chercheur et ingénieur renommé en intelligence artificielle, connu pour ses contributions majeures dans les domaines de la vision par ordinateur et de l'apprentissage profond. Il est actuellement Directeur de l'IA chez Tesla, où il supervise le développement des systèmes d'IA pour les véhicules autonomes.

## Contexte
Né en Slovaquie, Karpathy a obtenu son doctorat en informatique à l'Université de Stanford sous la direction de Fei-Fei Li. Il a ensuite rejoint OpenAI en tant que chercheur principal, où il a contribué au développement de plusieurs modèles de langage avancés.

## Carrière
- **2022-Présent** : Directeur de l'IA, Tesla
- **2016-2022** : Chercheur principal, OpenAI
- **2015-2016** : Chercheur postdoctoral, Stanford University
- **2009-2015** : Doctorat, Stanford University

## Contributions majeures
- Développement de l'architecture Transformer
- Travaux sur la vision par ordinateur et la reconnaissance d'images
- Contributions aux modèles de langage GPT-2 et GPT-3
- Développement de systèmes d'IA pour la conduite autonome

## Publications notables
- [[paper_2024_001_attention_is_all_you_need]]
- [[paper_2018_012_bert]]

## Références
- [[sources/paper_2024_001_attention_is_all_you_need]]
- [[sources/article_2023_045_karpathy_llm_wiki]]
- [[organizations/openai]]
- [[organizations/tesla]]
```

### Exemple de Page Concept

**Fichier :** `wiki/concepts/transformers.md`

```markdown
---
type: concept
name: Transformers
description: Architecture de réseau de neurones basée sur le mécanisme d'attention
categories:
  - deep-learning
  - neural-networks
  - nlp
tags:
  - attention
  - self-attention
  - multi-head-attention
  - encoder-decoder
related:
  - concepts/attention_mechanism
  - concepts/self_attention
  - concepts/multi_head_attention
  - concepts/encoder_decoder_architecture
  - entities/people/vaswani_ashish
  - entities/people/shazeer_noam
  - sources/paper_2024_001_attention_is_all_you_need
status: active
authority: high
created: 2024-01-15T10:30:00Z
updated: 2024-01-20T14:45:00Z
sources:
  - sources/paper_2024_001_attention_is_all_you_need
  - sources/tutorial_transformers_2023
  - sources/book_deep_learning_2022
---

# Transformers

## Définition
Les Transformers sont une architecture de réseau de neurones introduite dans l'article "Attention Is All You Need" (Vaswani et al., 2017) qui repose entièrement sur le mécanisme d'attention, sans utiliser de réseaux de neurones récurrents ou convolutifs.

## Contexte
Avant les Transformers, les modèles de traitement du langage naturel (NLP) reposaient principalement sur des architectures récurrentes (RNN, LSTM) ou convolutives (CNN). Ces architectures avaient des limitations en termes de parallélisation et de capacité à capturer des dépendances à long terme.

Le papier "Attention Is All You Need" a introduit une nouvelle architecture qui surmonte ces limitations en utilisant exclusivement des mécanismes d'attention.

## Fonctionnement

### Architecture de base
Le Transformer utilise une architecture encoder-decoder :

```
[Input] → [Encoder] → [Decoder] → [Output]
```

### Composants clés

#### Mécanisme d'attention
Le cœur du Transformer est le mécanisme d'attention qui permet au modèle de se concentrer sur différentes parties de l'entrée lors de la génération de chaque partie de la sortie.

[[concepts/attention_mechanism]]

#### Self-Attention
Capacité du modèle à relier différentes positions d'une seule séquence pour calculer une représentation de la séquence.

[[concepts/self_attention]]

#### Multi-Head Attention
Mécanisme qui exécute plusieurs mécanismes d'attention en parallèle, permettant au modèle de capturer différentes relations entre les éléments de la séquence.

[[concepts/multi_head_attention]]

### Flux de données
1. **Embedding** : Conversion des tokens en vecteurs
2. **Positional Encoding** : Ajout d'informations de position
3. **Encoder Layers** : Plusieurs couches d'auto-attention et feed-forward
4. **Decoder Layers** : Plusieurs couches d'attention et feed-forward
5. **Output** : Génération de la sortie

## Avantages
- **Parallélisation** : Tous les tokens sont traités simultanément
- **Efficacité** : Moins de calculs que les RNN pour les séquences longues
- **Capacité** : Meilleure capacité à capturer les dépendances à long terme
- **Scalabilité** : Scale bien avec l'augmentation des données et des paramètres

## Limites
- **Complexité quadratique** : La complexité calculatoire augmente quadratiquement avec la longueur de la séquence
- **Mémoire** : Consommation mémoire élevée pour les séquences longues
- **Interprétabilité** : Moins interprétable que les modèles plus simples

## Variantes
- **BERT** : Encoder-only pour les tâches de compréhension
- **GPT** : Decoder-only pour les tâches de génération
- **T5** : Architecture unifiée pour toutes les tâches NLP
- **Vision Transformer (ViT)** : Application aux images

## Applications
- Traduction automatique
- Génération de texte
- Compréhension de texte
- Résumé automatique
- Réponse aux questions
- Classification de texte

## Références
- [[sources/paper_2024_001_attention_is_all_you_need]]
- [[sources/tutorial_transformers_2023]]
- [[concepts/attention_mechanism]]
- [[concepts/self_attention]]
- [[entities/people/vaswani_ashish]]
- [[entities/people/shazeer_noam]]
```

## Validation et Tests

### Tests de Validation

1. **Validation du Frontmatter** : Vérifier que tous les champs requis sont présents
2. **Validation des Liens** : Vérifier que tous les liens wiki pointent vers des fichiers existants
3. **Validation des Références** : Vérifier que toutes les références existent
4. **Validation des Types** : Vérifier que le type de page est valide
5. **Validation des Tags** : Vérifier que les tags sont valides

### Outils de Validation

```bash
# Valider toutes les pages
python projects/rag/scripts/lint_wiki.py --validate-all

# Valider une page spécifique
python projects/rag/scripts/lint_wiki.py --validate wiki/entities/people/andrej_karpathy.md
```

## Évolutions Futures

### Versions Futures

- **v0.2.0** : Ajout du support pour les images
- **v0.3.0** : Intégration avec des bases de données externes
- **v0.4.0** : Support multi-utilisateurs

### Améliorations Potentielles

- Indexation automatique des métadonnées
- Recherche avancée avec embeddings
- Détection automatique des contradictions
- Suggestions de références croisées
- Génération automatique de synthèses

## Conclusion

Ce document définit les schémas et structures de données qui forment la base du système RAG Wiki. Tous les fichiers dans le vault doivent suivre ces conventions pour assurer la cohérence, l'interopérabilité et la maintenabilité du système.

Pour plus d'informations, consulter :
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture technique
- [CLAUDE.md](CLAUDE.md) - Configuration pour Claude Code
- [AGENTS.md](AGENTS.md) - Configuration pour d'autres outils
