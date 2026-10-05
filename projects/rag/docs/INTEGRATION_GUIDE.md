# 📡 Guide d'Intégration - Système RAG Wiki avec Mistral API

*Dernière mise à jour: 05/10/2026*

Ce guide explique comment intégrer le système RAG Wiki avec différents outils et cas d'usage.

---

## 📋 Table des Matières

1. [Architecture des Agents](#1-architecture-des-agents)
2. [Intégration avec Open WebUI](#2-intégration-avec-open-webui)
3. [Utilisation en CLI](#3-utilisation-en-cli)
4. [Intégration avec un Chatbot Site Web](#4-intégration-avec-un-chatbot-site-web)
5. [Configuration pour un Vault Unique Centralisé](#5-configuration-pour-un-vault-unique-centralisé)
6. [Modèles Mistral Utilisés](#6-modèles-mistral-utilisés)
7. [Exemples Concrets](#7-exemples-concrets)

---

## 1. Architecture des Agents

### 🎯 **Séparation des Responsabilités (1 Agent = 1 Tâche Majeure)**

| **Agent** | **Fichier** | **Responsabilité** | **Modèle Mistral** | **Dépendances** |
|-----------|------------|-------------------|-------------------|----------------|
| **OCRAgent** | `src/agents/ocr_agent.py` | **Extraction de texte** depuis PDF/images via Mistral OCR API | `mistral-ocr-latest` | Mistral API |
| **PreprocessingAgent** | `src/agents/preprocessing_agent.py` | **Nettoyage et structuration** (déduplication, formatage Markdown) | `mistral-small-latest` | Aucun |
| **WikiIngestorAgent** | `src/agents/wiki_ingestor.py` | **Ingestion complète** (OCR + prétraitement + création de pages) | `mistral-large-latest` | OCRAgent, PreprocessingAgent |
| **WikiLibrarianAgent** | `src/agents/wiki_librarian.py` | **Recherche et synthèse** (requêtes avec embeddings) | `mistral-large-latest` + `codestral-embed` | WikiEngine |
| **WikiLinterAgent** | `src/agents/wiki_linter.py` | **Vérification de santé** (liens brisés, contradictions) | `mistral-small-latest` | Aucun |
| **OpenWebUIAgent** | `src/agents/openwebui_agent.py` | **Interface avec Open WebUI** | `mistral-large-latest` | Tous les autres agents |

### 🔄 **Workflow Typique**

```
Utilisateur → OpenWebUIAgent
    ↓
OpenWebUIAgent → WikiIngestorAgent (pour /wiki-ingest)
    ↓
WikiIngestorAgent → OCRAgent (extraction texte)
    ↓
OCRAgent → Mistral OCR API
    ↓
WikiIngestorAgent → PreprocessingAgent (nettoyage)
    ↓
PreprocessingAgent → Nettoyage/Deduplication
    ↓
WikiIngestorAgent → WikiEngine (création pages)
    ↓
WikiEngine → Sauvegarde dans vault/wiki/
```

**✅ Avantages de cette architecture:**
- **Modularité**: Chaque agent peut être utilisé indépendamment
- **Maintenabilité**: Une seule responsabilité par agent
- **Flexibilité**: Possibilité de remplacer un agent sans tout casser
- **Testabilité**: Chaque agent peut être testé unitairement

---

## 2. Intégration avec Open WebUI

### 🎯 **Ce que vous devez configurer**

Dans Open WebUI, allez dans **Paramètres → Custom Commands** et ajoutez les commandes suivantes:

| **Nom** | **Type** | **Commande** | **Description** |
|---------|----------|--------------|-----------------|
| Wiki Query | `text` | `python /chemin/vers/projects/rag/scripts/query_wiki.py --path ~/vaults/knowledge_base --query "{input}"` | Pose une question |
| Wiki Ingest | `text` | `python /chemin/vers/projects/rag/scripts/ingest_source.py --path ~/vaults/knowledge_base --source {input}` | Ingest un fichier |
| Wiki Status | `text` | `python /chemin/vers/projects/rag/scripts/query_wiki.py --path ~/vaults/knowledge_base --status` | Statut du vault |
| Wiki Lint | `text` | `python /chemin/vers/projects/rag/scripts/lint_wiki.py --path ~/vaults/knowledge_base` | Vérifie la santé |

**⚠️ Important:**
- Remplacez `/chemin/vers/` par le chemin **absolu** de votre dépôt
- Remplacez `~/vaults/knowledge_base` par le chemin de votre vault
- **Seul OpenWebUIAgent est exposé** à Open WebUI. Les autres agents sont appelés en interne

### 💡 **Exemple d'utilisation dans Open WebUI**

```
Vous: /Wiki Ingest ~/Documents/SEO_Guide_2024.pdf

Open WebUI:
✓ OCR terminé via Mistral OCR API
✓ Nettoyage et déduplication terminés
✓ 5 pages créées:
  - wiki/sources/SEO_Guide_2024.md
  - wiki/concepts/backlinks.md
  - wiki/concepts/technical_SEO.md
  - wiki/entities/Google.md
  - wiki/entities/Ahrefs.md

Vous: /Wiki Query "Quelles sont les meilleures pratiques pour les backlinks ?"

Open WebUI:
D'après les documents ingérés, les meilleures pratiques pour les backlinks en 2024 sont:

1. **Qualité > Quantité**: Privilégiez les liens de sites avec un DA > 30
   [source:SEO_Guide_2024.md, §2.1]

2. **Diversité des ancres**: Évitez les ancres exact-match à 100%
   [source:SEO_Guide_2024.md, §2.3]

Citations:
- SEO_Guide_2024.md (paragraphe 2.1)
- SEO_Guide_2024.md (paragraphe 2.3)
```

---

## 3. Utilisation en CLI

### 📌 **Commandes CLI Disponibles**

| **Script** | **Commande** | **Description** |
|------------|-------------|-----------------|
| `init_vault.py` | `python init_vault.py --path ~/vaults/mon_vault` | Initialise un vault |
| `ingest_source.py` | `python ingest_source.py --path ~/vaults/mon_vault --source mon_fichier.pdf` | Ingest un fichier |
| `query_wiki.py` | `python query_wiki.py --path ~/vaults/mon_vault --query "ma question"` | Pose une question |
| `lint_wiki.py` | `python lint_wiki.py --path ~/vaults/mon_vault` | Vérifie la santé |
| `preprocess_raw.py` | `python preprocess_raw.py --input mon_fichier.txt --vault ~/vaults/mon_vault` | Prétraite un fichier |
| `api_server.py` | `python api_server.py --port 5000` | Lance le serveur API |

### 💡 **Exemples d'utilisation**

```bash
# Initialiser un vault
python projects/rag/scripts/init_vault.py --path ~/vaults/SEO_Project

# Ingest un PDF
python projects/rag/scripts/ingest_source.py \
  --path ~/vaults/SEO_Project \
  --source ~/Documents/SEO_Guide.pdf

# Poser une question
python projects/rag/scripts/query_wiki.py \
  --path ~/vaults/SEO_Project \
  --query "Qu'est-ce que le Core Web Vitals ?"

# Prétraiter un fichier (sans ingestion)
python projects/rag/scripts/preprocess_raw.py \
  --input ~/Documents/notes.txt \
  --vault ~/vaults/SEO_Project

# Lancer le serveur API
python projects/rag/scripts/api_server.py --port 5000
```

---

## 4. Intégration avec un Chatbot Site Web

### 🎯 **Solution Recommandée: Serveur API Flask**

Le fichier `scripts/api_server.py` fournit une API REST complète pour intégrer le système RAG Wiki à votre site web.

#### **Endpoints Disponibles**

| **Endpoint** | **Méthode** | **Description** | **Exemple de Requête** |
|--------------|-------------|-----------------|-----------------------|
| `/api/health` | GET | Vérifier la santé | `curl http://localhost:5000/api/health` |
| `/api/status` | GET | Statut du vault | `curl http://localhost:5000/api/status` |
| `/api/query` | POST | Poser une question | `curl -X POST -H "Content-Type: application/json" -d '{"query":"Qu'est-ce que l'IA ?"}' http://localhost:5000/api/query` |
| `/api/ingest` | POST | Ingest un fichier | `curl -X POST -H "Content-Type: application/json" -d '{"source_path":"/chemin/fichier.pdf"}' http://localhost:5000/api/ingest` |
| `/api/ocr` | POST | OCR d'un fichier | `curl -X POST -H "Content-Type: application/json" -d '{"file_path":"/chemin/fichier.pdf"}' http://localhost:5000/api/ocr` |
| `/api/search` | POST | Recherche simple | `curl -X POST -H "Content-Type: application/json" -d '{"query":"IA générative"}' http://localhost:5000/api/search` |
| `/api/list_sources` | GET | Lister les sources | `curl http://localhost:5000/api/list_sources` |
| `/api/preprocess` | POST | Prétraitement | `curl -X POST -H "Content-Type: application/json" -d '{"input_path":"/chemin/fichier.txt"}' http://localhost:5000/api/preprocess` |
| `/api/batch_ingest` | POST | Ingest en batch | `curl -X POST -H "Content-Type: application/json" -d '{"source_paths":["/chemin/fichier1.pdf","/chemin/fichier2.pdf"]}' http://localhost:5000/api/batch_ingest` |

#### **Exemple d'Intégration JavaScript**

```javascript
// Configuration
const API_URL = 'http://localhost:5000/api/query';

// Fonction pour poser une question
async function askQuestion(question) {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: question,
      top_k: 5,
      save_answer: false,
      use_hybrid: true
    })
  });
  
  const data = await response.json();
  
  if (data.success) {
    console.log('Réponse:', data.answer);
    console.log('Citations:', data.citations);
    console.log('Confiance:', data.confidence);
  } else {
    console.error('Erreur:', data.error);
  }
}

// Utilisation
askQuestion("Qu'est-ce que l'IA générative ?");
```

#### **Exemple avec HTML (chatbot_example.html)**

Un exemple complet de chatbot HTML est fourni dans `scripts/chatbot_example.html`.

Pour l'utiliser:
1. Lancez le serveur API: `python scripts/api_server.py`
2. Ouvrez `scripts/chatbot_example.html` dans votre navigateur
3. Posez des questions via l'interface

**✅ Fonctionnalités du chatbot:**
- Interface conviviale avec historique
- Indicateur de typage
- Affichage des citations
- Gestion des erreurs
- Design responsive

#### **Déploiement en Production**

Pour déployer en production avec Gunicorn:

```bash
# Installer Gunicorn
pip install gunicorn

# Lancer le serveur (4 workers, port 8000)
gunicorn -w 4 -b 0.0.0.0:8000 projects.rag.scripts.api_server:app
```

Pour un déploiement avec Docker:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copier les fichiers
COPY projects/rag /app/projects/rag

# Installer les dépendances
RUN pip install flask flask-cors httpx

# Exposer le port
EXPOSE 8000

# Lancer le serveur
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "projects.rag.scripts.api_server:app"]
```

---

## 5. Configuration pour un Vault Unique Centralisé

### 🎯 **Pourquoi un seul vault ?**

Le système est conçu pour **un vault unique** contenant toute votre connaissance.

**Avantages:**
- **Recherche globale**: Toutes vos informations sont accessibles via une seule requête
- **Cross-références**: Les pages peuvent se référencer entre elles (ex: une page sur le SEO peut lier vers une page sur l'IA)
- **Maintenance simplifiée**: Un seul endroit à mettre à jour
- **Économie de coûts**: Moins d'appels API Mistral (pas de duplication)

### 📌 **Configuration**

Dans `configs/mistral_config.json`:

```json
{
  "vault": {
    "default_path": "~/vaults/knowledge_base",
    "single_vault": true,
    "description": "Configuration pour un vault unique centralisé"
  }
}
```

### 💡 **Structure Recommandée pour le Vault**

```
~/vaults/knowledge_base/
├── raw/                          # Fichiers bruts (PDF, images, etc.)
│   ├── IA/                       # Documents sur l'IA
│   │   ├── introduction_IA.pdf
│   │   ├── llm_guide.md
│   │   └── ...
│   ├── SEO/                      # Documents sur le SEO
│   │   ├── seo_2024.pdf
│   │   ├── technical_seo.md
│   │   └── ...
│   └── Dev/                      # Documents sur le développement
│       ├── python_best_practices.md
│       └── ...
├── wiki/                         # Base de connaissances (Markdown)
│   ├── index.md                  # Catalogue de toutes les pages
│   ├── log.md                    # Historique des opérations
│   ├── entities/                 # Entités (personnes, organisations, outils)
│   │   ├── Google.md
│   │   ├── Mistral_AI.md
│   │   └── ...
│   ├── concepts/                 # Concepts (idées, théories)
│   │   ├── IA/                  # Concepts liés à l'IA
│   │   │   ├── Large_Language_Models.md
│   │   │   ├── Transformers.md
│   │   │   └── ...
│   │   ├── SEO/                 # Concepts liés au SEO
│   │   │   ├── Backlinks.md
│   │   │   ├── Core_Web_Vitals.md
│   │   │   └── ...
│   │   └── Dev/                 # Concepts liés au développement
│   │       ├── Clean_Code.md
│   │       └── ...
│   ├── sources/                  # Résumés des documents ingérés
│   │   ├── IA/
│   │   │   ├── introduction_IA.md
│   │   │   └── ...
│   │   ├── SEO/
│   │   │   ├── seo_2024.md
│   │   │   └── ...
│   │   └── Dev/
│   │       └── ...
│   ├── comparisons/              # Comparaisons entre outils/concepts
│   │   ├── Mistral_vs_OpenAI.md
│   │   └── Ahrefs_vs_SEMrush.md
│   └── synthesis/                # Synthèses et rapports
│       ├── IA_2024_Trends.md
│       ├── SEO_Strategy.md
│       └── ...
└── configs/                      # Configurations
    └── mistral_config.json       # Configuration Mistral API
```

### 🔄 **Workflow avec un Vault Unique**

1. **Ajoutez tous vos documents** dans `raw/` (organisés par thème)
2. **Ingérez-les** via `/wiki-ingest` ou `ingest_source.py`
3. **Posez des questions** via `/wiki-query` ou l'API
4. **Le système crée automatiquement** les pages dans les bons dossiers

**Exemple:**
```bash
# Ingest un document sur l'IA
python ingest_source.py --path ~/vaults/knowledge_base --source raw/IA/introduction_IA.pdf

# Ingest un document sur le SEO
python ingest_source.py --path ~/vaults/knowledge_base --source raw/SEO/seo_2024.pdf

# Poser une question qui combine les deux
python query_wiki.py --path ~/vaults/knowledge_base --query "Comment l'IA peut-elle améliorer le SEO ?"
```

---

## 6. Modèles Mistral Utilisés

### 🎯 **Configuration Complète (mistral_config.json)**

```json
{
  "llm": {
    "ingestion": {
      "model": "mistral-large-latest",
      "temperature": 0.2,
      "description": "Précision maximale pour l'ingestion"
    },
    "query": {
      "model": "mistral-large-latest",
      "temperature": 0.4,
      "description": "Équilibre précision/créativité pour les requêtes"
    },
    "preprocessing": {
      "model": "mistral-small-latest",
      "temperature": 0.0,
      "description": "Déterminisme total pour le nettoyage"
    },
    "moderation": {
      "model": "shieldstral-latest",
      "temperature": 0.0,
      "description": "Filtrage du contenu inapproprié"
    }
  },
  
  "embeddings": {
    "model": "codestral-embed",
    "dimension": 1024,
    "description": "Embeddings optimisés pour la recherche sémantique"
  },
  
  "ocr": {
    "primary": {
      "engine": "mistral-ocr",
      "model": "mistral-ocr-latest",
      "enabled": true,
      "description": "OCR via Mistral API (DISPONIBLE depuis 05/10/2026)"
    },
    "image_description": {
      "enabled": true,
      "model": "mistral-small-latest",
      "description": "Génère des descriptions contextuelles des images"
    }
  },
  
  "moderation": {
    "enabled": true,
    "model": "shieldstral-latest",
    "block_list": ["hate", "harassment", "violence", "self-harm", "sexual", "illegal", "personal_data"],
    "action": "filter"
  }
}
```

### 📌 **À quoi sert chaque modèle ?**

| **Modèle** | **Utilisation** | **Pourquoi ce modèle ?** |
|------------|----------------|--------------------------|
| `mistral-ocr-latest` | Extraction de texte depuis PDF/images | **Spécialisé OCR**, meilleure précision que les modèles LLM |
| `codestral-embed` | Génération d'embeddings | **Optimisé pour la recherche**, 1024 dimensions |
| `shieldstral-latest` | Modération de contenu | **Filtre les contenus inappropriés** avant traitement |
| `mistral-large-latest` | Ingestion, requêtes | **Contexte long** (16K tokens), précision élevée |
| `mistral-small-latest` | Prétraitement, description images | **Économique et rapide** pour les tâches simples |

### ⚠️ **Modération (Shieldstral)**

Le système utilise **shieldstral-latest** pour filtrer automatiquement:
- Contenu haineux (hate)
- Harcèlement (harassment)
- Violence
- Automutilation (self-harm)
- Contenu sexuel inapproprié
- Activités illégales
- Données personnelles

**Configuration dans `mistral_config.json`:**
```json
"moderation": {
  "enabled": true,
  "model": "shieldstral-latest",
  "block_list": ["hate", "harassment", "violence", "self-harm", "sexual", "illegal", "personal_data"],
  "action": "filter"  // ou "warn" pour juste avertir
}
```

---

## 7. Exemples Concrets

### 📌 **Cas d'Usage 1: Chatbot Site Web sur l'IA**

**Objectif:** Créer un chatbot qui répond aux questions sur l'IA en utilisant vos documents.

**Étapes:**

1. **Préparer le vault:**
   ```bash
   # Initialiser le vault
   python projects/rag/scripts/init_vault.py --path ~/vaults/IA_KnowledgeBase
   
   # Copier vos documents sur l'IA
   cp ~/Documents/IA/*.pdf ~/vaults/IA_KnowledgeBase/raw/
   ```

2. **Ingérer les documents:**
   ```bash
   # Ingest tous les PDF
   for f in ~/vaults/IA_KnowledgeBase/raw/*.pdf; do
     python projects/rag/scripts/ingest_source.py \
       --path ~/vaults/IA_KnowledgeBase \
       --source "$f"
   done
   ```

3. **Lancer le serveur API:**
   ```bash
   python projects/rag/scripts/api_server.py \
     --vault ~/vaults/IA_KnowledgeBase \
     --port 8000
   ```

4. **Intégrer à votre site web:**
   ```javascript
   // Dans votre site web
   async function askAIQuestion(question) {
     const response = await fetch('http://localhost:8000/api/query', {
       method: 'POST',
       headers: {'Content-Type': 'application/json'},
       body: JSON.stringify({query: question})
     });
     
     const data = await response.json();
     return data.answer;
   }
   
   // Utilisation
   const answer = await askAIQuestion("Explique-moi les Transformers en IA");
   console.log(answer);
   ```

**Résultat:** Votre chatbot répondra **uniquement** en se basant sur vos documents sur l'IA.

---

### 📌 **Cas d'Usage 2: Base de Connaissance SEO pour un Client**

**Objectif:** Créer une base de connaissance pour un client en SEO.

**Étapes:**

1. **Créer un vault dédié:**
   ```bash
   python projects/rag/scripts/init_vault.py --path ~/vaults/Client_X_SEO
   ```

2. **Ajouter les documents du client:**
   ```bash
   # Copier les audits SEO
   cp ~/Clients/Client_X/Audits/*.pdf ~/vaults/Client_X_SEO/raw/
   
   # Copier les stratégies
   cp ~/Clients/Client_X/Strategies/*.docx ~/vaults/Client_X_SEO/raw/
   ```

3. **Ingérer et prétraiter:**
   ```bash
   # Prétraiter et ingérer un audit
   python projects/rag/scripts/preprocess_raw.py \
     --input ~/vaults/Client_X_SEO/raw/Audit_SEO_2024.pdf \
     --vault ~/vaults/Client_X_SEO
   
   python projects/rag/scripts/ingest_source.py \
     --path ~/vaults/Client_X_SEO \
     --source ~/vaults/Client_X_SEO/raw/clean/Audit_SEO_2024.md
   ```

4. **Générer un rapport:**
   ```bash
   python projects/rag/scripts/query_wiki.py \
     --path ~/vaults/Client_X_SEO \
     --query "Génère un rapport SEO complet pour le client X avec les 5 problèmes les plus critiques et les recommandations" \
     --save true
   ```

**Résultat:** Un rapport complet généré automatiquement dans `wiki/synthesis/`.

---

### 📌 **Cas d'Usage 3: Veille Technologique**

**Objectif:** Centraliser et rechercher dans vos articles de veille.

**Étapes:**

1. **Automatiser l'ingestion:**
   ```bash
   # Script pour ingérer tous les nouveaux PDF dans un dossier
   #!/bin/bash
   VAULT="/home/user/vaults/Tech_Watch"
   WATCH_DIR="/home/user/Downloads/Veille"
   
   for file in $WATCH_DIR/*.pdf; do
     if [ -f "$file" ]; then
       python /chemin/vers/projects/rag/scripts/ingest_source.py \
         --path "$VAULT" \
         --source "$file"
       mv "$file" "$VAULT/raw/archives/"
     fi
   done
   ```

2. **Rechercher dans la veille:**
   ```bash
   # Via CLI
   python query_wiki.py --path ~/vaults/Tech_Watch --query "Quelles sont les dernières avancées en LLM ?"
   
   # Via API
   curl -X POST http://localhost:5000/api/query \
     -H "Content-Type: application/json" \
     -d '{"query":"Quelles sont les dernières avancées en LLM ?"}'
   ```

---

## 🚀 **Résumé des Bonnes Pratiques**

1. **✅ Utilisez un vault unique** pour toute votre connaissance
2. **✅ Configurez les Custom Commands** dans Open WebUI pour une utilisation facile
3. **✅ Utilisez le serveur API** pour intégrer à des sites web ou autres outils
4. **✅ Activez la modération** (shieldstral) pour filtrer le contenu inapproprié
5. **✅ Utilisez codestral-embed** pour des embeddings de qualité
6. **✅ Mistral OCR est maintenant disponible** (plus besoin de Tesseract)
7. **✅ Séparation claire des agents** (1 agent = 1 tâche majeure)

---

## 📚 **Documentation Complémentaire**

- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture technique détaillée
- [SCHEMA.md](SCHEMA.md) - Schéma des pages et métadonnées
- [README.md](README.md) - Guide général du projet
- [ROADMAP.md](ROADMAP.md) - Feuille de route des fonctionnalités

---

## 🔧 **Dépannage**

### ❌ **Problème: Mistral OCR ne fonctionne pas**

**Solution:**
1. Vérifiez que `MISTRAL_API_KEY` est défini
2. Vérifiez que le modèle `mistral-ocr-latest` est disponible
3. Vérifiez dans `mistral_config.json` que OCR est activé:
   ```json
   "ocr": {
     "primary": {
       "enabled": true
     }
   }
   ```

### ❌ **Problème: Les embeddings ne marchent pas**

**Solution:**
1. Vérifiez que le modèle est `codestral-embed` dans `mistral_config.json`
2. Vérifiez que vous avez accès à ce modèle via votre compte Mistral

### ❌ **Problème: Le serveur API plante au démarrage**

**Solution:**
1. Vérifiez que toutes les dépendances sont installées:
   ```bash
   pip install flask flask-cors httpx
   ```
2. Vérifiez que `MISTRAL_API_KEY` est défini
3. Vérifiez que le vault existe

### ❌ **Problème: Open WebUI ne trouve pas les commandes**

**Solution:**
1. Vérifiez que les chemins sont **absolus** dans les Custom Commands
2. Vérifiez que Python est dans votre PATH
3. Testez la commande directement dans le terminal pour vérifier qu'elle fonctionne

---

## 📞 **Support**

Pour toute question ou problème, consultez:
- Les logs du système (`wiki/log.md`)
- La documentation dans `docs/`
- Les exemples dans `scripts/`

**Bon usage du système RAG Wiki !** 🚀
