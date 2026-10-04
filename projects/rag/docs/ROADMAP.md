# Feuille de Route du Projet RAG Wiki

> **Version :** 1.0.0
> **Dernière mise à jour :** 2024-01-20

Ce document décrit la feuille de route pour le développement du système RAG Wiki.

---

## Vision

Créer un système de gestion de connaissances **compounding** qui permet aux utilisateurs de construire et maintenir une base de connaissances structurée et interconnectée, en utilisant les LLM comme assistants intelligents.

---

## Phases de Développement

### Phase 1: Fondations (v0.1.0) ✅ COMPLET

**Objectif :** Créer la structure de base et les fonctionnalités principales.

#### Livrables

- [x] **Architecture** : Structure modulaire complète
- [x] **Types et Modèles** : Définition des types de données
- [x] **Core Engine** : WikiEngine avec pipelines principaux
- [x] **Storage** : VaultManager pour la gestion des fichiers
- [x] **Indexing** : IndexManager pour la gestion des index
- [x] **Retrieval** : Services de récupération (BM25, Embeddings, Hybride)
- [x] **Sources** : Parsers pour différents types de sources
- [x] **Pages** : Factory et templates pour les pages
- [x] **Agents** : BaseAgent et agents spécialisés
- [x] **Scripts** : Scripts CLI principaux (init, ingest, query, lint)
- [x] **Configuration** : Système de configuration flexible
- [x] **Documentation** : Documentation complète (README, ARCHITECTURE, SCHEMA)
- [x] **Templates** : Templates pour Obsidian et configuration

#### Fonctionnalités Implémentées

1. **Ingestion**
   - Parsing de sources (PDF, HTML, Markdown, texte)
   - Extraction d'entités et concepts
   - Création de pages structurées
   - Mise à jour des références croisées
   - Mise à jour automatique de l'index
   - Logging des opérations

2. **Requête**
   - Recherche en couches (index → BM25 → embeddings)
   - Sélection des pages pertinentes
   - Synthèse de réponses avec citations
   - Offre de sauvegarde des réponses

3. **Linting**
   - Vérifications mécaniques (frontmatter, liens, références)
   - Vérifications sémantiques (contradictions, orphelins)
   - Vérifications de santé globale
   - Génération de rapports détaillés

#### Tests

- [x] Tests unitaires pour les types
- [x] Tests unitaires pour la configuration
- [x] Tests unitaires pour les utilitaires
- [ ] Tests d'intégration pour les pipelines
- [ ] Tests de bout en bout pour les workflows

---

### Phase 2: Améliorations (v0.2.0) 🚀 EN COURS

**Objectif :** Améliorer les performances, l'expérience utilisateur et les fonctionnalités avancées.

#### Fonctionnalités Prévues

1. **Améliorations du Retrieval**
   - [ ] Implémentation complète de BM25 avec rank-bm25
   - [ ] Support des embeddings avec sentence-transformers
   - [ ] Optimisation des index pour les grands vaults
   - [ ] Recherche hybride améliorée (RRF avancé)

2. **Améliorations de l'Ingestion**
   - [ ] Parsing PDF avancé avec pypdf
   - [ ] Parsing HTML avec BeautifulSoup
   - [ ] Extraction d'entités avec NER (Named Entity Recognition)
   - [ ] Extraction de concepts avec analyse sémantique
   - [ ] Détection automatique des citations

3. **Améliorations de l'Interface**
   - [ ] Interface CLI améliorée avec argparse
   - [ ] Support des commandes slash pour différents outils
   - [ ] Intégration avec Obsidian (plugins)
   - [ ] Interface web basique (Flask/FastAPI)

4. **Gestion des Connaissances**
   - [ ] Détection automatique des contradictions
   - [ ] Résolution automatique des contradictions (avec confirmation utilisateur)
   - [ ] Suggestions de références croisées
   - [ ] Génération automatique de synthèses

5. **Gestion du Vault**
   - [ ] Support Git natif pour le versionnage
   - [ ] Synchronisation avec des dépôts distants
   - [ ] Backup automatique
   - [ ] Restauration de versions

6. **Performance**
   - [ ] Cache des index en mémoire
   - [ ] Lazy loading des embeddings
   - [ ] Batch processing pour l'ingestion
   - [ ] Parallel processing pour la recherche

#### Tests

- [ ] Tests de performance
- [ ] Tests de charge pour les grands vaults
- [ ] Tests de compatibilité multi-outils
- [ ] Tests d'intégration continue (CI/CD)

---

### Phase 3: Extension (v0.3.0) 📅 PRÉVU

**Objectif :** Étendre les capacités du système avec des fonctionnalités avancées.

#### Fonctionnalités Prévues

1. **Multi-Utilisateurs**
   - [ ] Gestion des utilisateurs
   - [ ] Permissions et accès
   - [ ] Historique par utilisateur
   - [ ] Collaboration en temps réel

2. **Multi-Vaults**
   - [ ] Gestion de plusieurs vaults
   - [ ] Recherche croisée entre vaults
   - [ ] Synchronisation entre vaults
   - [ ] Fusion de vaults

3. **Fonctionnalités Avancées**
   - [ ] Support des images et diagrammes
   - [ ] Support des vidéos et audio (transcription)
   - [ ] Support des bases de données externes
   - [ ] Intégration avec des APIs externes

4. **Intelligence Artificielle**
   - [ ] Détection automatique des topics
   - [ ] Clustering automatique des pages
   - [ ] Génération automatique de tags
   - [ ] Recommandations de contenu

5. **Visualisation**
   - [ ] Graphes de connaissances
   - [ ] Visualisation des connexions
   - [ ] Tableaux de bord
   - [ ] Export vers différents formats

6. **Intégrations**
   - [ ] Intégration avec Notion
   - [ ] Intégration avec Confluence
   - [ ] Intégration avec Google Drive
   - [ ] Intégration avec Dropbox

---

### Phase 4: Production (v1.0.0) 🎯 FUTUR

**Objectif :** Préparer le système pour une utilisation en production.

#### Fonctionnalités Prévues

1. **Stabilité**
   - [ ] Tests complets
   - [ ] Documentation complète
   - [ ] Support et maintenance
   - [ ] Gestion des erreurs robuste

2. **Performance**
   - [ ] Optimisation complète
   - [ ] Scalabilité horizontale
   - [ ] Monitoring et métriques
   - [ ] Alertes et notifications

3. **Sécurité**
   - [ ] Authentification et autorisation
   - [ ] Chiffrement des données
   - [ ] Audit des opérations
   - [ ] Conformité RGPD

4. **Déploiement**
   - [ ] Package PyPI
   - [ ] Conteneurs Docker
   - [ ] Déploiement cloud (AWS, GCP, Azure)
   - [ ] Documentation de déploiement

5. **Communauté**
   - [ ] Documentation utilisateur
   - [ ] Exemples et tutoriels
   - [ ] Support communautaire
   - [ ] Contributions ouvertes

---

## Priorités

### Priorité 1: Critique
- Fonctionnalités de base (ingestion, requête, linting)
- Stabilité et fiabilité
- Sécurité des données

### Priorité 2: Importante
- Performances
- Expérience utilisateur
- Documentation

### Priorité 3: Utile
- Fonctionnalités avancées
- Intégrations
- Visualisation

### Priorité 4: Future
- Multi-utilisateurs
- Multi-vaults
- IA avancée

---

## Calendrier

| Phase | Version | Période | Statut |
|-------|---------|---------|--------|
| 1 | v0.1.0 | Janvier 2024 | ✅ COMPLET |
| 2 | v0.2.0 | Février - Mars 2024 | 🚀 EN COURS |
| 3 | v0.3.0 | Avril - Juin 2024 | 📅 PRÉVU |
| 4 | v1.0.0 | Juillet - Septembre 2024 | 🎯 FUTUR |

---

## Contributions

Les contributions sont les bienvenues ! Voici comment contribuer :

1. **Signaler des bugs** : Ouvrir une issue sur GitHub
2. **Proposer des fonctionnalités** : Ouvrir une issue avec la proposition
3. **Contribuer au code** : Forker le dépôt et ouvrir une PR
4. **Améliorer la documentation** : Mettre à jour les fichiers de documentation
5. **Participer aux discussions** : Rejoindre la communauté

---

## Ressources

- [README.md](README.md) - Documentation principale
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture technique
- [SCHEMA.md](SCHEMA.md) - Schémas et structures de données
- [CLAUDE.md](CLAUDE.md) - Configuration pour Claude Code
- [AGENTS.md](AGENTS.md) - Configuration pour autres outils
- [SKILL.md](SKILL.md) - Compétences et règles

---

**Note :** Cette feuille de route est sujette à changement. Les priorités et dates peuvent être ajustées en fonction des besoins et des contributions.
