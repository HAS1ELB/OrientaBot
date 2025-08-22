"""
Module ui - Interface utilisateur
Contient les composants et styles de l'interface utilisateur Streamlit
"""

# Import components seulement si streamlit est disponible
try:
    from .components import (
        setup_page_config,
        render_header,
        render_info_box,
        render_sidebar,
        render_footer,
        apply_custom_styles
    )
    __all__ = [
        'setup_page_config',
        'render_header', 
        'render_info_box',
        'render_sidebar',
        'render_footer',
        'apply_custom_styles'
    ]
except ImportError:
    __all__ = []