# OrientaBot - Architecture Frontend/Backend

## 🎯 Résultat de la Séparation

Le projet OrientaBot a été séparé avec succès en deux applications distinctes :

### 🖥️ **Backend (API FastAPI)** - `/backend/`
- **API REST** complète avec FastAPI
- **Logique métier** (chat, RAG, mémoire contextuelle)  
- **Base de données vectorielle** et système de recherche hybride
- **Port par défaut**: 8000

### 🎨 **Frontend (Interface Streamlit)** - `/frontend/`  
- **Interface utilisateur** moderne avec Streamlit
- **Client API** pour communiquer avec le backend
- **Gestion de session** et état utilisateur
- **Port par défaut**: 8501

## 🚀 Instructions de Lancement

### 1. Démarrer le Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Configurer GROQ_API_KEY dans .env
python run.py
```

### 2. Démarrer le Frontend  
```bash
cd frontend
pip install -r requirements.txt
cp .env.example .env
# Configurer BACKEND_API_URL=http://localhost:8000
python run.py
```

### 3. Accès
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **Documentation API**: http://localhost:8000/docs

## 📁 Structure Détaillée

```
OrientaBot/
├── backend/                    # API Backend
│   ├── src/
│   │   ├── api/               # Routes FastAPI
│   │   │   ├── main.py        # Application principale
│   │   │   ├── models/        # Modèles Pydantic
│   │   │   └── routes/        # Routes (chat, profile, search, system)
│   │   ├── chat/              # Gestionnaires de conversation
│   │   ├── core/              # Configuration et mémoire
│   │   ├── rag/               # Système RAG et recherche
│   │   └── utils/             # Utilitaires
│   ├── data/                  # Données partagées
│   ├── requirements.txt       # Dépendances backend
│   └── run.py                 # Script de lancement
│
├── frontend/                   # Interface Utilisateur  
│   ├── src/
│   │   ├── main.py            # Application Streamlit
│   │   ├── ui/                # Composants d'interface
│   │   ├── core/              # Session manager Streamlit
│   │   └── services/          # Client API
│   ├── requirements.txt       # Dépendances frontend
│   └── run.py                 # Script de lancement
│
├── data/                      # Données originales (référence)
└── README.md       # Cette documentation
```

## 🔄 Communication Frontend/Backend

Le frontend communique avec le backend via l'API REST :

- **POST /api/chat/message** - Envoi de messages
- **GET /api/chat/history/{session_id}** - Historique
- **POST /api/profile/{user_id}** - Gestion profils
- **POST /api/search/** - Recherche RAG
- **GET /api/system/stats** - Statistiques

## ✅ Avantages de cette Architecture

1. **🔧 Maintenance** - Séparation claire des responsabilités
2. **📈 Scalabilité** - Backend et frontend indépendants
3. **🔒 Sécurité** - API centralisée avec authentification possible
4. **🚀 Performance** - Chaque service optimisé pour son rôle
5. **🔄 Flexibilité** - Possibilité de créer d'autres interfaces
6. **🐳 Déploiement** - Containers Docker indépendants

## 🐛 Résolution de Problèmes

### Backend ne démarre pas
- Vérifier que GROQ_API_KEY est configuré
- Contrôler que le port 8000 est libre

### Frontend ne se connecte pas au Backend
- Vérifier que le backend est démarré
- Contrôler BACKEND_API_URL dans frontend/.env
- Tester http://localhost:8000/health

### Données manquantes
- Les PDFs doivent être dans backend/data/raw/
- L'index vectoriel se reconstruit automatiquement

## 🎯 Prochaines Étapes Recommandées

1. **Docker** - Conteneurisation des deux services
2. **Auth** - Système d'authentification utilisateur  
3. **BDD** - Base de données persistante (PostgreSQL)
4. **Cache** - Redis pour les sessions
5. **Monitoring** - Logs et métriques centralisés
6. **CI/CD** - Pipeline de déploiement automatisé

---

✅ **La séparation est complète et fonctionnelle !** 

Les deux applications peuvent maintenant évoluer indépendamment tout en préservant toutes les fonctionnalités d'OrientaBot.