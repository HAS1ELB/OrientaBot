"""
Script de lancement pour le backend OrientaBot
"""
import os
import sys
import uvicorn
from pathlib import Path

# Ajouter le dossier src au PYTHONPATH
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def main():
    """Lance le serveur FastAPI"""
    
    # Configuration depuis les variables d'environnement
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("DEBUG", "True").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    print(f"🚀 Lancement du backend OrientaBot")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Reload: {reload}")
    print(f"   Log Level: {log_level}")
    print(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    # Lancement du serveur
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )

if __name__ == "__main__":
    main()