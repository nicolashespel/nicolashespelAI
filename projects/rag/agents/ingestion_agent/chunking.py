"""
Découpage intelligent du texte pour l'ingestion RAG.

Ce module divise le texte en chunks optimisés pour:
- L'indexation par embeddings
- La recherche sémantique
- La gestion des contextes longs
"""

import re
from typing import Any, Dict, List, Optional


class TextChunker:
    """
    Découpageur de texte pour l'ingestion RAG.
    
    Fonctionnalités:
    - Découpage par taille de tokens
    - Gestion de l'overlap entre chunks
    - Préservation des éléments importants (titres, code, etc.)
    - Adaptation au contenu
    """
    
    def __init__(
        self,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        max_tokens: int = 8192,
        preserve_important: Optional[List[str]] = None,
    ) -> None:
        """
        Initialiser le découpeur de texte.
        
        Args:
            chunk_size: Taille maximale d'un chunk en tokens.
            chunk_overlap: Nombre de tokens de chevauchement.
            max_tokens: Taille maximale totale.
            preserve_important: Liste des éléments à préserver ensemble.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_tokens = max_tokens
        self.preserve_important = preserve_important or [
            "titles", "authors", "dates", "citations", "code", "formulas"
        ]
        
        # Patterns pour détecter les éléments importants
        self.important_patterns = {
            "title": r'^[#\s]*[A-Z][^\n]*$',  # Lignes qui ressemblent à des titres
            "code": r'`[^`]+`|```[^`]+```',  # Blocs de code
            "formula": r'\$[^\$]+\$|\\begin\{[^}]+\}\\end\{[^}]+\}',  # Formules LaTeX
            "citation": r'\[[^\]]+\]',  # Citations
        }
    
    def _count_tokens(self, text: str) -> int:
        """Estimer le nombre de tokens dans un texte."""
        # Estimation simple: environ 4 caractères par token
        return len(text) // 4
    
    def _is_important_block(self, text: str) -> bool:
        """Vérifier si un bloc de texte est important."""
        for pattern_type, pattern in self.important_patterns.items():
            if pattern_type in self.preserve_important:
                if re.search(pattern, text, re.MULTILINE):
                    return True
        return False
    
    def _split_at_boundary(self, text: str, max_length: int) -> List[str]:
        """Diviser le texte à une frontière naturelle."""
        # Frontières naturelles
        boundaries = [".\n", "!\n", "?\n", "\n\n", "\n", " "]
        
        for boundary in boundaries:
            parts = text.split(boundary)
            if len(parts) > 1:
                # Trouver la meilleure position pour diviser
                current_length = 0
                chunks = []
                current_chunk = ""
                
                for part in parts:
                    if current_chunk:
                        test_chunk = current_chunk + boundary + part
                    else:
                        test_chunk = part
                    
                    token_count = self._count_tokens(test_chunk)
                    
                    if token_count <= max_length:
                        current_chunk = test_chunk
                        current_length = token_count
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = part
                        current_length = self._count_tokens(part)
                
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Si on a divisé, retourner
                if len(chunks) > 1:
                    return chunks
        
        # Si aucune frontière naturelle trouvée, diviser à la position max
        return [text[:max_length], text[max_length:]]
    
    def _create_overlap(self, previous_chunk: str, current_chunk: str, overlap_size: int) -> str:
        """Créer un chevauchement entre deux chunks."""
        if not previous_chunk:
            return current_chunk
        
        # Prendre la fin du chunk précédent
        overlap = previous_chunk[-overlap_size:] if len(previous_chunk) >= overlap_size else previous_chunk
        
        # Ajouter au début du chunk courant
        return overlap + current_chunk
    
    def chunk_text(
        self,
        text: str,
        custom_chunk_size: Optional[int] = None,
        custom_overlap: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Découper le texte en chunks.
        
        Args:
            text: Texte à découper.
            custom_chunk_size: Taille de chunk personnalisée.
            custom_overlap: Chevauchement personnalisé.
            
        Returns:
            Liste de chunks avec métadonnées.
        """
        chunk_size = custom_chunk_size or self.chunk_size
        overlap = custom_overlap or self.chunk_overlap
        
        if not text or len(text.strip()) == 0:
            return []
        
        # Calculer la taille cible en caractères (estimation)
        target_size = chunk_size * 4
        overlap_size = overlap * 4
        
        chunks = []
        remaining_text = text
        chunk_index = 0
        
        while remaining_text:
            # Vérifier si le texte restant est un bloc important
            if self._is_important_block(remaining_text) and len(remaining_text) <= target_size * 2:
                # Prendre le bloc important en entier
                chunk_text = remaining_text
                remaining_text = ""
            else:
                # Diviser à la frontière la plus proche
                if len(remaining_text) <= target_size:
                    chunk_text = remaining_text
                    remaining_text = ""
                else:
                    parts = self._split_at_boundary(remaining_text, target_size)
                    chunk_text = parts[0]
                    remaining_text = parts[1] if len(parts) > 1 else ""
            
            # Créer le chunk
            chunk = {
                "index": chunk_index,
                "text": chunk_text,
                "token_count": self._count_tokens(chunk_text),
                "char_count": len(chunk_text),
                "is_important": self._is_important_block(chunk_text),
            }
            
            chunks.append(chunk)
            chunk_index += 1
        
        # Appliquer le chevauchement
        if overlap > 0 and len(chunks) > 1:
            final_chunks = []
            
            for i, chunk in enumerate(chunks):
                if i == 0:
                    final_chunks.append(chunk)
                else:
                    # Créer le chevauchement
                    overlapped_text = self._create_overlap(
                        chunks[i-1]["text"],
                        chunk["text"],
                        overlap_size,
                    )
                    
                    overlapped_chunk = chunk.copy()
                    overlapped_chunk["text"] = overlapped_text
                    overlapped_chunk["token_count"] = self._count_tokens(overlapped_text)
                    overlapped_chunk["char_count"] = len(overlapped_text)
                    
                    final_chunks.append(overlapped_chunk)
            
            chunks = final_chunks
        
        return chunks
    
    def chunk_file(
        self,
        file_path: str,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Découper un fichier en chunks.
        
        Args:
            file_path: Chemin du fichier.
            **kwargs: Arguments à passer à chunk_text.
            
        Returns:
            Liste de chunks.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            return self.chunk_text(text, **kwargs)
            
        except Exception as e:
            return [{
                "error": str(e),
                "file": file_path,
            }]
