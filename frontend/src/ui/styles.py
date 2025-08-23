"""
Styles and CSS for the OrientaBot application
"""

def get_custom_css():
    """Return custom CSS styles for the application"""
    return """
    <style>
        .main-header {
            text-align: center;
            color: #2E86AB;
            margin-bottom: 1rem;
        }
        
        .chat-container {
            max-width: 800px;
            margin: 0 auto;
            padding-bottom: 120px;
        }
        
        .info-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 15px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .example-questions {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0 2rem 0;
        }
        
        .example-question {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 0.8rem;
            margin: 0.5rem 0;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .example-question:hover {
            background: #f0f8ff;
            border-color: #2E86AB;
            transform: translateY(-1px);
        }
        
        .settings-section {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .footer {
            text-align: center;
            color: #666;
            font-size: 0.9rem;
            margin-top: 2rem;
            padding: 1rem;
            border-top: 1px solid #eee;
            margin-bottom: 2rem;
        }
        
        /* Fixed bottom input styling */
        .stChatInput {
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            background: white !important;
            border-top: 2px solid #f0f2f6 !important;
            padding: 1rem !important;
            z-index: 999 !important;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1) !important;
        }
        
        .stChatInput > div {
            max-width: 800px !important;
            margin: 0 auto !important;
        }
        
        /* Ensure main content doesn't overlap with fixed input */
        .main .block-container {
            padding-bottom: 100px !important;
        }
        
        /* Chat messages container */
        .stChatMessage {
            margin-bottom: 1rem !important;
        }
        
        /* Sidebar adjustments */
        .css-1d391kg {
            padding-top: 1rem;
        }
    </style>
    """

def get_info_box_html():
    """Return HTML for the info box"""
    return """
    <div class="info-box">
        <h3>🌟 Votre conseiller d'orientation personnalisé</h3>
        <p>Posez-moi vos questions sur l'orientation post-bac au Maroc. Plus vous me donnez d'informations sur votre situation (filière, notes, intérêts, ville...), plus mes conseils seront précis et adaptés.</p>
    </div>
    """

def get_footer_html():
    """Return HTML for the footer"""
    return """
    <div class="footer">
        <p><strong>⚠️ Important:</strong> Les informations fournies sont indicatives. Vérifiez toujours les procédures et dates sur les sites officiels des établissements.</p>
        <p>OrientaBot v2.0 - Conseiller d'orientation académique pour le Maroc</p>
    </div>
    """