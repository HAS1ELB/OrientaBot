"""
Chat handling and API interaction module with RAG support
"""
import json
import re
import streamlit as st
import logging
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL, MAX_TOKENS

# Import RAG components
try:
    from rag_manager import RAGManager
    RAG_AVAILABLE = True
    logger = logging.getLogger(__name__)
except ImportError as e:
    RAG_AVAILABLE = False
    print(f"Warning: RAG components not available: {e}")

class ChatHandler:
    def __init__(self):
        """Initialize the chat handler with Groq client and RAG manager"""
        if not GROQ_API_KEY:
            st.error("⌚ GROQ_API_KEY manquant. Configurez votre .env file avec votre clé API Groq.")
            st.stop()
        
        self.client = Groq(api_key=GROQ_API_KEY)
        
        # Initialize RAG manager if available
        self.rag_manager = None
        self.rag_initialized = False
        
        if RAG_AVAILABLE:
            self._initialize_rag()
    
    def stream_response(self, messages, temperature=0.7):
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
            yield f"Erreur: {str(e)}"
    
    def extract_json_recommendations(self, text):
        """Extract JSON recommendations if present"""
        pattern = r"```json\s*(\{.*?\})\s*```"
        match = re.search(pattern, text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        return None
    
    def process_chat_input(self, prompt, system_prompt, temperature):
        """Process user input and generate response with RAG support"""
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            # Augment the system prompt with RAG if available
            augmented_prompt = self._get_augmented_prompt(prompt, system_prompt)
            
            # Prepare messages for API
            messages = [{"role": "system", "content": augmented_prompt}]
            messages.extend(st.session_state.messages)
            
            # Stream response
            response_placeholder = st.empty()
            full_response = ""
            
            # Show RAG status if available
            if self.rag_manager and self.rag_initialized:
                with st.spinner("🔍 Recherche dans la base de connaissances..."):
                    pass  # RAG search is done in _get_augmented_prompt
            
            for chunk in self.stream_response(messages, temperature):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
            # Add assistant message to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # Check for JSON recommendations
            recommendations = self.extract_json_recommendations(full_response)
            if recommendations:
                with st.expander("📊 Recommandations structurées"):
                    st.json(recommendations)
            
            # Show RAG info if used
            self._show_rag_info(prompt)
            
            return full_response
    
    def _initialize_rag(self):
        """Initialize the RAG manager"""
        try:
            if 'rag_manager' not in st.session_state:
                with st.spinner("🚀 Initialisation du système RAG..."):
                    self.rag_manager = RAGManager()
                    
                    # Initialize knowledge base
                    success = self.rag_manager.initialize_knowledge_base()
                    
                    if success:
                        st.session_state.rag_manager = self.rag_manager
                        self.rag_initialized = True
                        logger.info("✅ Système RAG initialisé avec succès")
                        
                        # Show success message
                        stats = self.rag_manager.get_stats()
                        st.success(f"🧪 Base de connaissances chargée: {stats['vector_store_stats']['total_chunks']} chunks depuis {stats['pdf_files_count']} PDF(s)")
                    else:
                        logger.warning("⚠️ Échec de l'initialisation RAG - Mode connaissances générales activé")
                        st.warning("📁 Mode connaissances générales activé. Pour bénéficier d'informations spécialisées, ajoutez des PDFs d'écoles dans le dossier 'pdfs'.")
            else:
                self.rag_manager = st.session_state.rag_manager
                self.rag_initialized = True
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation RAG: {e}")
            st.error(f"🚫 Erreur RAG: {e}")
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
    
    def _show_rag_info(self, user_query: str):
        """Show RAG information and search results if available"""
        if self.rag_manager and self.rag_initialized:
            # Get search results for info display
            try:
                search_results = self.rag_manager.search_knowledge(user_query, top_k=3)
                
                if search_results:
                    with st.expander("🔍 Sources consultées", expanded=False):
                        st.markdown("**Informations trouvées dans:**")
                        for i, (chunk, score) in enumerate(search_results, 1):
                            confidence = "Haute" if score > 0.8 else "Moyenne" if score > 0.6 else "Faible"
                            st.markdown(f"{i}. **{chunk.source}** (Page {chunk.page_number}) - Pertinence: {confidence}")
                            with st.expander(f"Extrait {i}"):
                                st.markdown(chunk.content[:300] + "..." if len(chunk.content) > 300 else chunk.content)
                else:
                    with st.expander("📄 Information", expanded=False):
                        st.info("🧪 Aucune information spécialisée trouvée pour cette question. Réponse basée sur les connaissances générales.")
                        
            except Exception as e:
                logger.error(f"Erreur lors de l'affichage des infos RAG: {e}")
    
    def get_rag_stats(self) -> dict:
        """Get RAG system statistics"""
        if self.rag_manager and self.rag_initialized:
            return self.rag_manager.get_stats()
        return {'status': 'non_disponible'}