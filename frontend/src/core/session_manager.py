"""
Session state management for the OrientaBot application
"""
import streamlit as st
from backend.src.core.config import DEFAULT_TEMPERATURE

class SessionManager:
    @staticmethod
    def initialize_session():
        """Initialize session state variables"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "temperature" not in st.session_state:
            st.session_state.temperature = DEFAULT_TEMPERATURE
    
    @staticmethod
    def clear_chat():
        """Clear chat history"""
        st.session_state.messages = []
        st.rerun()
    
    @staticmethod
    def get_messages():
        """Get chat messages from session state"""
        return st.session_state.messages
    
    @staticmethod
    def get_temperature():
        """Get temperature setting from session state"""
        return st.session_state.temperature
    
    @staticmethod
    def set_temperature(temperature):
        """Set temperature in session state"""
        st.session_state.temperature = temperature
    
    @staticmethod
    def display_chat_history():
        """Display chat history"""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])