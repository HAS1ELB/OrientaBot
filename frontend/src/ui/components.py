"""
UI components for the OrientaBot application
"""
import streamlit as st
from .styles import get_custom_css, get_info_box_html, get_footer_html
import sys , os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)
from backend.src.chat.prompts import get_tips_sidebar
from core.session_manager import SessionManager

def setup_page_config():
    """Configure the Streamlit page"""
    from backend.src.core.config import APP_TITLE, APP_ICON, PAGE_LAYOUT, SIDEBAR_STATE
    
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout=PAGE_LAYOUT,
        initial_sidebar_state=SIDEBAR_STATE
    )

def render_header():
    """Render the main header"""
    st.markdown('<h1 class="main-header">🎓 OrientaBot - Conseiller d\'orientation Maroc</h1>', unsafe_allow_html=True)

def render_info_box():
    """Render the information box"""
    st.markdown(get_info_box_html(), unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar with settings"""
    with st.sidebar:
        st.header("⚙️ Paramètres")
        
        temperature = st.slider(
            "Créativité des réponses", 
            min_value=0.0, 
            max_value=1.0, 
            value=SessionManager.get_temperature(), 
            step=0.1,
            help="Plus élevé = plus créatif, plus bas = plus factuel"
        )
        SessionManager.set_temperature(temperature)
        
        st.markdown("---")
        
        if st.button("🔄 Nouvelle conversation", use_container_width=True):
            SessionManager.clear_chat()
        
        st.markdown("---")
        
        st.markdown(get_tips_sidebar())

def render_footer():
    """Render the footer"""
    st.markdown(get_footer_html(), unsafe_allow_html=True)

def apply_custom_styles():
    """Apply custom CSS styles"""
    st.markdown(get_custom_css(), unsafe_allow_html=True)