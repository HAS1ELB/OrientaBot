"""
Modèles Pydantic pour les réponses API
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

class StatusEnum(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"

class ChatResponse(BaseModel):
    """Modèle pour les réponses de chat"""
    status: StatusEnum = Field(..., description="Statut de la réponse")
    response: str = Field(..., description="Réponse générée")
    session_id: str = Field(..., description="ID de session")
    recommendations: Optional[Dict[str, Any]] = Field(None, description="Recommandations personnalisées")
    context_used: List[Dict[str, Any]] = Field([], description="Contexte utilisé pour la réponse")
    debug_info: Optional[Dict[str, Any]] = Field(None, description="Informations de debug")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp de la réponse")
    processing_time: Optional[float] = Field(None, description="Temps de traitement en secondes")

class UserProfileResponse(BaseModel):
    """Modèle pour les réponses de profil utilisateur"""
    status: StatusEnum = Field(..., description="Statut de la réponse")
    user_id: str = Field(..., description="ID utilisateur")
    profile_data: Dict[str, Any] = Field(..., description="Données du profil")
    nombre_conversations: int = Field(0, description="Nombre de conversations")
    derniere_activite: Optional[datetime] = Field(None, description="Dernière activité")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Préférences utilisateur")
    created_at: Optional[datetime] = Field(None, description="Date de création")
    updated_at: Optional[datetime] = Field(None, description="Date de dernière mise à jour")

class SearchResultItem(BaseModel):
    """Modèle pour un élément de résultat de recherche"""
    content: str = Field(..., description="Contenu du résultat")
    score: float = Field(..., description="Score de pertinence")
    source: str = Field(..., description="Source du document")
    metadata: Dict[str, Any] = Field({}, description="Métadonnées du document")
    chunk_id: Optional[str] = Field(None, description="ID du chunk")
    
class SearchResponse(BaseModel):
    """Modèle pour les réponses de recherche"""
    status: StatusEnum = Field(..., description="Statut de la réponse")
    query: str = Field(..., description="Requête originale")
    results: List[SearchResultItem] = Field([], description="Résultats de recherche")
    total_results: int = Field(0, description="Nombre total de résultats")
    search_time: float = Field(..., description="Temps de recherche en secondes")
    mode_used: str = Field(..., description="Mode de recherche utilisé")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="Filtres appliqués")

class SystemStatsResponse(BaseModel):
    """Modèle pour les réponses de statistiques système"""
    status: StatusEnum = Field(..., description="Statut de la réponse")
    uptime: float = Field(..., description="Temps de fonctionnement en secondes")
    memory_usage: Dict[str, Any] = Field(..., description="Utilisation mémoire")
    rag_stats: Dict[str, Any] = Field(..., description="Statistiques RAG")
    chat_stats: Dict[str, Any] = Field(..., description="Statistiques de chat")
    system_info: Dict[str, Any] = Field(..., description="Informations système")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp des stats")

class SessionResponse(BaseModel):
    """Modèle pour les réponses de session"""
    status: StatusEnum = Field(..., description="Statut de la réponse")
    session_id: str = Field(..., description="ID de session")
    session_data: Optional[Dict[str, Any]] = Field(None, description="Données de session")
    created_at: Optional[datetime] = Field(None, description="Date de création")
    last_activity: Optional[datetime] = Field(None, description="Dernière activité")
    is_active: bool = Field(True, description="Session active")

class ErrorResponse(BaseModel):
    """Modèle pour les réponses d'erreur"""
    status: StatusEnum = StatusEnum.ERROR
    error_code: str = Field(..., description="Code d'erreur")
    error_message: str = Field(..., description="Message d'erreur")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Détails de l'erreur")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp de l'erreur")
    request_id: Optional[str] = Field(None, description="ID de la requête")

class InitializationResponse(BaseModel):
    """Modèle pour les réponses d'initialisation"""
    status: StatusEnum = Field(..., description="Statut de l'initialisation")
    components_initialized: List[str] = Field([], description="Composants initialisés")
    initialization_time: float = Field(..., description="Temps d'initialisation en secondes")
    warnings: List[str] = Field([], description="Avertissements")
    details: Dict[str, Any] = Field({}, description="Détails de l'initialisation")

class APIResponse(BaseModel):
    """Modèle générique de réponse API"""
    status: StatusEnum = Field(..., description="Statut de la réponse")
    message: str = Field(..., description="Message de réponse")
    data: Optional[Any] = Field(None, description="Données de la réponse")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp")