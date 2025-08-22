"""
Module chat - Gestion des conversations
Contient la logique de traitement des conversations et les prompts système
"""

# Import modules seulement si les dépendances sont disponibles
try:
    from .handler import ChatHandler
    from .prompts import get_system_prompt, get_conversation_starters, get_tips_sidebar
    __all__ = ['ChatHandler', 'get_system_prompt', 'get_conversation_starters', 'get_tips_sidebar']
except ImportError:
    __all__ = []