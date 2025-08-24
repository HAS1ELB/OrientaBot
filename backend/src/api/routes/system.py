"""
Routes API pour les informations et statistiques système
"""
from fastapi import APIRouter, HTTPException
import time
import psutil
import os
import logging
from datetime import datetime

from api.models import (
    SystemStatsRequest,
    SystemStatsResponse,
    InitializationRequest,
    InitializationResponse,
    StatusEnum
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Variable pour tracker le temps de démarrage
start_time = time.time()

@router.get("/health")
async def health_check():
    """
    Vérification de l'état de santé du système
    """
    try:
        health_info = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - start_time,
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "components": {
                "api": "operational",
                "rag_system": "operational",  # TODO: Vérifier le vrai statut
                "chat_handler": "operational",  # TODO: Vérifier le vrai statut
                "memory_system": "operational"  # TODO: Vérifier le vrai statut
            }
        }
        
        return health_info
        
    except Exception as e:
        logger.error(f"Erreur lors du health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.post("/stats", response_model=SystemStatsResponse)
async def get_system_stats(request: SystemStatsRequest):
    """
    Récupère les statistiques détaillées du système
    """
    try:
        # Statistiques système de base
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')
        
        uptime = time.time() - start_time
        
        stats = {
            "status": StatusEnum.SUCCESS,
            "uptime": uptime,
            "memory_usage": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free
            },
            "system_info": {
                "cpu_percent": cpu,
                "disk_total": disk.total,
                "disk_used": disk.used, 
                "disk_free": disk.free,
                "disk_percent": (disk.used / disk.total) * 100,
                "python_version": f"{psutil.version_info}",
                "platform": os.name
            },
            "rag_stats": {},
            "chat_stats": {}
        }
        
        # Statistiques RAG si demandées
        if request.include_detailed or request.component == "rag":
            # TODO: Implémenter avec le vrai système RAG
            stats["rag_stats"] = {
                "total_documents": 35,
                "total_chunks": 1250,
                "index_size_mb": 45.2,
                "last_indexing": "2024-01-01T10:00:00",
                "average_search_time": 0.15,
                "cache_hit_rate": 0.78
            }
        
        # Statistiques de chat si demandées  
        if request.include_detailed or request.component == "chat":
            # TODO: Implémenter avec le vrai système de chat
            stats["chat_stats"] = {
                "total_conversations": 245,
                "active_sessions": 12,
                "average_response_time": 2.3,
                "total_messages_processed": 1856,
                "error_rate": 0.02,
                "top_topics": ["orientation", "écoles", "carrières"]
            }
            
        return SystemStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )

@router.post("/initialize", response_model=InitializationResponse)
async def initialize_system(request: InitializationRequest):
    """
    Initialise ou réinitialise les composants du système
    """
    try:
        start_init = time.time()
        components_initialized = []
        warnings = []
        
        # Initialisation des composants selon la demande
        if not request.component or request.component == "all":
            # Initialiser tous les composants
            components_to_init = ["rag", "chat", "memory", "cache"]
        else:
            components_to_init = [request.component]
        
        for component in components_to_init:
            try:
                if component == "rag":
                    # TODO: Initialiser le système RAG
                    components_initialized.append("rag_system")
                    
                elif component == "chat":
                    # TODO: Initialiser les gestionnaires de chat
                    components_initialized.append("chat_handlers")
                    
                elif component == "memory":
                    # TODO: Initialiser le système de mémoire
                    components_initialized.append("memory_system")
                    
                elif component == "cache":
                    # TODO: Initialiser le cache
                    components_initialized.append("cache_system")
                    
            except Exception as comp_error:
                warning_msg = f"Avertissement lors de l'initialisation de {component}: {str(comp_error)}"
                warnings.append(warning_msg)
                logger.warning(warning_msg)
        
        initialization_time = time.time() - start_init
        
        response = InitializationResponse(
            status=StatusEnum.SUCCESS if components_initialized else StatusEnum.WARNING,
            components_initialized=components_initialized,
            initialization_time=initialization_time,
            warnings=warnings,
            details={
                "force_rebuild": request.force_rebuild,
                "config_overrides": request.config_override or {},
                "initialization_method": "manual_api_call"
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'initialisation: {str(e)}"
        )

@router.get("/config")
async def get_system_config():
    """
    Récupère la configuration actuelle du système
    """
    try:
        # TODO: Récupérer la vraie configuration
        config = {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "groq_model": os.getenv("GROQ_MODEL", "llama3-70b-8192"),
            "max_tokens": int(os.getenv("MAX_TOKENS", "4000")),
            "temperature_default": float(os.getenv("TEMPERATURE_DEFAULT", "0.7")),
            "rag_config": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "max_results": 5,
                "min_score": 0.7
            },
            "chat_config": {
                "max_history_length": 20,
                "stream_enabled": True,
                "context_window": 8000
            },
            "system_config": {
                "log_level": "INFO",
                "debug_mode": False,
                "cache_enabled": True,
                "async_processing": True
            }
        }
        
        return {
            "status": "success",
            "config": config,
            "config_sources": ["environment_variables", "default_values"],
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la configuration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de la configuration: {str(e)}"
        )

@router.post("/config")
async def update_system_config(config_updates: dict):
    """
    Met à jour la configuration système (runtime uniquement)
    """
    try:
        # TODO: Implémenter la mise à jour de configuration
        
        updated_keys = list(config_updates.keys())
        
        return {
            "status": "success",
            "message": "Configuration mise à jour (session en cours uniquement)",
            "updated_keys": updated_keys,
            "note": "Ces modifications sont temporaires et seront perdues au redémarrage",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la configuration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )

@router.get("/models")
async def get_available_models():
    """
    Retourne les modèles disponibles (compatibilité OpenAI API)
    """
    try:
        models = {
            "object": "list",
            "data": [
                {
                    "id": os.getenv("GROQ_MODEL", "llama3-70b-8192"),
                    "object": "model",
                    "created": 1687882411,
                    "owned_by": "groq",
                    "permission": [],
                    "root": os.getenv("GROQ_MODEL", "llama3-70b-8192"),
                    "parent": None
                }
            ]
        }
        return models
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des modèles: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des modèles: {str(e)}"
        )

@router.get("/logs")
async def get_system_logs(
    lines: int = 100,
    level: str = "INFO",
    component: str = None
):
    """
    Récupère les logs système récents
    """
    try:
        # TODO: Implémenter la lecture des logs réels
        
        mock_logs = [
            {
                "timestamp": "2024-01-01T10:00:00",
                "level": "INFO",
                "component": "api",
                "message": "API démarrée avec succès"
            },
            {
                "timestamp": "2024-01-01T10:01:00", 
                "level": "INFO",
                "component": "rag",
                "message": "Index vectoriel chargé"
            },
            {
                "timestamp": "2024-01-01T10:02:00",
                "level": "WARNING",
                "component": "chat",
                "message": "Température élevée détectée dans les paramètres"
            }
        ]
        
        # Filtrage par composant si spécifié
        if component:
            mock_logs = [log for log in mock_logs if log["component"] == component]
        
        # Filtrage par niveau
        mock_logs = [log for log in mock_logs if log["level"] == level or level == "ALL"]
        
        # Limitation du nombre de lignes
        mock_logs = mock_logs[-lines:]
        
        return {
            "logs": mock_logs,
            "total_entries": len(mock_logs),
            "filters_applied": {
                "lines": lines,
                "level": level,
                "component": component
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des logs: {str(e)}"
        )