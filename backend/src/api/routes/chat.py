"""
Routes API pour la gestion des conversations de chat
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import asyncio
import json
import time
import logging
from typing import Dict, Any, AsyncGenerator

from api.models import (
    ChatRequest, 
    ChatResponse, 
    StatusEnum,
    ErrorResponse
)

# Importation du module backend simplifié
from api.simple_chat_handler import SimpleChatHandler

router = APIRouter()
logger = logging.getLogger(__name__)

# Instance globale du gestionnaire
chat_handler = None

def get_or_create_chat_handler():
    """Récupère ou crée l'instance du chat handler"""
    global chat_handler
    if chat_handler is None:
        try:
            chat_handler = SimpleChatHandler()
            logger.info("✅ Simple chat handler initialisé")
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation du chat handler: {e}")
            raise
    return chat_handler

@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Envoie un message au chatbot et récupère la réponse
    """
    try:
        start_time = time.time()
        
        # Validation de la requête
        if not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Le message ne peut pas être vide"
            )
        
        # Utiliser le chat handler simple
        session_id = request.session_id or f"session_{int(time.time())}"
        
        # Récupérer le chat handler
        handler = get_or_create_chat_handler()
        
        # Traiter le message
        result = handler.process_message(
            message=request.message,
            conversation_history=request.conversation_history or [],
            temperature=request.temperature,
            session_id=session_id
        )
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"Erreur du chat handler: {result.get('error', 'Erreur inconnue')}"
            )
        
        # Préparer la réponse API
        api_response = {
            "status": StatusEnum.SUCCESS,
            "response": result["response"],
            "session_id": session_id,
            "recommendations": result.get("recommendations"),
            "context_used": [],  # Simple handler doesn't use RAG yet
            "processing_time": time.time() - start_time
        }
        
        return ChatResponse(**api_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du traitement du message: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne: {str(e)}"
        )

@router.post("/stream")
async def stream_message(request: ChatRequest):
    """
    Envoie un message et stream la réponse en temps réel
    """
    async def generate_response() -> AsyncGenerator[str, None]:
        try:
            session_id = request.session_id or f"session_{int(time.time())}"
            
            # Récupérer le chat handler
            handler = get_or_create_chat_handler()
            
            # Streamer la réponse
            for chunk in handler.stream_message(
                message=request.message,
                conversation_history=request.conversation_history or [],
                temperature=request.temperature,
                session_id=session_id
            ):
                yield f"data: {json.dumps({'content': chunk, 'session_id': session_id})}\n\n"
                
            yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"
            
        except Exception as e:
            logger.error(f"Erreur lors du streaming: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Récupère l'historique de conversation pour une session
    """
    try:
        # TODO: Implémenter avec le vrai système de mémoire
        mock_history = {
            "session_id": session_id,
            "messages": [
                {
                    "role": "user",
                    "content": "Bonjour, je cherche une orientation",
                    "timestamp": "2024-01-01T10:00:00"
                },
                {
                    "role": "assistant", 
                    "content": "Bonjour ! Je suis ravi de vous aider...",
                    "timestamp": "2024-01-01T10:00:05"
                }
            ],
            "created_at": "2024-01-01T10:00:00",
            "last_activity": "2024-01-01T10:00:05"
        }
        
        return mock_history
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de l'historique: {str(e)}"
        )

@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """
    Efface l'historique de conversation pour une session
    """
    try:
        # TODO: Implémenter avec le vrai système de mémoire
        return {
            "status": "success",
            "message": f"Historique de la session {session_id} effacé"
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'effacement de l'historique: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'effacement de l'historique: {str(e)}"
        )

@router.post("/context/analyze")
async def analyze_user_context(request: ChatRequest):
    """
    Analyse le contexte utilisateur d'un message pour adapter la réponse
    """
    try:
        # TODO: Implémenter l'analyse contextuelle réelle
        
        # Simulation de détection de contexte
        message_lower = request.message.lower()
        
        context = "general"
        if any(word in message_lower for word in ["stress", "anxieux", "peur"]):
            context = "anxious_student"
        elif any(word in message_lower for word in ["parents", "famille"]):
            context = "parent_pressure"
        elif any(word in message_lower for word in ["excellent", "18", "19", "20"]):
            context = "high_achiever"
        elif any(word in message_lower for word in ["ne sais pas", "hésit", "confus"]):
            context = "uncertain"
            
        return {
            "context_detected": context,
            "confidence": 0.85,
            "suggested_approach": f"Approche adaptée pour {context}",
            "keywords_found": ["exemple", "mots-clés"]
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse contextuelle: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse: {str(e)}"
        )

# Fonction d'initialisation pour les gestionnaires de chat
async def initialize_chat_handlers():
    """
    Initialize les gestionnaires de chat
    """
    global chat_handler
    
    try:
        chat_handler = get_or_create_chat_handler()
        logger.info("✅ Gestionnaires de chat initialisés avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation des gestionnaires: {e}")
        raise