"""
Main application file for OrientaBot - Conseiller d'orientation Maroc
Updated to work with enhanced prompts
"""
import streamlit as st
from ui.components import (
    setup_page_config, 
    render_header,
    apply_custom_styles
)
from ui.enhanced_components import (
    render_info_box,
    render_sidebar,
    render_footer,
    apply_enhanced_styles
)
from core.session_manager import SessionManager
from chat.enhanced_handler import EnhancedChatHandler
from chat.prompts import (
    get_system_prompt, 
    get_conversation_starters
)
from chat.enhanced_prompts import get_enhanced_system_prompt
from core.contextual_memory import get_contextual_memory_system

def get_appropriate_greeting():
    """
    Determine appropriate greeting based on conversation state
    """
    conversation_starters = get_conversation_starters()
    
    # If no messages yet, use first interaction greeting
    if not st.session_state.messages:
        return conversation_starters.get("first_interaction")
    
    return None

def display_welcome_message():
    """
    Display enhanced welcome message with contextual information
    """
    if not st.session_state.messages:
        # Show enhanced welcome message as a chat message from assistant
        with st.chat_message("assistant"):
            # Check if user has existing profile
            memory_system = get_contextual_memory_system()
            user_profile = memory_system.load_user_profile()
            
            if user_profile.nombre_conversations > 0:
                # Returning user
                welcome_msg = f"""👋 **Re-bonjour ! Content de vous retrouver !**

Je vois que nous avons déjà eu {user_profile.nombre_conversations} conversation(s) ensemble.

"""
                # Add contextual info if available
                if user_profile.filiere:
                    welcome_msg += f"- Je me souviens que vous êtes en **{user_profile.filiere.value}**\n"
                if user_profile.ville:
                    welcome_msg += f"- Vous êtes de **{user_profile.ville}**\n"
                if user_profile.interets:
                    welcome_msg += f"- Vos centres d'intérêt: **{', '.join(user_profile.interets[:3])}**\n"
                
                welcome_msg += "\nComment puis-je vous aider aujourd'hui dans votre orientation ? 🎯"
            else:
                # New user
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

def detect_user_context(prompt):
    """
    Simple context detection to adapt responses
    """
    prompt_lower = prompt.lower()
    
    # Detect emotional states or situations
    if any(word in prompt_lower for word in ["stress", "anxieux", "peur", "inquiet"]):
        return "anxious_student"
    elif any(word in prompt_lower for word in ["parents", "famille", "conflit"]):
        return "parent_pressure" 
    elif any(word in prompt_lower for word in ["excellent", "très bien", "18", "19", "20"]):
        return "high_achiever"
    elif any(word in prompt_lower for word in ["ne sais pas", "hésit", "confus", "perdu"]):
        return "uncertain"
    
    return "general"

def enhance_system_prompt_with_context(base_prompt, user_context):
    """
    Enhance the system prompt based on detected user context
    """
    context_additions = {
        "anxious_student": "\n\n# CONTEXTE SPÉCIAL: Étudiant anxieux détecté. Utilise un ton particulièrement rassurant et décompose les étapes de manière très claire.",
        "parent_pressure": "\n\n# CONTEXTE SPÉCIAL: Possible conflit familial détecté. Active le mode médiation pour trouver des solutions équilibrées.",
        "high_achiever": "\n\n# CONTEXTE SPÉCIAL: Étudiant excellent détecté. Propose des défis stimulants et des options d'excellence.",
        "uncertain": "\n\n# CONTEXTE SPÉCIAL: Étudiant indécis détecté. Focus sur la clarification des intérêts et des options."
    }
    
    return base_prompt + context_additions.get(user_context, "")

def main():
    """Main application function"""
    # Setup page configuration
    setup_page_config()
    
    # Apply enhanced styles
    apply_enhanced_styles()
    
    # Initialize session state
    SessionManager.initialize_session()
    
    # Initialize enhanced chat handler
    chat_handler = EnhancedChatHandler()
    
    # Initialize contextual memory system
    memory_system = get_contextual_memory_system()
    
    # Render header
    #render_header()
    
    # Render info box
    #render_info_box()
    
    # Render sidebar
    render_sidebar()
    
    # Main chat interface
    chat_container = st.container()
    
    with chat_container:
        # Display welcome message for first-time users
        display_welcome_message()
        
        # Display chat history
        SessionManager.display_chat_history()
        
        # Enhanced chat input with contextual processing
        if prompt := st.chat_input("Décrivez votre situation et posez votre question..."):
            # Process with enhanced handler (includes all improvements)
            chat_handler.process_chat_input(
                prompt, 
                get_system_prompt(),  # Base prompt (will be enriched automatically)
                SessionManager.get_temperature()
            )
    
    # Render footer
    #render_footer()

if __name__ == "__main__":
    main()