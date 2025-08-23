"""
Frontend Streamlit pour OrientaBot - Conseiller d'orientation Maroc
Version adaptée pour communiquer avec l'API backend
"""
import streamlit as st
import logging
from uuid import uuid4
from ui.components import (
    setup_page_config, 
    render_header,
    apply_custom_styles
)
from ui.enhanced_components import (
    render_sidebar,
    apply_enhanced_styles
)
from core.session_manager import SessionManager
from services.api_client import get_api_client, test_api_connection, ChatResponse

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_or_create_session_id() -> str:
    """Génère ou récupère l'ID de session"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid4())
    return st.session_state.session_id

def display_welcome_message():
    """
    Affiche le message de bienvenue avec informations contextuelles
    """
    if not st.session_state.messages:
        # Afficher le message de bienvenue enrichi
        with st.chat_message("assistant"):
            welcome_msg = """👋 **Bienvenue ! Je suis Dr. Karima Benjelloun, votre conseillère d'orientation intelligente.**

🧠 **Système Avancé Activé** - Je dispose maintenant de capacités enrichies :
- 🎯 **Analyse personnalisée** de votre profil académique et personnel
- 🔍 **Recherche hybride** dans ma base de connaissances spécialisée
- 💭 **Mémoire contextuelle** pour des conseils de plus en plus précis
- 🎭 **Adaptation automatique** selon votre situation et personnalité

Pour commencer, parlez-moi de :
- 📚 **Votre filière et résultats** (ex: "Je suis en SM-B avec 15 de moyenne")
- ❤️ **Vos passions et intérêts** 
- 🤔 **Votre situation** (contraintes, préoccupations, famille)
- 🎯 **Vos objectifs** ou questions précises

Plus vous partagez, plus mes conseils seront personnalisés et efficaces ! ✨"""
            
            st.markdown(welcome_msg)

def display_api_status():
    """Affiche le statut de connexion à l'API"""
    if test_api_connection():
        st.sidebar.success("🟢 API Backend connectée")
    else:
        st.sidebar.error("🔴 API Backend déconnectée")
        st.sidebar.warning("Vérifiez que le backend est démarré sur le port 8000")

def process_user_message(prompt: str):
    """
    Traite le message utilisateur via l'API
    
    Args:
        prompt: Message de l'utilisateur
    """
    # Ajouter le message utilisateur à l'historique
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Générer la réponse via l'API
    with st.chat_message("assistant"):
        try:
            # Récupérer le client API
            api_client = get_api_client()
            
            # Préparer l'historique de conversation pour l'API
            conversation_history = [
                {"role": msg["role"], "content": msg["content"]} 
                for msg in st.session_state.messages[:-1]  # Exclure le dernier message (déjà ajouté)
            ]
            
            # Afficher un indicateur de chargement
            with st.spinner("💭 Réflexion en cours..."):
                # Envoyer le message à l'API
                response = api_client.send_message(
                    message=prompt,
                    session_id=get_or_create_session_id(),
                    temperature=SessionManager.get_temperature(),
                    conversation_history=conversation_history
                )
            
            if response.error:
                # Afficher l'erreur
                st.error(f"❌ Erreur: {response.error}")
                error_response = "Désolé, une erreur s'est produite. Veuillez réessayer."
                st.markdown(error_response)
                st.session_state.messages.append({"role": "assistant", "content": error_response})
            else:
                # Afficher la réponse
                st.markdown(response.response)
                st.session_state.messages.append({"role": "assistant", "content": response.response})
                
                # Afficher les recommandations si disponibles
                if response.recommendations:
                    with st.expander("📊 Recommandations structurées"):
                        st.json(response.recommendations)
                
                # Afficher les informations de contexte si disponibles
                if response.context_info and response.context_info.get("sources_used"):
                    with st.expander("🔍 Sources consultées", expanded=False):
                        st.markdown("**Informations trouvées dans:**")
                        for i, source in enumerate(response.context_info["sources_used"], 1):
                            st.markdown(f"{i}. **{source['source']}** (Page {source['page_number']}) - Pertinence: {source['confidence']}")
                            with st.expander(f"Extrait {i}"):
                                st.markdown(source["excerpt"])
                
                # Afficher un indicateur si RAG est utilisé
                if response.rag_available:
                    st.sidebar.info("🧠 Système RAG activé")
                else:
                    st.sidebar.info("💡 Mode connaissances générales")
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}")
            st.error(f"❌ Erreur de communication: {str(e)}")
            error_response = "Impossible de communiquer avec le serveur. Veuillez vérifier votre connexion."
            st.markdown(error_response)
            st.session_state.messages.append({"role": "assistant", "content": error_response})

def process_user_message_streaming(prompt: str):
    """
    Traite le message utilisateur avec streaming via l'API
    
    Args:
        prompt: Message de l'utilisateur
    """
    # Ajouter le message utilisateur à l'historique
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Générer la réponse via l'API avec streaming
    with st.chat_message("assistant"):
        try:
            # Récupérer le client API
            api_client = get_api_client()
            
            # Préparer l'historique de conversation pour l'API
            conversation_history = [
                {"role": msg["role"], "content": msg["content"]} 
                for msg in st.session_state.messages[:-1]  # Exclure le dernier message (déjà ajouté)
            ]
            
            # Placeholder pour la réponse streaming
            response_placeholder = st.empty()
            full_response = ""
            
            # Stream la réponse
            for chunk in api_client.stream_message(
                message=prompt,
                session_id=get_or_create_session_id(),
                temperature=SessionManager.get_temperature(),
                conversation_history=conversation_history
            ):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            
            # Finaliser l'affichage
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            logger.error(f"Erreur lors du streaming: {e}")
            st.error(f"❌ Erreur de streaming: {str(e)}")
            error_response = "Erreur lors du streaming. Mode standard activé."
            st.markdown(error_response)
            st.session_state.messages.append({"role": "assistant", "content": error_response})

def render_debug_panel():
    """Affiche le panneau de debug si activé"""
    if st.session_state.get('debug_mode', False):
        with st.sidebar.expander("🔧 Debug", expanded=False):
            st.markdown("**Session Info:**")
            st.markdown(f"- Session ID: {get_or_create_session_id()}")
            st.markdown(f"- Messages: {len(st.session_state.messages)}")
            st.markdown(f"- Temperature: {SessionManager.get_temperature()}")
            
            # Test API
            if st.button("Test API"):
                result = test_api_connection()
                if result:
                    st.success("✅ API OK")
                else:
                    st.error("❌ API KO")
            
            # Stats système
            if st.button("Stats Système"):
                try:
                    api_client = get_api_client()
                    stats = api_client.get_system_stats(include_detailed=True)
                    if "error" not in stats:
                        st.json(stats)
                    else:
                        st.error(f"Erreur: {stats['error']}")
                except Exception as e:
                    st.error(f"Erreur: {e}")

def main():
    """Fonction principale de l'application"""
    # Configuration de la page
    setup_page_config()
    
    # Application des styles
    apply_enhanced_styles()
    
    # Initialisation de la session
    SessionManager.initialize_session()
    
    # Vérification de la connexion API
    display_api_status()
    
    # Interface principale
    render_header()
    render_sidebar()
    
    # Panneau de debug
    render_debug_panel()
    
    # Interface de chat principal
    chat_container = st.container()
    
    with chat_container:
        # Message de bienvenue pour les nouveaux utilisateurs
        display_welcome_message()
        
        # Affichage de l'historique de chat
        SessionManager.display_chat_history()
        
        # Interface de chat avec traitement API
        if prompt := st.chat_input("Décrivez votre situation et posez votre question..."):
            # Option pour choisir le mode de traitement
            use_streaming = st.session_state.get('streaming_enabled', True)
            
            if use_streaming:
                process_user_message_streaming(prompt)
            else:
                process_user_message(prompt)

if __name__ == "__main__":
    main()