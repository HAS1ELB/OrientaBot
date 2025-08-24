"""
Modèles Pydantic pour les requêtes API
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime

class ChatRequest(BaseModel):
    """Modèle pour les requêtes de chat"""
    message: str = Field(..., description="Message de l'utilisateur")
    session_id: Optional[str] = Field(None, description="ID de session pour le suivi")
    user_profile: Optional[Dict[str, Any]] = Field(None, description="Profil utilisateur")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Température du modèle")
    stream: bool = Field(False, description="Streaming de la réponse")
    conversation_history: Optional[List[Dict[str, str]]] = Field([], description="Historique de conversation")
    
class UserProfileRequest(BaseModel):
    """Modèle pour les requêtes de profil utilisateur"""
    user_id: Optional[str] = Field(None, description="ID utilisateur")
    nom: Optional[str] = Field(None, description="Nom de l'utilisateur")
    filiere: Optional[str] = Field(None, description="Filière d'études")
    niveau_scolaire: Optional[str] = Field(None, description="Niveau scolaire")
    ville: Optional[str] = Field(None, description="Ville de résidence")
    interets: Optional[List[str]] = Field([], description="Centres d'intérêt")
    competences: Optional[List[str]] = Field([], description="Compétences")
    resultats_academiques: Optional[Dict[str, Any]] = Field(None, description="Résultats académiques")
    contraintes: Optional[List[str]] = Field([], description="Contraintes")
    objectifs: Optional[List[str]] = Field([], description="Objectifs")
    
class SearchRequest(BaseModel):
    """Modèle pour les requêtes de recherche RAG"""
    query: str = Field(..., description="Requête de recherche")
    mode: str = Field("hybrid", description="Mode de recherche: 'semantic', 'keyword', ou 'hybrid'")
    max_results: int = Field(5, ge=1, le=20, description="Nombre maximum de résultats")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="Score minimum pour filtrer les résultats")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filtres de recherche")
    
class SessionRequest(BaseModel):
    """Modèle pour les requêtes de session"""
    session_id: str = Field(..., description="ID de session")
    action: str = Field(..., description="Action: 'create', 'get', 'update', 'delete'")
    data: Optional[Dict[str, Any]] = Field(None, description="Données de session")

class SystemStatsRequest(BaseModel):
    """Modèle pour les requêtes de statistiques système"""
    include_detailed: bool = Field(False, description="Inclure les statistiques détaillées")
    component: Optional[str] = Field(None, description="Composant spécifique: 'rag', 'chat', 'memory'")

class InitializationRequest(BaseModel):
    """Modèle pour les requêtes d'initialisation"""
    force_rebuild: bool = Field(False, description="Forcer la reconstruction des index")
    component: Optional[str] = Field(None, description="Composant à initialiser")
    config_override: Optional[Dict[str, Any]] = Field(None, description="Surcharge de configuration")