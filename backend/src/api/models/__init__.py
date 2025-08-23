"""
Modèles Pydantic pour l'API OrientaBot
"""
from .requests import (
    ChatRequest,
    UserProfileRequest, 
    SearchRequest,
    SessionRequest,
    SystemStatsRequest,
    InitializationRequest
)

from .responses import (
    ChatResponse,
    UserProfileResponse,
    SearchResponse,
    SearchResultItem,
    SystemStatsResponse,
    SessionResponse,
    ErrorResponse,
    InitializationResponse,
    APIResponse,
    StatusEnum
)

__all__ = [
    # Requests
    "ChatRequest",
    "UserProfileRequest",
    "SearchRequest", 
    "SessionRequest",
    "SystemStatsRequest",
    "InitializationRequest",
    
    # Responses
    "ChatResponse",
    "UserProfileResponse", 
    "SearchResponse",
    "SearchResultItem",
    "SystemStatsResponse",
    "SessionResponse",
    "ErrorResponse",
    "InitializationResponse",
    "APIResponse",
    "StatusEnum"
]