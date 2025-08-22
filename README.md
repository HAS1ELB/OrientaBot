# OrientaBot - Conseiller d'orientation Maroc

## 📁 Structure du projet

```
OrientaBot/
├── src/                          # Code source principal
│   ├── main.py                   # Point d'entrée de l'application
│   ├── core/                     # Configuration et gestion de session
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration de l'application
│   │   └── session_manager.py   # Gestion des sessions Streamlit
│   ├── ui/                       # Interface utilisateur
│   │   ├── __init__.py
│   │   ├── components.py        # Composants UI Streamlit
│   │   └── styles.py           # Styles CSS personnalisés
│   ├── chat/                     # Gestion des conversations
│   │   ├── __init__.py
│   │   ├── handler.py          # Gestionnaire de chat et API Groq
│   │   └── prompts.py          # Prompts système et conversation
│   ├── rag/                      # Système RAG (Retrieval Augmented Generation)
│   │   ├── __init__.py
│   │   ├── manager.py          # Gestionnaire principal RAG
│   │   ├── vector_store.py     # Base vectorielle FAISS
│   │   └── pdf_processor.py    # Traitement des documents PDF
│   └── utils/                    # Utilitaires
│       ├── __init__.py
│       └── combine_pdfs.py     # Combinaison de PDFs
├── data/                         # Données
│   ├── raw/                     # PDFs sources des écoles
│   │   ├── Ecole-Nationale-des-Sciences-Appliquees-El-Jadida.pdf
│   │   ├── EMSI-CASA.pdf
│   │   └── ISPITS.pdf
│   └── processed/               # Données traitées
│       ├── ecoles_maroc_combined.pdf
│       ├── chunks.pkl          # Chunks de texte vectorisés
│       ├── faiss_index.bin     # Index FAISS
│       └── metadata.json       # Métadonnées des documents
├── run.py                       # Script de lancement
├── requirements.txt             # Dépendances Python
└── README.md                    # Documentation

```

## 🚀 Installation et lancement

### 1. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 2. Configuration

Créez un fichier `.env` avec votre clé API Groq :

```env
GROQ_API_KEY=votre_cle_groq_ici
GROQ_MODEL=llama3-70b-8192
```

### 3. Lancement de l'application

```bash
# Méthode recommandée avec le script de lancement
python run.py

# Ou avec streamlit directement
streamlit run run.py

# Ou en spécifiant le PYTHONPATH manuellement
PYTHONPATH=src streamlit run src/main.py
```

## 📋 Modules

### Core
- **config.py** : Configuration centralisée de l'application
- **session_manager.py** : Gestion des sessions et état de l'application

### UI
- **components.py** : Composants d'interface utilisateur réutilisables
- **styles.py** : Styles CSS personnalisés pour Streamlit

### Chat
- **handler.py** : Gestionnaire des conversations avec l'API Groq
- **prompts.py** : Prompts système et démarreurs de conversation

### RAG
- **manager.py** : Orchestrateur du système RAG
- **vector_store.py** : Gestion de la base vectorielle avec FAISS
- **pdf_processor.py** : Traitement et extraction de texte des PDFs

### Utils
- **combine_pdfs.py** : Utilitaire pour combiner plusieurs PDFs

## 🔧 Développement

### Ajout de nouveaux PDFs d'écoles

1. Placez les PDFs dans `data/raw/`
2. Relancez l'application pour réindexer automatiquement

### Modification des prompts

Éditez `src/chat/prompts.py` pour personnaliser les prompts système.

### Personnalisation de l'interface

Modifiez `src/ui/components.py` et `src/ui/styles.py` pour personnaliser l'apparence.

## 📦 Structure modulaire

Cette nouvelle organisation offre :

- **Séparation claire des responsabilités** : Chaque module a un rôle spécifique
- **Imports explicites** : Facilite la maintenance et la compréhension
- **Extensibilité** : Facile d'ajouter de nouveaux modules
- **Tests** : Structure adaptée pour les tests unitaires
- **Documentation** : Code mieux organisé et documenté

## 🔄 Migration depuis l'ancienne structure

L'ancienne structure à plat a été réorganisée comme suit :

```
app.py → src/main.py
config.py → src/core/config.py
session_manager.py → src/core/session_manager.py
components.py → src/ui/components.py
styles.py → src/ui/styles.py
chat_handler.py → src/chat/handler.py
prompts.py → src/chat/prompts.py
rag_manager.py → src/rag/manager.py
vector_store.py → src/rag/vector_store.py
pdf_processor.py → src/rag/pdf_processor.py
combine_pdfs.py → src/utils/combine_pdfs.py
pdfs/ → data/raw/
data/ → data/processed/
vector_db/ → data/processed/
```

Tous les imports ont été mis à jour automatiquement pour fonctionner avec la nouvelle structure.