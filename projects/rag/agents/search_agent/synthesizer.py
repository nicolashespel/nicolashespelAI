"""
Synthétiseur de réponses avec Mistral Large.

Ce module utilise Mistral Large pour:
- Générer des réponses complètes
- Synthétiser les informations des documents
- Ajouter des citations automatiques
- Formater les réponses en Markdown
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class ResponseSynthesizer:
    """
    Synthétiseur de réponses utilisant Mistral Large.
    
    Fonctionnalités:
    - Génération de réponses complètes
    - Synthèse des informations
    - Ajout de citations
    - Formatage en Markdown
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base_url: str = "https://api.mistral.ai/v1",
        model: str = "mistral-large-latest",
        temperature: float = 0.4,
        max_tokens: int = 4096,
        timeout: float = 120.0,
        max_retries: int = 3,
    ) -> None:
        """
        Initialiser le synthétiseur.
        
        Args:
            api_key: Clé API Mistral.
            api_base_url: URL de base de l'API.
            model: Modèle pour la synthèse.
            temperature: Température du modèle.
            max_tokens: Nombre maximal de tokens.
            timeout: Timeout en secondes.
            max_retries: Nombre de tentatives maximales.
        """
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Clé API Mistral requise. "
                "Définissez MISTRAL_API_KEY ou passez api_key."
            )
        
        self.api_base_url = api_base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Client HTTP
        self.client = httpx.AsyncClient(
            base_url=self.api_base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        
        # Prompt système pour la synthèse
        self.system_prompt = """
Tu es un assistant expert dans la synthèse d'informations pour un système RAG.
Ta tâche est de générer des réponses complètes et précises à partir des documents fournis.

## Instructions

1. **Analyse la requête** : Comprends exactement ce que l'utilisateur cherche.
2. **Analyse les documents** : Lis attentivement tous les documents fournis.
3. **Synthétise les informations** : Combine les informations pertinentes des documents.
4. **Génère une réponse** : Crée une réponse complète, bien structurée et précise.
5. **Ajoute des citations** : Utilise [[doc_id]] pour citer les sources.
6. **Formate en Markdown** : Utilise une mise en forme claire avec titres et listes.

## Format de la réponse

### Pour une réponse simple:
```markdown
**Réponse:** [Réponse concise avec citations]

**Sources:**
- [[doc_id_1]]
- [[doc_id_2]]
```

### Pour une réponse détaillée:
```markdown
## [Titre de la réponse]

[Réponse détaillée en markdown avec citations inline]

### Points clés
- Point 1 [[doc_id_1]]
- Point 2 [[doc_id_2]]

### Références
- [[doc_id_1]]
- [[doc_id_2]]

**Souhaitez-vous sauvegarder cette réponse comme une nouvelle page ?** (Oui/Non)
```

## Règles importantes

1. **Toujours citer** : Chaque affirmation doit être supportée par au moins une citation.
2. **Être précis** : Ne pas inventer d'informations, se baser uniquement sur les documents.
3. **Être complet** : Inclure toutes les informations pertinentes des documents.
4. **Signaler les limites** : Si les documents ne contiennent pas assez d'informations, le dire.
5. **Signaler les contradictions** : Si les documents se contredisent, le mentionner.

## Exemple

Requête: "Qu'est-ce que le mécanisme d'attention ?"

Documents:
- doc_1: "Le mécanisme d'attention permet aux transformers de se concentrer sur différentes parties de l'entrée..."
- doc_2: "L'attention est calculée avec des poids qui déterminent l'importance relative..."

Réponse:
```markdown
## Mécanisme d'Attention

Le mécanisme d'attention est un composant fondamental des architectures Transformer qui permet au modèle de se concentrer sur différentes parties de l'entrée lors de la génération de chaque partie de la sortie [[doc_1]].

### Fonctionnement
Le mécanisme calcule des poids d'attention qui déterminent l'importance relative de chaque élément de la séquence d'entrée [[doc_2]].

### Importance
Ce mécanisme permet aux Transformers de capturer des dépendances à long terme [[doc_1]].

**Sources:**
- [[doc_1]]
- [[doc_2]]
```
"""
    
    def _get_api_key(self) -> str:
        """Obtenir la clé API."""
        return self.api_key or os.getenv("MISTRAL_API_KEY", "")
    
    async def _make_request(
        self,
        messages: List[Dict[str, Any]],
        retry_count: int = 0,
    ) -> str:
        """Effectuer une requête à l'API."""
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "stream": False,
                },
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extraire le contenu
            choices = result.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            
            return ""
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and retry_count < self.max_retries:
                await asyncio.sleep(1)
                return await self._make_request(messages, retry_count + 1)
            
            logger.error(f"Erreur API: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la requête: {e}")
            raise
    
    async def synthesize(
        self,
        query: str,
        results: List[Dict[str, Any]],
        include_citations: bool = True,
        include_sources: bool = True,
        format: str = "detailed",
    ) -> Dict[str, Any]:
        """
        Synthétiser une réponse à partir des résultats de recherche.
        
        Args:
            query: Requête de recherche.
            results: Liste de résultats de recherche.
            include_citations: Inclure les citations.
            include_sources: Inclure la liste des sources.
            format: Format de la réponse (simple, detailed).
            
        Returns:
            Réponse synthétisée.
        """
        if not results:
            return {
                "success": False,
                "query": query,
                "answer": "Aucun résultat trouvé pour cette requête.",
                "sources": [],
                "citations": [],
            }
        
        # Préparer les documents pour le contexte
        context_documents = []
        for i, result in enumerate(results):
            doc_id = result.get("doc_id", f"doc_{i}")
            text = result.get("text", "") or result.get("content", "")
            
            # Limiter la taille du texte pour le contexte
            if len(text) > 4000:
                text = text[:4000] + "..."
            
            context_documents.append({
                "doc_id": doc_id,
                "text": text,
                "metadata": result.get("metadata", {}),
            })
        
        # Créer le prompt
        context_str = "\n\n".join(
            f"**Document {i+1} (ID: {doc['doc_id']}):**\n{doc['text']}"
            for i, doc in enumerate(context_documents)
        )
        
        prompt = f"""
{self.system_prompt}

## Requête actuelle

{query}

## Documents pertinents

{context_str}

## Génère une réponse
"""
        
        # Ajouter des instructions spécifiques selon le format
        if format == "simple":
            prompt += "\n\nRéponds de manière concise (1-2 paragraphes maximum)."
        elif format == "detailed":
            prompt += "\n\nRéponds de manière détaillée et complète."
        
        messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            }
        ]
        
        try:
            response = await self._make_request(messages)
            
            # Parser la réponse
            # Extraire les citations (format [[doc_id]])
            citations = []
            if include_citations:
                import re
                citations = re.findall(r'\[\[(.*?)\]\]', response)
            
            # Extraire les sources
            sources = list(set(citations))
            
            return {
                "success": True,
                "query": query,
                "answer": response,
                "sources": sources if include_sources else [],
                "citations": citations if include_citations else [],
                "results_used": len(results),
                "confidence": self._calculate_confidence(results, response),
            }
            
        except Exception as e:
            logger.error(f"Échec de la synthèse: {e}")
            return {
                "success": False,
                "query": query,
                "answer": f"Erreur lors de la synthèse: {e}",
                "sources": [],
                "citations": [],
            }
    
    def _calculate_confidence(
        self,
        results: List[Dict[str, Any]],
        answer: str,
    ) -> float:
        """Calculer un score de confiance."""
        if not results:
            return 0.0
        
        # Calculer la confiance basée sur:
        # - Nombre de résultats
        # - Scores des résultats
        # - Présence de citations dans la réponse
        
        # Score de base
        confidence = 0.5
        
        # Ajouter pour le nombre de résultats
        num_results = min(len(results), 5)
        confidence += num_results * 0.1
        
        # Ajouter pour les scores
        total_score = sum(
            result.get("combined_score", 0) or
            result.get("score", 0) or
            result.get("similarity", 0)
            for result in results
        )
        avg_score = total_score / len(results) if results else 0
        confidence += avg_score * 0.2
        
        # Ajouter pour les citations
        import re
        citations = re.findall(r'\[\[(.*?)\]\]', answer)
        confidence += min(len(citations) * 0.05, 0.2)
        
        # Clamper entre 0 et 1
        return min(max(confidence, 0.0), 1.0)
    
    async def summarize(
        self,
        documents: List[str],
        query: Optional[str] = None,
    ) -> str:
        """
        Résumer une liste de documents.
        
        Args:
            documents: Liste de textes à résumer.
            query: Requête pour un résumé ciblé.
            
        Returns:
            Résumé des documents.
        """
        context = "\n\n".join(documents)
        
        if query:
            prompt = f"""
Résumé les documents suivants en répondant spécifiquement à la question: {query}

Documents:
{context}

Résumé:
"""
        else:
            prompt = f"""
Résumé les documents suivants de manière concise et complète.

Documents:
{context}

Résumé:
"""
        
        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]
        
        try:
            return await self._make_request(messages)
        except Exception as e:
            logger.error(f"Échec du résumé: {e}")
            return f"Erreur lors du résumé: {e}"
    
    async def generate_title(
        self,
        query: str,
        answer: str,
    ) -> str:
        """
        Générer un titre pour une réponse.
        
        Args:
            query: Requête de recherche.
            answer: Réponse générée.
            
        Returns:
            Titre pour la réponse.
        """
        prompt = f"""
Génère un titre concis (3-8 mots) pour la réponse suivante à la requête: "{query}"

Réponse:
{answer[:500]}

Titre:
"""
        
        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]
        
        try:
            response = await self._make_request(messages)
            # Nettoyer le titre
            title = response.strip()
            title = title.replace('"', '').replace("'", "").replace("\n", " ")
            return title[:100]  # Limiter à 100 caractères
        except Exception as e:
            logger.error(f"Échec de la génération du titre: {e}")
            return query[:50]  # Utiliser la requête comme titre par défaut
    
    async def save_response(
        self,
        query: str,
        answer: str,
        vault_path: Union[Path, str],
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Sauvegarder une réponse comme une nouvelle page wiki.
        
        Args:
            query: Requête de recherche.
            answer: Réponse à sauvegarder.
            vault_path: Chemin du vault.
            title: Titre de la page (optionnel).
            tags: Tags pour la page (optionnel).
            
        Returns:
            Chemin de la page sauvegardée.
        """
        vault_path = Path(vault_path)
        synthesis_dir = vault_path / "wiki" / "synthesis"
        synthesis_dir.mkdir(parents=True, exist_ok=True)
        
        # Générer un titre si non fourni
        if not title:
            title = await self.generate_title(query, answer)
        
        # Nettoyer le titre pour le nom de fichier
        filename = title.lower().replace(" ", "_").replace("'", "").replace('"', "")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        page_path = synthesis_dir / f"{timestamp}_{filename}.md"
        
        # Créer le contenu de la page
        content = f"""---
type: synthesis
title: {title}
description: Réponse à "{query}"
query: {query}
tags: {tags or ['auto-generated']}
related: []
sources: []
created: {datetime.now().isoformat()}
updated: {datetime.now().isoformat()}
---

# {title}

**Requête:** {query}

{answer}

---

*Généré automatiquement par le système RAG*
"""
        
        # Sauvegarder la page
        with open(page_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Réponse sauvegardée: {page_path}")
        return str(page_path)
    
    async def close(self) -> None:
        """Fermer le client HTTP."""
        await self.client.aclose()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.run(self.close())
