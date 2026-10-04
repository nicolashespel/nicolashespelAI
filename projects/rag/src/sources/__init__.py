"""
Module Sources - Parsers de sources pour le système RAG Wiki.
"""

from .base_parser import BaseParser
from .pdf_parser import PDFParser
from .html_parser import HTMLParser
from .md_parser import MarkdownParser
from .txt_parser import TextParser


def get_parser_for_type(source_type: str) -> BaseParser:
    """
    Obtenir le parser approprié pour un type de source.
    
    Args:
        source_type: Type de source (pdf, html, markdown, text).
        
    Returns:
        Parser approprié.
    """
    parser_map = {
        "pdf": PDFParser(),
        "html": HTMLParser(),
        "markdown": MarkdownParser(),
        "md": MarkdownParser(),
        "text": TextParser(),
        "txt": TextParser(),
    }
    
    return parser_map.get(source_type, TextParser())
