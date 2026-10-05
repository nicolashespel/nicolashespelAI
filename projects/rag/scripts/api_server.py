#!/usr/bin/env python3
"""
Serveur API Flask pour intégrer le système RAG Wiki à un chatbot site web.

Ce serveur permet d'exposer les fonctionnalités du système RAG Wiki via une API REST.
Utilisation :
1. Lancez le serveur : python scripts/api_server.py
2. Envoyez des requêtes POST à http://localhost:5000/api/query avec {"query": "votre question"}
3. Le serveur répondra avec le résultat de la recherche dans votre vault.

Exemple d'intégration avec un chatbot JavaScript :
```javascript
fetch('http://localhost:5000/api/query', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({query: "Qu'est-ce que l'IA générative ?"})
})
.then(response => response.json())
.then(data => console.log(data.answer));
```
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask, request, jsonify, abort
from flask_cors import CORS

# Ajouter le chemin parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.wiki_librarian import WikiLibrarianAgent
from src.agents.wiki_ingestor import WikiIngestorAgent
from src.agents.ocr_agent import OCRAgent
from src.core.config import WikiConfig


app = Flask(__name__)
CORS(app)  # Autoriser les requêtes CORS pour le chatbot


# Configuration globale
VAULT_PATH = Path(os.getenv("RAG_VAULT_PATH", "~/vaults/knowledge_base")).expanduser()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Initialiser les agents (lazy loading)
_agents = {}


def get_librarian_agent() -> WikiLibrarianAgent:
    """Récupérer ou créer l'agent WikiLibrarian."""
    if "librarian" not in _agents:
        config = WikiConfig(vault_path=VAULT_PATH)
        _agents["librarian"] = WikiLibrarianAgent(
            vault_path=VAULT_PATH,
            config=config,
            api_key=MISTRAL_API_KEY,
        )
    return _agents["librarian"]


def get_ingestor_agent() -> WikiIngestorAgent:
    """Récupérer ou créer l'agent WikiIngestor."""
    if "ingestor" not in _agents:
        config = WikiConfig(vault_path=VAULT_PATH)
        _agents["ingestor"] = WikiIngestorAgent(
            vault_path=VAULT_PATH,
            config=config,
            api_key=MISTRAL_API_KEY,
        )
    return _agents["ingestor"]


def get_ocr_agent() -> OCRAgent:
    """Récupérer ou créer l'agent OCRAgent."""
    if "ocr" not in _agents:
        config = WikiConfig(vault_path=VAULT_PATH)
        _agents["ocr"] = OCRAgent(
            vault_path=VAULT_PATH,
            config=config,
            api_key=MISTRAL_API_KEY,
        )
    return _agents["ocr"]


@app.route('/api/health', methods=['GET'])
def health_check():
    """Vérifier que le serveur est en vie."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "vault_path": str(VAULT_PATH),
        "agents_loaded": list(_agents.keys()),
    })


@app.route('/api/query', methods=['POST'])
async def query():
    """
    Poser une question au vault.
    
    Requête POST : {"query": "votre question", "top_k": 5, "save_answer": true}
    Réponse : {"answer": "...", "citations": [...], "confidence": 0.85, "sources": [...]}
    """
    data = request.get_json()
    if not data or 'query' not in data:
        abort(400, description="Le champ 'query' est requis")
    
    try:
        librarian = get_librarian_agent()
        
        result = await librarian.execute(
            query=data['query'],
            top_k=data.get('top_k', 5),
            save_answer=data.get('save_answer', True),
            use_hybrid=data.get('use_hybrid', True),
        )
        
        # Formater la réponse
        response = {
            "success": result["success"],
            "query": result["query"],
            "answer": result["answer"],
            "citations": result["citations"],
            "confidence": result["confidence"],
            "sources": result["sources"],
            "duration_seconds": result["duration_seconds"],
            "timestamp": datetime.now().isoformat(),
        }
        
        if not result["success"]:
            response["error"] = result.get("error", "Erreur inconnue")
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }), 500


@app.route('/api/ingest', methods=['POST'])
async def ingest():
    """
    Ingest un fichier dans le vault.
    
    Requête POST : {"source_path": "/chemin/vers/fichier.pdf", "preprocess": true}
    Réponse : {"success": true, "summary_page": "...", "updated_pages": [...]}
    """
    data = request.get_json()
    if not data or 'source_path' not in data:
        abort(400, description="Le champ 'source_path' est requis")
    
    try:
        source_path = Path(data['source_path'])
        if not source_path.is_absolute():
            source_path = VAULT_PATH / source_path
        
        if not source_path.exists():
            return jsonify({
                "success": False,
                "error": f"Fichier non trouvé: {source_path}",
                "timestamp": datetime.now().isoformat(),
            }), 404
        
        ingestor = get_ingestor_agent()
        
        result = await ingestor.execute(
            source_path=source_path,
            preprocess=data.get('preprocess', True),
            ask_for_confirmation=data.get('ask_for_confirmation', True),
            describe_images=data.get('describe_images', True),
        )
        
        return jsonify({
            "success": result["success"],
            "source_path": result["source_path"],
            "preprocessed": result.get("preprocessed", False),
            "ingestion_report": result.get("ingestion_report", {}),
            "timestamp": datetime.now().isoformat(),
            "error": result.get("error"),
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }), 500


@app.route('/api/ocr', methods=['POST'])
async def ocr():
    """
    Extraire le texte d'un fichier via OCR.
    
    Requête POST : {"file_path": "/chemin/vers/fichier.pdf", "describe_images": true}
    Réponse : {"success": true, "text": "...", "report": {...}}
    """
    data = request.get_json()
    if not data or 'file_path' not in data:
        abort(400, description="Le champ 'file_path' est requis")
    
    try:
        file_path = Path(data['file_path'])
        if not file_path.is_absolute():
            file_path = VAULT_PATH / file_path
        
        if not file_path.exists():
            return jsonify({
                "success": False,
                "error": f"Fichier non trouvé: {file_path}",
                "timestamp": datetime.now().isoformat(),
            }), 404
        
        ocr_agent = get_ocr_agent()
        
        success, text, report = await ocr_agent.extract_text(
            file_path=file_path,
            context=data.get('context'),
            describe_images=data.get('describe_images', True),
        )
        
        return jsonify({
            "success": success,
            "text": text,
            "report": report,
            "timestamp": datetime.now().isoformat(),
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }), 500


@app.route('/api/status', methods=['GET'])
async def status():
    """
    Obtenir le statut du vault.
    
    Réponse : {"raw_files": 10, "wiki_pages": 25, "entities": 5, ...}
    """
    try:
        # Compter les fichiers
        raw_files = len(list(VAULT_PATH.glob("raw/**/*"))) if (VAULT_PATH / "raw").exists() else 0
        wiki_pages = len(list(VAULT_PATH.glob("wiki/**/*.md"))) if (VAULT_PATH / "wiki").exists() else 0
        entities = len(list((VAULT_PATH / "wiki" / "entities").glob("*.md"))) if (VAULT_PATH / "wiki" / "entities").exists() else 0
        concepts = len(list((VAULT_PATH / "wiki" / "concepts").glob("*.md"))) if (VAULT_PATH / "wiki" / "concepts").exists() else 0
        sources = len(list((VAULT_PATH / "wiki" / "sources").glob("*.md"))) if (VAULT_PATH / "wiki" / "sources").exists() else 0
        synthesis = len(list((VAULT_PATH / "wiki" / "synthesis").glob("*.md"))) if (VAULT_PATH / "wiki" / "synthesis").exists() else 0
        
        return jsonify({
            "vault_path": str(VAULT_PATH),
            "raw_files": raw_files,
            "wiki_pages": wiki_pages,
            "entities": entities,
            "concepts": concepts,
            "sources": sources,
            "synthesis": synthesis,
            "timestamp": datetime.now().isoformat(),
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }), 500


@app.route('/api/list_sources', methods=['GET'])
async def list_sources():
    """
    Lister toutes les sources dans le vault.
    
    Réponse : {"sources": [{"path": "...", "title": "...", "type": "..."}, ...]}
    """
    try:
        sources = []
        sources_dir = VAULT_PATH / "wiki" / "sources"
        
        if sources_dir.exists():
            for md_file in sources_dir.glob("*.md"):
                # Lire les métadonnées YAML
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Extraire le titre et le type
                title = md_file.stem.replace("_", " ")
                source_type = "source"
                
                # Chercher le type dans le YAML
                if content.startswith("---"):
                    yaml_end = content.find("---", 3)
                    if yaml_end != -1:
                        yaml_content = content[3:yaml_end]
                        for line in yaml_content.split('\n'):
                            if line.strip().startswith("title:"):
                                title = line.strip().split(":", 1)[1].strip().strip('"')
                            if line.strip().startswith("type:"):
                                source_type = line.strip().split(":", 1)[1].strip().strip('"')
                
                sources.append({
                    "path": str(md_file.relative_to(VAULT_PATH)),
                    "title": title,
                    "type": source_type,
                })
        
        return jsonify({"sources": sources, "timestamp": datetime.now().isoformat()})
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }), 500


@app.route('/api/search', methods=['POST'])
async def search():
    """
    Recherche simple dans le vault (sans synthèse LLM).
    
    Requête POST : {"query": "votre requête", "top_k": 5}
    Réponse : {"results": [{"path": "...", "content": "...", "score": 0.85}, ...]}
    """
    data = request.get_json()
    if not data or 'query' not in data:
        abort(400, description="Le champ 'query' est requis")
    
    try:
        librarian = get_librarian_agent()
        
        # Recherche simple (sans synthèse)
        results = await librarian._search(
            query=data['query'],
            top_k=data.get('top_k', 5),
            use_hybrid=data.get('use_hybrid', True),
        )
        
        return jsonify({
            "success": True,
            "query": data['query'],
            "results": results.get("sources", []),
            "timestamp": datetime.now().isoformat(),
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }), 500


@app.route('/api/preprocess', methods=['POST'])
async def preprocess():
    """
    Prétraiter un fichier (nettoyage, déduplication).
    
    Requête POST : {"input_path": "/chemin/vers/fichier.txt", "ask_for_confirmation": true}
    Réponse : {"success": true, "output_path": "...", "report": {...}}
    """
    data = request.get_json()
    if not data or 'input_path' not in data:
        abort(400, description="Le champ 'input_path' est requis")
    
    try:
        from src.agents.preprocessing_agent import PreprocessingAgent
        
        input_path = Path(data['input_path'])
        if not input_path.is_absolute():
            input_path = VAULT_PATH / input_path
        
        if not input_path.exists():
            return jsonify({
                "success": False,
                "error": f"Fichier non trouvé: {input_path}",
                "timestamp": datetime.now().isoformat(),
            }), 404
        
        preprocessing_agent = PreprocessingAgent(VAULT_PATH)
        
        success, output_path, report = await preprocessing_agent.preprocess(
            input_path=input_path,
            ask_for_confirmation=data.get('ask_for_confirmation', True),
        )
        
        return jsonify({
            "success": success,
            "input_path": str(input_path),
            "output_path": str(output_path) if output_path else "",
            "report": report,
            "timestamp": datetime.now().isoformat(),
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }), 500


@app.route('/api/batch_ingest', methods=['POST'])
async def batch_ingest():
    """
    Ingest plusieurs fichiers en batch.
    
    Requête POST : {"source_paths": ["/chemin/vers/fichier1.pdf", "/chemin/vers/fichier2.pdf"]}
    Réponse : {"successful": 2, "failed": 0, "results": {...}}
    """
    data = request.get_json()
    if not data or 'source_paths' not in data:
        abort(400, description="Le champ 'source_paths' est requis")
    
    try:
        source_paths = [Path(p) for p in data['source_paths']]
        
        # Résoudre les chemins
        resolved_paths = []
        for path in source_paths:
            if not path.is_absolute():
                path = VAULT_PATH / path
            if path.exists():
                resolved_paths.append(path)
        
        if not resolved_paths:
            return jsonify({
                "success": False,
                "error": "Aucun fichier valide trouvé",
                "timestamp": datetime.now().isoformat(),
            }), 400
        
        ingestor = get_ingestor_agent()
        
        result = await ingestor.ingest_batch(
            source_paths=resolved_paths,
            preprocess=data.get('preprocess', True),
            describe_images=data.get('describe_images', True),
        )
        
        return jsonify({
            "success": True,
            "total_sources": result["total_sources"],
            "successful": result["successful"],
            "failed": result["failed"],
            "results": result["sources"],
            "timestamp": datetime.now().isoformat(),
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }), 500


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Fermer les agents à la fin de la requête."""
    for name, agent in _agents.items():
        if hasattr(agent, 'close'):
            try:
                if asyncio.iscoroutinefunction(agent.close):
                    asyncio.run(agent.close())
                else:
                    agent.close()
            except Exception:
                pass
    _agents.clear()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Serveur API pour le système RAG Wiki")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Hôte du serveur")
    parser.add_argument("--port", type=int, default=5000, help="Port du serveur")
    parser.add_argument("--vault", type=str, default="~/vaults/knowledge_base", help="Chemin du vault")
    parser.add_argument("--debug", action="store_true", help="Mode debug")
    
    args = parser.parse_args()
    
    # Mettre à jour VAULT_PATH
    VAULT_PATH = Path(args.vault).expanduser()
    
    # Créer le vault si inexistant
    if not VAULT_PATH.exists():
        VAULT_PATH.mkdir(parents=True, exist_ok=True)
        (VAULT_PATH / "raw").mkdir(exist_ok=True)
        (VAULT_PATH / "wiki").mkdir(exist_ok=True)
        print(f"Vault créé: {VAULT_PATH}")
    
    print(f"Démarrage du serveur API RAG Wiki...")
    print(f"Vault: {VAULT_PATH}")
    print(f"URL: http://{args.host}:{args.port}")
    print(f"Endpoints disponibles:")
    print(f"  - GET  /api/health       - Vérifier la santé")
    print(f"  - GET  /api/status       - Statut du vault")
    print(f"  - GET  /api/list_sources - Lister les sources")
    print(f"  - POST /api/query        - Poser une question")
    print(f"  - POST /api/search       - Recherche simple")
    print(f"  - POST /api/ingest       - Ingest un fichier")
    print(f"  - POST /api/batch_ingest - Ingest en batch")
    print(f"  - POST /api/ocr          - OCR d'un fichier")
    print(f"  - POST /api/preprocess   - Prétraitement")
    
    app.run(host=args.host, port=args.port, debug=args.debug)
