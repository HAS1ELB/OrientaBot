"""
Main application file for OrientaBot - Conseiller d'orientation Maroc
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
from prompts import get_system_prompt

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
        # Display chat history
        SessionManager.display_chat_history()
        
        # Chat input
        if prompt := st.chat_input("Décrivez votre situation et posez votre question..."):
            chat_handler.process_chat_input(
                prompt, 
                get_system_prompt(), 
                SessionManager.get_temperature()
            )
    
    # Render footer
    render_footer()

if __name__ == "__main__":
    main()