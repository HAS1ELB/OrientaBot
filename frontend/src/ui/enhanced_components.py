"""
Composants UI enrichis pour OrientaBot avec toutes les améliorations
"""
import streamlit as st
import json
from datetime import datetime
from typing import Optional, Dict, Any

# Import des modules de base
from .styles import get_custom_css, get_info_box_html, get_footer_html
from chat.prompts import get_tips_sidebar
from core.session_manager import SessionManager

# Import des modules enrichis
from core.contextual_memory import get_contextual_memory_system
from chat.enhanced_prompts import detect_user_profiles, classify_user_question

def render_enhanced_sidebar():
    """Sidebar enrichie avec nouvelles fonctionnalités et statistiques"""
    with st.sidebar:
        # Titre avec indicateur de version
        st.markdown("### ⚙️ Paramètres Avancés")
        st.caption("🚀 Version Enrichie Activée")
        
        # Paramètres existants
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
        
        # Gestion des conversations et profil
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Nouveau", use_container_width=True):
                SessionManager.clear_chat()
        
        with col2:
            if st.button("👤 Profil", use_container_width=True):
                show_user_profile_modal()
        
        # Mode debug
        debug_mode = st.session_state.get('debug_mode', False)
        if st.checkbox("🔧 Mode debug", value=debug_mode):
            st.session_state.debug_mode = True
        else:
            st.session_state.debug_mode = False
        
        st.markdown("---")
        
        # Informations système enrichies
        render_system_status()
        
        st.markdown("---")
        
        # Conseils d'utilisation enrichis
        render_enhanced_tips()
        
        st.markdown("---")
        
        # Statistiques utilisateur
        render_user_stats()

def show_user_profile_modal():
    """Affiche le profil utilisateur dans une modal"""
    memory_system = get_contextual_memory_system()
    user_profile = memory_system.load_user_profile()
    
    if user_profile:
        st.markdown("#### 👤 Votre Profil Actuel")
        
        # Informations académiques
        if user_profile.filiere or user_profile.moyenne_generale:
            st.markdown("**📚 Académique:**")
            if user_profile.filiere:
                st.write(f"- Filière: {user_profile.filiere.value}")
            if user_profile.moyenne_generale:
                st.write(f"- Moyenne: {user_profile.moyenne_generale}/20")
        
        # Informations personnelles
        if user_profile.ville or user_profile.interets:
            st.markdown("**🏠 Personnel:**")
            if user_profile.ville:
                st.write(f"- Ville: {user_profile.ville}")
            if user_profile.interets:
                st.write(f"- Intérêts: {', '.join(user_profile.interets[:3])}")
        
        # Traits de personnalité détectés
        if user_profile.traits_personnalite:
            st.markdown("**🧠 Personnalité détectée:**")
            traits = [t.value for t in user_profile.traits_personnalite[:3]]
            st.write(f"- {', '.join(traits)}")
        
        # Statistiques
        st.markdown("**📊 Historique:**")
        st.write(f"- Conversations: {user_profile.nombre_conversations}")
        st.write(f"- Confiance orientation: {user_profile.confiance_orientation}/5")
        
        # Option de suppression
        if st.button("🗑️ Supprimer mes données", type="secondary"):
            if st.button("⚠️ Confirmer la suppression", type="secondary"):
                memory_system.clear_user_data()
                st.success("Données supprimées")
                st.rerun()

def render_system_status():
    """Affiche le statut des systèmes enrichis"""
    st.markdown("#### 🔧 Statut Système")
    
    # Vérifier les systèmes
    memory_system = get_contextual_memory_system()
    
    # Mémoire contextuelle
    memory_status = "✅" if memory_system.current_profile else "⚪"
    st.markdown(f"{memory_status} **Mémoire contextuelle**")
    
    # RAG System
    rag_status = "✅" if st.session_state.get('enhanced_rag_manager') else "❌"
    st.markdown(f"{rag_status} **Système RAG avancé**")
    
    # Recherche hybride
    hybrid_status = "✅" if st.session_state.get('hybrid_search_engine') else "❌"
    st.markdown(f"{hybrid_status} **Recherche hybride**")
    
    # Profil utilisateur
    profile_status = "✅" if memory_system.current_profile and memory_system.current_profile.nombre_conversations > 0 else "⚪"
    st.markdown(f"{profile_status} **Profil utilisateur**")

def render_enhanced_tips():
    """Conseils d'utilisation enrichis"""
    st.markdown("#### 💡 Conseils Enrichis")
    
    with st.expander("🎯 Optimiser vos réponses", expanded=False):
        st.markdown("""
        **Pour de meilleurs conseils personnalisés:**
        
        🎓 **Profil académique:**
        - Mentionnez votre filière (SM-A, SP, SVT...)
        - Indiquez vos notes/moyennes
        - Précisez vos matières fortes/faibles
        
        🏠 **Contexte personnel:**
        - Votre ville/région
        - Vos centres d'intérêt
        - Contraintes familiales/budgétaires
        
        💭 **État d'esprit:**
        - Vos inquiétudes ou stress
        - Votre niveau de confiance
        - Votre ouverture au changement
        """)
    
    with st.expander("🔍 Types de questions", expanded=False):
        st.markdown("""
        **Le système détecte automatiquement:**
        
        📊 **Questions factuelles** → Recherche mots-clés
        - "Quel est le seuil de l'ENSA Rabat ?"
        - "Combien coûte l'EMSI ?"
        
        🤔 **Questions conceptuelles** → Recherche sémantique  
        - "Qu'est-ce que le génie informatique ?"
        - "Pourquoi choisir l'ingénierie ?"
        
        ⚖️ **Questions comparatives** → Recherche hybride
        - "ENSA vs EMSI : quelle différence ?"
        - "Mieux vaut médecine ou ingénierie ?"
        """)

def render_user_stats():
    """Affiche les statistiques utilisateur"""
    memory_system = get_contextual_memory_system()
    
    if not memory_system.current_profile:
        return
    
    st.markdown("#### 📊 Vos Statistiques")
    
    profile = memory_system.current_profile
    
    # Métriques principales
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Conversations", profile.nombre_conversations)
        st.metric("Confiance", f"{profile.confiance_orientation}/5")
    
    with col2:
        st.metric("Infos détectées", len(profile.interets) + len(profile.valeurs))
        st.metric("Traits détectés", len(profile.traits_personnalite))
    
    # Progression dans l'orientation
    if profile.nombre_conversations > 0:
        progression = min(profile.nombre_conversations * 20, 100)
        st.progress(progression / 100)
        st.caption(f"Progression dans l'orientation: {progression}%")

def render_enhanced_info_box():
    """Boîte d'information enrichie avec nouvelles fonctionnalités"""
    info_html = f"""
    <div class="info-box">
        <h3>🎓 OrientaBot - Version Enrichie</h3>
        <p><strong>🧠 Intelligence Avancée :</strong></p>
        <ul>
            <li>🎯 <strong>Personnalisation automatique</strong> selon votre profil</li>
            <li>🔍 <strong>Recherche hybride</strong> dans la base de connaissances</li>
            <li>💭 <strong>Mémoire contextuelle</strong> de vos conversations</li>
            <li>🎭 <strong>Adaptation d'experts</strong> selon vos besoins</li>
        </ul>
        <p><strong>📚 Base de connaissances :</strong> Informations officielles sur les établissements marocains</p>
        <p><strong>🎯 Conseil :</strong> Plus vous partagez d'informations, plus mes conseils deviennent précis !</p>
    </div>
    """
    st.markdown(info_html, unsafe_allow_html=True)

def render_conversation_insights():
    """Affiche des insights sur la conversation en cours"""
    if not st.session_state.get('debug_mode', False):
        return
    
    if not st.session_state.messages:
        return
    
    with st.sidebar.expander("🔍 Insights Conversation", expanded=False):
        last_message = st.session_state.messages[-1]['content']
        
        # Profils détectés
        profiles = detect_user_profiles(last_message, st.session_state.messages)
        if profiles:
            st.markdown(f"**Profils:** {', '.join(profiles)}")
        
        # Type de question
        question_type = classify_user_question(last_message)
        st.markdown(f"**Type:** {question_type}")
        
        # Longueur de conversation
        st.markdown(f"**Messages:** {len(st.session_state.messages)}")

def render_enhanced_footer():
    """Footer enrichi avec informations sur les améliorations"""
    footer_html = f"""
    <div class="footer">
        <div class="footer-content">
            <div class="footer-section">
                <h4>🎓 OrientaBot Enrichi</h4>
                <p>Conseiller d'orientation intelligent pour le système éducatif marocain</p>
                <p><strong>Version:</strong> 2.0 - Système Avancé</p>
            </div>
            
            <div class="footer-section">
                <h4>🚀 Nouvelles Fonctionnalités</h4>
                <ul>
                    <li>🎯 Personnalisation automatique</li>
                    <li>🔍 Recherche hybride avancée</li>
                    <li>💭 Mémoire contextuelle</li>
                    <li>🎭 Adaptation d'experts</li>
                </ul>
            </div>
            
            <div class="footer-section">
                <h4>📊 Performance</h4>
                <p>✅ Système RAG: {'Activé' if st.session_state.get('enhanced_rag_manager') else 'Désactivé'}</p>
                <p>🔍 Recherche hybride: {'Activée' if st.session_state.get('hybrid_search_engine') else 'Désactivée'}</p>
                <p>💭 Mémoire: {'Active' if get_contextual_memory_system().current_profile else 'Inactive'}</p>
            </div>
        </div>
        
        <div class="footer-bottom">
            <p>🤖 Développé avec ❤️ pour l'orientation des étudiants marocains | {datetime.now().year}</p>
            <p><em>⚠️ Vérifiez toujours les informations sur les sites officiels des établissements</em></p>
        </div>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

def display_system_performance():
    """Affiche les métriques de performance du système enrichi"""
    if not st.session_state.get('debug_mode', False):
        return
    
    # Obtenir les statistiques des différents composants
    memory_system = get_contextual_memory_system()
    
    with st.expander("📊 Métriques Système", expanded=False):
        
        # Métriques de mémoire
        memory_stats = memory_system.get_memory_stats()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**💭 Mémoire**")
            st.write(f"Profil chargé: {'✅' if memory_stats['profile_loaded'] else '❌'}")
            st.write(f"Session active: {'✅' if memory_stats['session_active'] else '❌'}")
            st.write(f"Tours conversation: {memory_stats['turns_in_session']}")
        
        with col2:
            st.markdown("**🔍 RAG**")
            if st.session_state.get('enhanced_rag_manager'):
                rag_stats = st.session_state.enhanced_rag_manager.get_stats()
                st.write(f"Chunks: {rag_stats['vector_store_stats']['total_chunks']}")
                st.write(f"Sources: {rag_stats['pdf_files_count']}")
            else:
                st.write("Non disponible")
        
        with col3:
            st.markdown("**🔧 Système**")
            st.write(f"Messages: {len(st.session_state.messages)}")
            st.write(f"User ID: {memory_stats.get('user_id', 'N/A')[:8]}...")

# Fonction principale pour remplacer render_sidebar
def render_sidebar():
    """Point d'entrée pour la sidebar enrichie"""
    render_enhanced_sidebar()
    
    # Insights de conversation en mode debug
    render_conversation_insights()
    
    # Métriques système en mode debug
    display_system_performance()

# Fonction pour remplacer render_info_box
def render_info_box():
    """Point d'entrée pour la boîte d'information enrichie"""
    render_enhanced_info_box()

# Fonction pour remplacer render_footer  
def render_footer():
    """Point d'entrée pour le footer enrichi"""
    render_enhanced_footer()

# CSS enrichi pour les nouveaux composants
def get_enhanced_css():
    """CSS enrichi pour les nouveaux composants"""
    return """
    <style>
    .footer {
        margin-top: 50px;
        padding: 30px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
    }
    
    .footer-content {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin-bottom: 20px;
    }
    
    .footer-section h4 {
        margin-bottom: 10px;
        color: #fff;
    }
    
    .footer-section ul {
        list-style: none;
        padding: 0;
    }
    
    .footer-section li {
        margin: 5px 0;
        padding-left: 15px;
    }
    
    .footer-bottom {
        border-top: 1px solid rgba(255,255,255,0.2);
        padding-top: 15px;
        text-align: center;
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 10px 0;
    }
    
    .system-status {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 5px 0;
    }
    
    .profile-info {
        background: linear-gradient(90deg, #667eea, #764ba2);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    </style>
    """

def apply_enhanced_styles():
    """Applique tous les styles enrichis"""
    from .styles import get_custom_css
    
    # CSS de base + CSS enrichi
    all_css = get_custom_css() + get_enhanced_css()
    st.markdown(all_css, unsafe_allow_html=True)