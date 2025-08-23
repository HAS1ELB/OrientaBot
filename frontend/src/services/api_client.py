"""
Client API pour communiquer avec le backend OrientaBot
"""
import os
import requests
import json
import logging
from typing import Dict, List, Any, Optional, Generator
from dataclasses import dataclass
import streamlit as st

logger = logging.getLogger(__name__)

@dataclass
class ChatResponse:
    """Réponse de l'API de chat"""
    response: str
    recommendations: Optional[Dict[str, Any]] = None
    context_info: Optional[Dict[str, Any]] = None
    rag_available: bool = False
    stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class OrientaBotAPIClient:
    """Client pour l'API OrientaBot"""
    
    def __init__(self, base_url: str = None, timeout: int = 30):
        """
        Initialise le client API
        
        Args:
            base_url: URL de base de l'API
            timeout: Timeout des requêtes en secondes
        """
        self.base_url = base_url or os.getenv("BACKEND_API_URL", "http://localhost:8000")
        self.timeout = timeout
        self.session = requests.Session()
        
        # Configuration des headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        logger.info(f"Client API initialisé: {self.base_url}")
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Traite la réponse de l'API"""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erreur HTTP {response.status_code}: {e}")
            return {
                "error": f"Erreur HTTP {response.status_code}",
                "details": response.text
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de requête: {e}")
            return {
                "error": "Erreur de connexion à l'API",
                "details": str(e)
            }
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de décodage JSON: {e}")
            return {
                "error": "Réponse invalide de l'API",
                "details": response.text
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Vérifie l'état de l'API"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Erreur lors du health check: {e}")
            return {"error": "API non disponible", "details": str(e)}
    
    def send_message(self, 
                    message: str, 
                    session_id: Optional[str] = None,
                    user_profile: Optional[Dict[str, Any]] = None,
                    temperature: float = 0.7,
                    conversation_history: Optional[List[Dict[str, str]]] = None) -> ChatResponse:
        """
        Envoie un message au chatbot
        
        Args:
            message: Message de l'utilisateur
            session_id: ID de session
            user_profile: Profil utilisateur
            temperature: Température du modèle
            conversation_history: Historique de conversation
            
        Returns:
            Réponse du chatbot
        """
        try:
            payload = {
                "message": message,
                "session_id": session_id,
                "user_profile": user_profile,
                "temperature": temperature,
                "conversation_history": conversation_history or []
            }
            
            response = self.session.post(
                f"{self.base_url}/api/chat/message",
                json=payload,
                timeout=self.timeout
            )
            
            result = self._handle_response(response)
            
            if "error" in result:
                return ChatResponse(
                    response="Désolé, une erreur s'est produite lors du traitement de votre message.",
                    error=result["error"]
                )
            
            return ChatResponse(
                response=result.get("response", ""),
                recommendations=result.get("recommendations"),
                context_info=result.get("context_info"),
                rag_available=result.get("rag_available", False),
                stats=result.get("stats")
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message: {e}")
            return ChatResponse(
                response="Désolé, impossible de communiquer avec le serveur.",
                error=str(e)
            )
    
    def stream_message(self, 
                      message: str,
                      session_id: Optional[str] = None,
                      user_profile: Optional[Dict[str, Any]] = None,
                      temperature: float = 0.7,
                      conversation_history: Optional[List[Dict[str, str]]] = None) -> Generator[str, None, None]:
        """
        Stream la réponse du chatbot
        
        Args:
            message: Message de l'utilisateur
            session_id: ID de session
            user_profile: Profil utilisateur  
            temperature: Température du modèle
            conversation_history: Historique de conversation
            
        Yields:
            Chunks de la réponse
        """
        try:
            payload = {
                "message": message,
                "session_id": session_id,
                "user_profile": user_profile,
                "temperature": temperature,
                "conversation_history": conversation_history or []
            }
            
            with self.session.post(
                f"{self.base_url}/api/chat/stream",
                json=payload,
                timeout=self.timeout,
                stream=True
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        line_text = line.decode('utf-8')
                        if line_text.startswith('data: '):
                            try:
                                data = json.loads(line_text[6:])  # Enlever 'data: '
                                if 'content' in data:
                                    yield data['content']
                                elif 'done' in data:
                                    break
                                elif 'error' in data:
                                    yield f"Erreur: {data['error']}"
                                    break
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            logger.error(f"Erreur lors du streaming: {e}")
            yield f"Erreur de connexion: {str(e)}"
    
    def get_chat_history(self, session_id: str) -> Dict[str, Any]:
        """Récupère l'historique de chat"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/chat/history/{session_id}",
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique: {e}")
            return {"error": str(e)}
    
    def clear_chat_history(self, session_id: str) -> Dict[str, Any]:
        """Efface l'historique de chat"""
        try:
            response = self.session.delete(
                f"{self.base_url}/api/chat/history/{session_id}",
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Erreur lors de l'effacement de l'historique: {e}")
            return {"error": str(e)}
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Récupère le profil utilisateur"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/profile/{user_id}",
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du profil: {e}")
            return {"error": str(e)}
    
    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour le profil utilisateur"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/profile/{user_id}",
                json=profile_data,
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du profil: {e}")
            return {"error": str(e)}
    
    def search_documents(self, 
                        query: str,
                        mode: str = "hybrid",
                        max_results: int = 5,
                        min_score: float = 0.0) -> Dict[str, Any]:
        """Recherche dans la base de connaissances"""
        try:
            payload = {
                "query": query,
                "mode": mode,
                "max_results": max_results,
                "min_score": min_score
            }
            
            response = self.session.post(
                f"{self.base_url}/api/search/",
                json=payload,
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {e}")
            return {"error": str(e)}
    
    def get_system_stats(self, include_detailed: bool = False) -> Dict[str, Any]:
        """Récupère les statistiques système"""
        try:
            payload = {
                "include_detailed": include_detailed
            }
            
            response = self.session.post(
                f"{self.base_url}/api/system/stats",
                json=payload,
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {e}")
            return {"error": str(e)}

# Instance globale pour Streamlit
@st.cache_resource
def get_api_client() -> OrientaBotAPIClient:
    """Retourne l'instance du client API (mise en cache)"""
    return OrientaBotAPIClient()

def test_api_connection() -> bool:
    """Teste la connexion à l'API"""
    try:
        client = get_api_client()
        result = client.health_check()
        return "error" not in result
    except Exception as e:
        logger.error(f"Test de connexion échoué: {e}")
        return False