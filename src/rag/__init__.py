"""
Module rag - Retrieval Augmented Generation
Contient le système RAG pour la recherche et l'augmentation de contexte
"""

# Import modules seulement si les dépendances sont disponibles
try:
    from .manager import RAGManager
    from .vector_store import VectorStore
    from .pdf_processor import PDFProcessor, DocumentChunk
    __all__ = ['RAGManager', 'VectorStore', 'PDFProcessor', 'DocumentChunk']
except ImportError as e:
    print(f"Warning: RAG dependencies not available: {e}")
    __all__ = []