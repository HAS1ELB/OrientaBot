"""
Main application file for OrientaBot - Conseiller d'orientation Maroc
Updated to work with enhanced prompts
"""
import streamlit as st
from components import (
    setup_page_config, 
    render_header, 
    render_info_box, 
    render_sidebar, 
    render_footer,
    apply_custom_styles
)
from session_manager import SessionManager
from chat_handler import ChatHandler
from prompts import (
    get_system_prompt, 
    get_conversation_starters
)

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
    Display welcome message with conversation starters if it's the first interaction
    """
    if not st.session_state.messages:
        # Show welcome message as a chat message from assistant
        with st.chat_message("assistant"):
            welcome_msg = """👋 **Bienvenue ! Je suis Dr. Karima Benjelloun, votre conseillère d'orientation.**

Avec 15 ans d'expérience dans le système éducatif marocain, je suis là pour vous accompagner dans vos choix d'orientation post-bac.

Pour notre première conversation, j'aimerais mieux vous connaître. Pouvez-vous me parler de:
- 📚 Votre filière actuelle et vos résultats
- ❤️ Ce qui vous passionne ou vous intéresse  
- 🤔 Vos préoccupations principales concernant l'orientation

Plus vous me donnez d'informations, plus mes conseils seront personnalisés et utiles! 😊"""
            
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
    
    # Apply custom styles
    apply_custom_styles()
    
    # Initialize session state
    SessionManager.initialize_session()
    
    # Initialize chat handler
    chat_handler = ChatHandler()
    
    # Render header
    render_header()
    
    # Render info box
    render_info_box()
    
    # Render sidebar
    render_sidebar()
    
    # Main chat interface
    chat_container = st.container()
    
    with chat_container:
        # Display welcome message for first-time users
        display_welcome_message()
        
        # Display chat history
        SessionManager.display_chat_history()
        
        # Chat input
        if prompt := st.chat_input("Décrivez votre situation et posez votre question..."):
            # Detect user context for adaptive responses
            user_context = detect_user_context(prompt)
            
            # Get base system prompt
            base_system_prompt = get_system_prompt()
            
            # Enhance prompt with context
            enhanced_system_prompt = enhance_system_prompt_with_context(
                base_system_prompt, 
                user_context
            )
            
            # Process chat input with enhanced prompt
            chat_handler.process_chat_input(
                prompt, 
                enhanced_system_prompt, 
                SessionManager.get_temperature()
            )
    
    # Render footer
    render_footer()

if __name__ == "__main__":
    main()