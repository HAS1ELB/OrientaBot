"""
Routes API pour OrientaBot
"""

# Import des modules de routes pour faciliter l'inclusion dans l'app principale
from . import chat
from . import profile  
from . import search
from . import system

__all__ = [
    "chat",
    "profile", 
    "search",
    "system"
]