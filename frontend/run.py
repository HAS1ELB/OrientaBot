"""
Script de lancement pour le frontend OrientaBot Streamlit
"""
import os
import sys
import subprocess
from pathlib import Path

# Ajouter le dossier src au PYTHONPATH
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def main():
    """Lance l'application Streamlit"""
    
    # Configuration depuis les variables d'environnement
    host = os.getenv("STREAMLIT_HOST", "0.0.0.0")
    port = int(os.getenv("STREAMLIT_PORT", 8501))
    backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")
    
    print(f"🎨 Lancement du frontend OrientaBot")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Backend API: {backend_url}")
    
    # Définir les variables d'environnement pour Streamlit
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_dir)
    
    # Commande Streamlit
    cmd = [
        "streamlit", "run", 
        str(src_dir / "main.py"),
        "--server.address", host,
        "--server.port", str(port),
        "--theme.base", "light",
        "--theme.primaryColor", "#FF6B6B",
        "--theme.backgroundColor", "#FFFFFF",
        "--theme.secondaryBackgroundColor", "#F0F2F6"
    ]
    
    # Lancer Streamlit
    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n👋 Arrêt du frontend OrientaBot")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du lancement: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()