"""
Module core - Configuration et gestion de session
Contient les fonctionnalités principales de configuration et de gestion des sessions
"""

from backend.src.core.config import *

# Import SessionManager seulement si streamlit est disponible
try:
    from .session_manager import SessionManager
    __all__ = ['SessionManager']
except ImportError:
    __all__ = []