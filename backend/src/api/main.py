"""
FastAPI backend pour OrientaBot - API de conseil d'orientation
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from api.routes import chat, profile, search, system

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title="OrientaBot API",
    description="API de conseil d'orientation académique pour le Maroc",
    version="1.0.0"
)

# Configuration CORS pour permettre les connexions depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000"],  # Ports Streamlit et React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(system.router, prefix="/api/system", tags=["system"])

@app.get("/")
async def root():
    """Point d'entrée racine de l'API"""
    return {
        "message": "OrientaBot API - Conseiller d'orientation Maroc",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    try:
        # Ici on peut ajouter des vérifications de santé (base de données, services externes, etc.)
        return {
            "status": "healthy",
            "message": "API opérationnelle"
        }
    except Exception as e:
        logger.error(f"Erreur lors du health check: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "message": f"Erreur: {str(e)}"
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)