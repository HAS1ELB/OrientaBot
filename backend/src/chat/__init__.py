"""
Module chat - Gestion des conversations
Contient la logique de traitement des conversations et les prompts systeme
"""

from .handler import ChatHandler
from .enhanced_handler import EnhancedChatHandler
from .prompts import get_system_prompt, get_conversation_starters, get_tips_sidebar
from .enhanced_prompts import get_enhanced_system_prompt

__all__ = [
    'ChatHandler', 
    'EnhancedChatHandler',
    'get_system_prompt', 
    'get_conversation_starters', 
    'get_tips_sidebar',
    'get_enhanced_system_prompt'
]