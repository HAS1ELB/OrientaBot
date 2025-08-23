"""
Chat handler enrichi intégrant toutes les améliorations d'OrientaBot (Backend API)
- Prompts système enrichis avec personas
- Système de mémoire contextuelle 
- Recherche hybride avancée
- Détection d'intentions
- Templates de réponses
Adapté pour fonctionner sans Streamlit
"""

import json
import re
import logging
from groq import Groq
from typing import List, Dict, Optional, Any, Generator

# Import des modules de base
from core.config import GROQ_API_KEY, GROQ_MODEL, MAX_TOKENS
from core.contextual_memory import get_contextual_memory_system, get_user_context_for_prompt

# Import des modules d'amélioration
from chat.enhanced_prompts import get_enhanced_system_prompt, detect_user_profiles, classify_user_question
from rag.hybrid_search import create_hybrid_search_engine, SearchMode, HybridSearchEngine
from rag.semantic_processor import SemanticDocumentProcessor, convert_to_document_chunk

# Import RAG de base
try:
    from rag.manager import RAGManager
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

logger = logging.getLogger(__name__)

class EnhancedChatHandler:
    """Chat handler avec toutes les améliorations intégrées (Backend API)"""
    
    def __init__(self):
        """Initialise le chat handler enrichi"""
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY manquant. Configurez votre .env file avec votre clé API Groq.")
        
        self.client = Groq(api_key=GROQ_API_KEY)
        
        # Système de mémoire contextuelle
        self.memory_system = get_contextual_memory_system()
        
        # Processeur sémantique pour le chunking avancé
        self.semantic_processor = SemanticDocumentProcessor()
        
        # Système RAG et recherche hybride
        self.rag_manager = None
        self.hybrid_search_engine: Optional[HybridSearchEngine] = None
        self.rag_initialized = False
        
        # Cache pour les gestionnaires initialisés
        self._rag_cache = {}
        
        if RAG_AVAILABLE:
            self._initialize_enhanced_rag()
        
        # Statistiques et métriques
        self.response_stats = {
            'total_responses': 0,
            'enhanced_prompts_used': 0,
            'rag_responses': 0,
            'hybrid_search_used': 0,
            'memory_context_used': 0
        }
        
        logger.info("EnhancedChatHandler initialisé avec toutes les améliorations")
    
    def _initialize_enhanced_rag(self):
        """Initialise le système RAG amélioré avec recherche hybride"""
        try:
            logger.info("🚀 Initialisation du système RAG avancé...")
            self.rag_manager = RAGManager()
            
            # Initialiser la base de connaissances avec chunking sémantique
            success = self.rag_manager.initialize_knowledge_base()
            
            if success:
                # Créer le moteur de recherche hybride
                self.hybrid_search_engine = create_hybrid_search_engine(self.rag_manager.vector_store)
                
                self.rag_initialized = True
                
                # Logger les statistiques
                stats = self.rag_manager.get_stats()
                search_stats = self.hybrid_search_engine.get_search_stats()
                
                logger.info(f"""✅ Système RAG Avancé Activé:
                - Base vectorielle: {stats['vector_store_stats']['total_chunks']} chunks sémantiques
                - Sources: {stats['pdf_files_count']} documents analysés  
                - Index mots-clés: {search_stats['keyword_index_terms']} termes indexés
                - Recherche hybride: Vectorielle + Mots-clés + Boost contextuel
                """)
            else:
                logger.warning("⚠️ Échec de l'initialisation RAG - Mode connaissances générales")
                self.rag_manager = None
                self.rag_initialized = False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation RAG avancé: {e}")
            self.rag_manager = None
            self.hybrid_search_engine = None
            self.rag_initialized = False
    
    def process_chat_input(self, 
                          prompt: str, 
                          base_system_prompt: str, 
                          temperature: float,
                          conversation_history: List[Dict[str, str]] = None,
                          session_id: Optional[str] = None,
                          stream: bool = False) -> Dict[str, Any]:
        """
        Traite l'input utilisateur avec toutes les améliorations
        
        Args:
            prompt: Message de l'utilisateur
            base_system_prompt: Prompt système de base (sera enrichi)
            temperature: Température pour la génération
            conversation_history: Historique de conversation
            session_id: ID de session
            stream: Retourner un générateur pour streaming
            
        Returns:
            Dictionnaire avec la réponse et les métadonnées
        """
        if conversation_history is None:
            conversation_history = []
        
        try:
            # Incrémenter les statistiques
            self.response_stats['total_responses'] += 1
            
            # Charger le profil utilisateur
            user_profile = self.memory_system.load_user_profile(session_id=session_id)
            
            # Démarrer ou continuer la session de conversation
            if self.memory_system.current_session is None:
                topic = classify_user_question(prompt)
                self.memory_system.start_conversation_session(topic, session_id=session_id)
            
            # Détecter les profils utilisateur depuis le prompt
            detected_profiles = detect_user_profiles(prompt, conversation_history)
            logger.info(f"Profils détectés: {detected_profiles}")
            
            # Générer le prompt système enrichi
            enhanced_system_prompt = get_enhanced_system_prompt(
                prompt, 
                conversation_history, 
                base_system_prompt
            )
            self.response_stats['enhanced_prompts_used'] += 1
            
            # Ajouter le contexte de mémoire utilisateur
            memory_context = get_user_context_for_prompt(session_id)
            if memory_context:
                enhanced_system_prompt += memory_context
                self.response_stats['memory_context_used'] += 1
            
            # Augmenter le prompt avec RAG avancé si disponible
            search_info = {}
            if self.rag_initialized and self.hybrid_search_engine:
                enhanced_system_prompt, search_info = self._augment_with_hybrid_search(
                    prompt, enhanced_system_prompt
                )
                self.response_stats['hybrid_search_used'] += 1
            
            # Préparer les messages
            messages = [{"role": "system", "content": enhanced_system_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": prompt})
            
            # Générer la réponse
            if stream:
                response_generator = self._stream_response(messages, temperature)
                
                return {
                    "type": "stream",
                    "generator": response_generator,
                    "detected_profiles": detected_profiles,
                    "search_info": search_info,
                    "rag_available": self.rag_initialized,
                    "stats": self._get_current_stats()
                }
            else:
                response = self._generate_enhanced_response(messages, temperature)
                
                # Ajouter le turn à la mémoire contextuelle
                self.memory_system.add_conversation_turn(
                    user_message=prompt,
                    assistant_response=response,
                    detected_intent=classify_user_question(prompt),
                    session_id=session_id
                )
                
                # Extraire les recommandations structurées
                recommendations = self._extract_json_recommendations(response)
                
                return {
                    "type": "complete",
                    "response": response,
                    "recommendations": recommendations,
                    "detected_profiles": detected_profiles,
                    "search_info": search_info,
                    "rag_available": self.rag_initialized,
                    "stats": self._get_current_stats(),
                    "message_count": len(messages)
                }
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement enrichi: {e}")
            return {
                "type": "error",
                "error": str(e),
                "rag_available": self.rag_initialized,
                "stats": self._get_current_stats()
            }
    
    def _augment_with_hybrid_search(self, user_query: str, base_prompt: str) -> tuple[str, Dict[str, Any]]:
        """Augmente le prompt avec la recherche hybride avancée"""
        search_info = {
            "search_performed": False,
            "results_found": 0,
            "search_mode": None,
            "query_type": None,
            "results": []
        }
        
        try:
            # Effectuer la recherche hybride
            search_results = self.hybrid_search_engine.search(
                user_query, 
                top_k=5, 
                mode=SearchMode.AUTO
            )
            
            # Informations sur le type de recherche
            query_type = self.hybrid_search_engine.detect_query_type(user_query)
            search_mode = self.hybrid_search_engine.select_search_mode(user_query, query_type)
            
            search_info.update({
                "search_performed": True,
                "query_type": query_type.value,
                "search_mode": search_mode.value
            })
            
            if not search_results:
                logger.info("Aucun résultat de recherche hybride")
                return self._add_no_context_notice(base_prompt), search_info
            
            search_info["results_found"] = len(search_results)
            
            # Construire le contexte enrichi
            context_parts = []
            total_length = 0
            max_context_size = 3000
            
            for result in search_results:
                chunk = result.chunk
                
                # Informations sur la source et le score
                source_info = f"**[{chunk.source} - Page {chunk.page_number}]**"
                
                # Informations sur le scoring hybride
                score_info = f"*Score: V:{result.vector_score:.2f} + K:{result.keyword_score:.2f} = H:{result.hybrid_score:.2f}*"
                
                # Mots-clés matchés
                keywords_info = ""
                if result.matched_keywords:
                    keywords_info = f" | Mots-clés: {', '.join(result.matched_keywords[:3])}"
                
                # Type de contenu si disponible
                content_info = ""
                if hasattr(chunk, 'metadata') and chunk.metadata.get('content_type'):
                    content_info = f" | Type: {chunk.metadata['content_type']}"
                
                chunk_text = f"""
{source_info}
{score_info}{keywords_info}{content_info}

{chunk.content}
"""
                
                if total_length + len(chunk_text) > max_context_size:
                    break
                
                context_parts.append(chunk_text)
                total_length += len(chunk_text)
                
                # Ajouter aux résultats pour l'info
                search_info["results"].append({
                    "source": chunk.source,
                    "page": chunk.page_number,
                    "vector_score": float(result.vector_score),
                    "keyword_score": float(result.keyword_score),
                    "hybrid_score": float(result.hybrid_score),
                    "matched_keywords": result.matched_keywords,
                    "content_preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    "relevance_factors": result.relevance_factors
                })
            
            if not context_parts:
                return self._add_no_context_notice(base_prompt), search_info
            
            # Construire le prompt augmenté
            enhanced_context = "## CONTEXTE SPÉCIALISÉ - SYSTÈME RAG AVANCÉ AVEC RECHERCHE HYBRIDE\n"
            enhanced_context += f"*Recherche vectorielle + mots-clés + boost contextuel*\n\n"
            
            for part in context_parts:
                enhanced_context += part
            
            augmented_prompt = f"""{base_prompt}

# MODE RAG AVANCÉ ACTIVÉ - RECHERCHE HYBRIDE

{enhanced_context}

## INSTRUCTIONS SPÉCIALISÉES:
- Tu as accès à des informations OFFICIELLES via un système RAG avancé avec recherche hybride
- Les scores indiquent la pertinence: Vectorielle (sémantique) + Mots-clés (factuelle) + Hybride (combiné)
- Les mots-clés matchés montrent les termes exacts trouvés dans les documents
- PRIORITÉ: Utilise ces informations spécialisées avant tes connaissances générales
- Cite toujours les sources en mentionnant le score de pertinence
- Si les informations hybrides ne couvrent pas la question, complète avec tes connaissances générales
- Mentionne le type de recherche utilisé (vectorielle/mots-clés/hybride) dans ta réponse

## SCORING HYBRIDE:
- **Score Vectoriel**: Similarité sémantique (0-1)
- **Score Mots-clés**: Correspondance factuelle TF-IDF (0-1)  
- **Score Hybride**: Combinaison pondérée avec boost contextuel

"""
            
            logger.info(f"✅ Prompt augmenté avec recherche hybride: {len(context_parts)} résultats")
            self.response_stats['rag_responses'] += 1
            
            return augmented_prompt, search_info
            
        except Exception as e:
            logger.error(f"Erreur lors de l'augmentation hybride: {e}")
            search_info["error"] = str(e)
            return self._add_no_context_notice(base_prompt), search_info
    
    def _add_no_context_notice(self, base_prompt: str) -> str:
        """Ajoute une notice quand aucun contexte spécialisé n'est disponible"""
        return f"""{base_prompt}

# MODE CONNAISSANCES GÉNÉRALES
*Aucune information spécialisée trouvée dans la base de données pour cette requête*

Tu réponds avec tes connaissances générales du système éducatif marocain en précisant que:
- Ces informations sont basées sur tes connaissances générales
- Il est recommandé de vérifier sur les sites officiels des établissements
- Pour des conseils plus précis, l'utilisateur peut fournir des documents spécifiques

"""
    
    def _generate_enhanced_response(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Génère une réponse complète avec gestion d'erreurs avancée"""
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
            error_msg = f"Erreur lors de la génération: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _stream_response(self, messages: List[Dict[str, str]], temperature: float) -> Generator[str, None, None]:
        """Stream la réponse depuis l'API Groq"""
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
            yield f"Erreur API: {str(e)}"
    
    def _extract_json_recommendations(self, text: str) -> Optional[Dict]:
        """Extrait les recommandations JSON si présentes"""
        pattern = r"```json\s*(\{.*?\})\s*```"
        match = re.search(pattern, text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return None
    
    def get_enhanced_search_info(self, user_query: str) -> Dict[str, Any]:
        """Obtient les informations détaillées sur la recherche hybride"""
        if not self.hybrid_search_engine:
            return {"available": False}
            
        try:
            # Obtenir les résultats de recherche pour analyse
            search_results = self.hybrid_search_engine.search(user_query, top_k=3)
            
            # Type de recherche utilisé
            query_type = self.hybrid_search_engine.detect_query_type(user_query)
            search_mode = self.hybrid_search_engine.select_search_mode(user_query, query_type)
            
            return {
                "available": True,
                "query_type": query_type.value,
                "search_mode": search_mode.value,
                "results_count": len(search_results),
                "results": [
                    {
                        "source": result.chunk.source,
                        "page": result.chunk.page_number,
                        "vector_score": float(result.vector_score),
                        "keyword_score": float(result.keyword_score),
                        "hybrid_score": float(result.hybrid_score),
                        "matched_keywords": result.matched_keywords,
                        "content_preview": result.chunk.content[:200] + "..." if len(result.chunk.content) > 200 else result.chunk.content,
                        "relevance_factors": result.relevance_factors
                    }
                    for result in search_results
                ]
            }
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'obtention des informations de recherche: {e}")
            return {"available": False, "error": str(e)}
    
    def _get_current_stats(self) -> Dict[str, Any]:
        """Obtient les statistiques actuelles"""
        return {
            'response_stats': self.response_stats,
            'rag_initialized': self.rag_initialized,
            'memory_available': self.memory_system is not None
        }
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques complètes du système enrichi"""
        base_stats = {
            'handler_type': 'Enhanced',
            'response_stats': self.response_stats,
        }
        
        # Stats de mémoire contextuelle
        if self.memory_system:
            base_stats['memory_stats'] = self.memory_system.get_memory_stats()
        
        # Stats de recherche hybride
        if self.hybrid_search_engine:
            base_stats['search_stats'] = self.hybrid_search_engine.get_search_stats()
        
        # Stats RAG
        if self.rag_manager:
            base_stats['rag_stats'] = self.rag_manager.get_stats()
        
        return base_stats
    
    def export_conversation_data(self) -> Dict[str, Any]:
        """Exporte les données de conversation pour analyse"""
        if not self.memory_system.current_session:
            return {}
        
        return {
            'session_id': self.memory_system.current_session.session_id,
            'start_time': self.memory_system.current_session.start_time,
            'total_turns': len(self.memory_system.current_session.turns),
            'user_profile': self.memory_system.current_profile.__dict__ if self.memory_system.current_profile else None,
            'stats': self.get_enhanced_stats()
        }
    
    def search_knowledge(self, query: str, top_k: int = 5, mode: str = "auto") -> List[Dict[str, Any]]:
        """
        Effectue une recherche directe dans la base de connaissances
        
        Args:
            query: Requête de recherche
            top_k: Nombre de résultats
            mode: Mode de recherche
            
        Returns:
            Liste des résultats avec métadonnées complètes
        """
        if not self.hybrid_search_engine:
            return []
        
        try:
            search_mode = SearchMode.AUTO
            if mode.lower() == "semantic":
                search_mode = SearchMode.SEMANTIC_ONLY
            elif mode.lower() == "keyword":
                search_mode = SearchMode.KEYWORD_ONLY
            elif mode.lower() == "hybrid":
                search_mode = SearchMode.HYBRID
            
            search_results = self.hybrid_search_engine.search(query, top_k=top_k, mode=search_mode)
            
            return [
                {
                    "content": result.chunk.content,
                    "source": result.chunk.source,
                    "page_number": result.chunk.page_number,
                    "vector_score": float(result.vector_score),
                    "keyword_score": float(result.keyword_score),
                    "hybrid_score": float(result.hybrid_score),
                    "matched_keywords": result.matched_keywords,
                    "relevance_factors": result.relevance_factors,
                    "metadata": {
                        "chunk_id": getattr(result.chunk, 'chunk_id', None),
                        "confidence": "Haute" if result.hybrid_score > 0.8 else "Moyenne" if result.hybrid_score > 0.6 else "Faible"
                    }
                }
                for result in search_results
            ]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {e}")
            return []
    
    def is_rag_available(self) -> bool:
        """Vérifie si le système RAG est disponible"""
        return self.rag_initialized and self.hybrid_search_engine is not None
    
    def reinitialize_rag(self) -> bool:
        """Réinitialise le système RAG"""
        try:
            if RAG_AVAILABLE:
                self._initialize_enhanced_rag()
                return self.rag_initialized
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation RAG: {e}")
            return False