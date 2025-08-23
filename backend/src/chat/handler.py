"""
Chat handling and API interaction module with RAG support (Backend API)
Adapté pour fonctionner sans Streamlit
"""
import json
import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Generator
from groq import Groq
from ..core.config import GROQ_API_KEY, GROQ_MODEL, MAX_TOKENS

# Import RAG components
try:
    from ..rag.manager import RAGManager
    RAG_AVAILABLE = True
    logger = logging.getLogger(__name__)
except ImportError as e:
    RAG_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"RAG components not available: {e}")

class ChatHandler:
    def __init__(self):
        """Initialize the chat handler with Groq client and RAG manager"""
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY manquant. Configurez votre .env file avec votre clé API Groq.")
        
        self.client = Groq(api_key=GROQ_API_KEY)
        
        # Initialize RAG manager if available
        self.rag_manager = None
        self.rag_initialized = False
        
        if RAG_AVAILABLE:
            self._initialize_rag()
    
    def stream_response(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> Generator[str, None, None]:
        """Stream chat response from Groq"""
        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=MAX_TOKENS,
                stream=True,
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Erreur lors du streaming: {e}")
            yield f"Erreur: {str(e)}"
    
    def get_response(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """Get complete response without streaming"""
        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=MAX_TOKENS,
                stream=False,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération: {e}")
            return f"Erreur: {str(e)}"
    
    def extract_json_recommendations(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON recommendations if present"""
        pattern = r"```json\s*(\{.*?\})\s*```"
        match = re.search(pattern, text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception as e:
                logger.warning(f"Erreur lors du parsing JSON: {e}")
        return None
    
    def process_chat_input(self, 
                          prompt: str, 
                          system_prompt: str, 
                          temperature: float = 0.7,
                          conversation_history: List[Dict[str, str]] = None,
                          stream: bool = False) -> Dict[str, Any]:
        """
        Process user input and generate response with RAG support
        
        Args:
            prompt: User input message
            system_prompt: System prompt to use
            temperature: Model temperature
            conversation_history: Previous conversation messages
            stream: Whether to return a generator for streaming
            
        Returns:
            Dictionary containing response and metadata
        """
        if conversation_history is None:
            conversation_history = []
        
        try:
            # Augment the system prompt with RAG if available
            augmented_prompt = self._get_augmented_prompt(prompt, system_prompt)
            
            # Prepare messages for API
            messages = [{"role": "system", "content": augmented_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": prompt})
            
            # Get context info if RAG is available
            context_info = self._get_context_info(prompt)
            
            if stream:
                # Return generator for streaming
                response_generator = self.stream_response(messages, temperature)
                return {
                    "type": "stream",
                    "generator": response_generator,
                    "context_info": context_info,
                    "rag_available": self.rag_initialized
                }
            else:
                # Get complete response
                full_response = self.get_response(messages, temperature)
                
                # Extract recommendations
                recommendations = self.extract_json_recommendations(full_response)
                
                return {
                    "type": "complete",
                    "response": full_response,
                    "recommendations": recommendations,
                    "context_info": context_info,
                    "rag_available": self.rag_initialized,
                    "message_count": len(messages)
                }
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du chat: {e}")
            return {
                "type": "error",
                "error": str(e),
                "rag_available": self.rag_initialized
            }
    
    def _initialize_rag(self):
        """Initialize the RAG manager"""
        try:
            logger.info("🚀 Initialisation du système RAG...")
            self.rag_manager = RAGManager()
            
            # Initialize knowledge base
            success = self.rag_manager.initialize_knowledge_base()
            
            if success:
                self.rag_initialized = True
                logger.info("✅ Système RAG initialisé avec succès")
                
                # Log stats
                stats = self.rag_manager.get_stats()
                logger.info(f"🧪 Base de connaissances chargée: {stats['vector_store_stats']['total_chunks']} chunks depuis {stats['pdf_files_count']} PDF(s)")
            else:
                logger.warning("⚠️ Échec de l'initialisation RAG - Mode connaissances générales activé")
                self.rag_manager = None
                self.rag_initialized = False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation RAG: {e}")
            self.rag_manager = None
            self.rag_initialized = False
    
    def _get_augmented_prompt(self, user_query: str, base_prompt: str) -> str:
        """Get augmented prompt with RAG context or fallback to base prompt"""
        if self.rag_manager and self.rag_initialized:
            try:
                return self.rag_manager.augment_prompt(user_query, base_prompt)
            except Exception as e:
                logger.error(f"Erreur lors de l'augmentation du prompt: {e}")
                # Fallback to base prompt
                return self._add_fallback_notice(base_prompt)
        else:
            # No RAG available - use base prompt with notice
            return self._add_fallback_notice(base_prompt)
    
    def _add_fallback_notice(self, base_prompt: str) -> str:
        """Add fallback notice to base prompt"""
        return f"""{base_prompt}

# MODE CONNAISSANCES GÉNÉRALES ACTIVÉ
*Système RAG non disponible - utilisation des connaissances générales du modèle*

Tu réponds avec tes connaissances générales du système éducatif marocain en précisant que:
- Ces informations sont basées sur tes connaissances générales
- Il est fortement recommandé de vérifier sur les sites officiels des établissements
- Les étudiants peuvent fournir des documents spécifiques pour des conseils plus précis
"""
    
    def _get_context_info(self, user_query: str) -> Dict[str, Any]:
        """Get context information including RAG search results"""
        context_info = {
            "rag_available": self.rag_initialized,
            "sources_used": [],
            "search_performed": False
        }
        
        if self.rag_manager and self.rag_initialized:
            try:
                search_results = self.rag_manager.search_knowledge(user_query, top_k=3)
                
                if search_results:
                    context_info["search_performed"] = True
                    context_info["sources_used"] = [
                        {
                            "source": chunk.source,
                            "page_number": chunk.page_number,
                            "confidence": "Haute" if score > 0.8 else "Moyenne" if score > 0.6 else "Faible",
                            "score": float(score),
                            "excerpt": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
                        }
                        for chunk, score in search_results
                    ]
                else:
                    context_info["search_performed"] = True
                    context_info["sources_used"] = []
                    
            except Exception as e:
                logger.error(f"Erreur lors de la recherche de contexte: {e}")
                context_info["error"] = str(e)
        
        return context_info
    
    def get_rag_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        if self.rag_manager and self.rag_initialized:
            return self.rag_manager.get_stats()
        return {'status': 'non_disponible', 'rag_initialized': self.rag_initialized}
    
    def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the knowledge base directly
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of search results with metadata
        """
        if not self.rag_manager or not self.rag_initialized:
            return []
        
        try:
            search_results = self.rag_manager.search_knowledge(query, top_k=top_k)
            
            return [
                {
                    "content": chunk.content,
                    "source": chunk.source,
                    "page_number": chunk.page_number,
                    "score": float(score),
                    "metadata": {
                        "chunk_id": getattr(chunk, 'chunk_id', None),
                        "confidence": "Haute" if score > 0.8 else "Moyenne" if score > 0.6 else "Faible"
                    }
                }
                for chunk, score in search_results
            ]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {e}")
            return []
    
    def is_rag_available(self) -> bool:
        """Check if RAG system is available and initialized"""
        return self.rag_initialized and self.rag_manager is not None
    
    def reinitialize_rag(self) -> bool:
        """Reinitialize the RAG system"""
        try:
            if RAG_AVAILABLE:
                self._initialize_rag()
                return self.rag_initialized
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation RAG: {e}")
            return False