"""
Chat handler enrichi intégrant toutes les améliorations d'OrientaBot
- Prompts système enrichis avec personas
- Système de mémoire contextuelle 
- Recherche hybride avancée
- Détection d'intentions
- Templates de réponses
"""

import json
import re
import streamlit as st
import logging
from groq import Groq
from typing import List, Dict, Optional, Any

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
    """Chat handler avec toutes les améliorations intégrées"""
    
    def __init__(self):
        """Initialise le chat handler enrichi"""
        if not GROQ_API_KEY:
            st.error("⌚ GROQ_API_KEY manquant. Configurez votre .env file avec votre clé API Groq.")
            st.stop()
        
        self.client = Groq(api_key=GROQ_API_KEY)
        
        # Système de mémoire contextuelle
        self.memory_system = get_contextual_memory_system()
        
        # Processeur sémantique pour le chunking avancé
        self.semantic_processor = SemanticDocumentProcessor()
        
        # Système RAG et recherche hybride
        self.rag_manager = None
        self.hybrid_search_engine: Optional[HybridSearchEngine] = None
        self.rag_initialized = False
        
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
            if 'enhanced_rag_manager' not in st.session_state:
                with st.spinner("🚀 Initialisation du système RAG avancé..."):
                    self.rag_manager = RAGManager()
                    
                    # Initialiser la base de connaissances avec chunking sémantique
                    success = self.rag_manager.initialize_knowledge_base()
                    
                    if success:
                        st.session_state.enhanced_rag_manager = self.rag_manager
                        
                        # Créer le moteur de recherche hybride
                        self.hybrid_search_engine = create_hybrid_search_engine(self.rag_manager.vector_store)
                        st.session_state.hybrid_search_engine = self.hybrid_search_engine
                        
                        self.rag_initialized = True
                        
                        # Afficher les statistiques
                        stats = self.rag_manager.get_stats()
                        search_stats = self.hybrid_search_engine.get_search_stats()
                        
                        st.success(f"""
                        🧪 **Système RAG Avancé Activé**
                        - **Base vectorielle:** {stats['vector_store_stats']['total_chunks']} chunks sémantiques
                        - **Sources:** {stats['pdf_files_count']} documents analysés  
                        - **Index mots-clés:** {search_stats['keyword_index_terms']} termes indexés
                        - **Recherche hybride:** Vectorielle + Mots-clés + Boost contextuel
                        """)
                        
                        logger.info("✅ Système RAG avancé initialisé avec recherche hybride")
                    else:
                        logger.warning("⚠️ Échec de l'initialisation RAG - Mode connaissances générales")
                        st.warning("📁 Mode connaissances générales activé. Ajoutez des PDFs pour activer le RAG avancé.")
            else:
                self.rag_manager = st.session_state.enhanced_rag_manager
                self.hybrid_search_engine = st.session_state.get('hybrid_search_engine')
                self.rag_initialized = True
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation RAG avancé: {e}")
            st.error(f"🚫 Erreur système RAG: {e}")
            self.rag_manager = None
            self.hybrid_search_engine = None
            self.rag_initialized = False
    
    def process_chat_input(self, prompt: str, base_system_prompt: str, temperature: float):
        """
        Traite l'input utilisateur avec toutes les améliorations
        
        Args:
            prompt: Message de l'utilisateur
            base_system_prompt: Prompt système de base (sera enrichi)
            temperature: Température pour la génération
        """
        # Incrémenter les statistiques
        self.response_stats['total_responses'] += 1
        
        # Charger le profil utilisateur
        user_profile = self.memory_system.load_user_profile()
        
        # Démarrer ou continuer la session de conversation
        if self.memory_system.current_session is None:
            topic = classify_user_question(prompt)
            self.memory_system.start_conversation_session(topic)
        
        # Détecter les profils utilisateur depuis le prompt
        detected_profiles = detect_user_profiles(prompt, st.session_state.messages)
        logger.info(f"Profils détectés: {detected_profiles}")
        
        # Générer le prompt système enrichi
        enhanced_system_prompt = get_enhanced_system_prompt(
            prompt, 
            st.session_state.messages, 
            base_system_prompt
        )
        self.response_stats['enhanced_prompts_used'] += 1
        
        # Ajouter le contexte de mémoire utilisateur
        memory_context = get_user_context_for_prompt()
        if memory_context:
            enhanced_system_prompt += memory_context
            self.response_stats['memory_context_used'] += 1
        
        # Augmenter le prompt avec RAG avancé si disponible
        if self.rag_initialized and self.hybrid_search_engine:
            enhanced_system_prompt = self._augment_with_hybrid_search(
                prompt, enhanced_system_prompt
            )
            self.response_stats['hybrid_search_used'] += 1
        
        # Ajouter le message utilisateur à l'historique
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Générer la réponse de l'assistant
        with st.chat_message("assistant"):
            response = self._generate_enhanced_response(
                enhanced_system_prompt, 
                temperature
            )
            
            # Ajouter le turn à la mémoire contextuelle
            self.memory_system.add_conversation_turn(
                user_message=prompt,
                assistant_response=response,
                detected_intent=classify_user_question(prompt)
            )
            
            # Afficher les informations sur la recherche si RAG utilisé
            if self.rag_initialized and self.hybrid_search_engine:
                self._show_enhanced_search_info(prompt)
            
            return response
    
    def _augment_with_hybrid_search(self, user_query: str, base_prompt: str) -> str:
        """Augmente le prompt avec la recherche hybride avancée"""
        try:
            # Effectuer la recherche hybride
            search_results = self.hybrid_search_engine.search(
                user_query, 
                top_k=5, 
                mode=SearchMode.AUTO
            )
            
            if not search_results:
                logger.info("Aucun résultat de recherche hybride")
                return self._add_no_context_notice(base_prompt)
            
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
            
            if not context_parts:
                return self._add_no_context_notice(base_prompt)
            
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
            
            return augmented_prompt
            
        except Exception as e:
            logger.error(f"Erreur lors de l'augmentation hybride: {e}")
            return self._add_no_context_notice(base_prompt)
    
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
    
    def _generate_enhanced_response(self, system_prompt: str, temperature: float) -> str:
        """Génère une réponse avec streaming et gestion d'erreurs avancée"""
        
        # Préparer les messages pour l'API
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(st.session_state.messages)
        
        # Afficher le statut de traitement
        response_placeholder = st.empty()
        full_response = ""
        
        # Informations de debug si nécessaire
        if st.session_state.get('debug_mode', False):
            with st.expander("🔧 Informations de debug", expanded=False):
                st.markdown(f"**Profils détectés:** {detect_user_profiles(st.session_state.messages[-1]['content'], st.session_state.messages)}")
                st.markdown(f"**Type de question:** {classify_user_question(st.session_state.messages[-1]['content'])}")
                st.markdown(f"**Longueur du prompt système:** {len(system_prompt)} caractères")
                st.markdown(f"**Recherche hybride:** {'✅ Activée' if self.rag_initialized else '❌ Non disponible'}")
        
        try:
            # Streaming de la réponse
            for chunk in self._stream_response(messages, temperature):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            
            # Finaliser l'affichage
            response_placeholder.markdown(full_response)
            
            # Ajouter la réponse à l'historique
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # Extraire et afficher des recommandations structurées si disponibles
            recommendations = self._extract_json_recommendations(full_response)
            if recommendations:
                with st.expander("📊 Recommandations structurées"):
                    st.json(recommendations)
            
            return full_response
            
        except Exception as e:
            error_msg = f"Erreur lors de la génération: {str(e)}"
            logger.error(error_msg)
            response_placeholder.error(error_msg)
            return error_msg
    
    def _stream_response(self, messages: List[Dict], temperature: float):
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
    
    def _show_enhanced_search_info(self, user_query: str):
        """Affiche les informations détaillées sur la recherche hybride"""
        if not self.hybrid_search_engine:
            return
            
        try:
            # Obtenir les résultats de recherche pour affichage
            search_results = self.hybrid_search_engine.search(user_query, top_k=3)
            
            if search_results:
                with st.expander("🔍 Analyse de recherche hybride", expanded=False):
                    st.markdown("### Résultats de la recherche avancée")
                    
                    # Type de recherche utilisé
                    query_type = self.hybrid_search_engine.detect_query_type(user_query)
                    search_mode = self.hybrid_search_engine.select_search_mode(user_query, query_type)
                    
                    st.markdown(f"""
                    **Type de question détecté:** {query_type.value}  
                    **Mode de recherche optimal:** {search_mode.value}
                    """)
                    
                    # Détails des résultats
                    for i, result in enumerate(search_results, 1):
                        with st.expander(f"Résultat {i} - {result.chunk.source} (Score: {result.hybrid_score:.3f})"):
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**Scores de pertinence:**")
                                st.markdown(f"- Vectoriel (sémantique): {result.vector_score:.3f}")
                                st.markdown(f"- Mots-clés (factuel): {result.keyword_score:.3f}")
                                st.markdown(f"- **Hybride (final): {result.hybrid_score:.3f}**")
                            
                            with col2:
                                if result.matched_keywords:
                                    st.markdown("**Mots-clés matchés:**")
                                    st.markdown(f"- {', '.join(result.matched_keywords[:5])}")
                                
                                if result.relevance_factors:
                                    st.markdown("**Facteurs de boost:**")
                                    for factor, value in result.relevance_factors.items():
                                        st.markdown(f"- {factor}: {value:.2f}")
                            
                            # Aperçu du contenu
                            content_preview = result.chunk.content[:200] + "..." if len(result.chunk.content) > 200 else result.chunk.content
                            st.markdown(f"**Extrait:** {content_preview}")
            else:
                with st.expander("📄 Information de recherche", expanded=False):
                    st.info("🔍 Aucun résultat spécialisé trouvé - Utilisation des connaissances générales du modèle")
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des informations de recherche: {e}")
    
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
    
    def toggle_debug_mode(self):
        """Active/désactive le mode debug"""
        current_mode = st.session_state.get('debug_mode', False)
        st.session_state.debug_mode = not current_mode
        
        mode_str = "activé" if st.session_state.debug_mode else "désactivé"
        st.success(f"Mode debug {mode_str}")
    
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