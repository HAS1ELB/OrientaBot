# OrientaBot (Maroc) – Chatbot d'orientation académique (LLaMA 3 via Groq + Streamlit)

OrientaBot est un chatbot d’orientation académique pour les lycéens marocains préparant le baccalauréat.
Il utilise des techniques de prompt engineering (non-RAG) pour fournir des recommandations personnalisées.

## Fonctionnalités

- Chat en streaming (Groq + LLaMA 3)
- Persona marocain spécialisé en orientation
- Profil élève (filière, notes, préférences, ville, budget…)
- Suggestions: Match forts, Ambitieux, Sécuritaires
- Plan d’action et conseils personnalisés
- UI Streamlit

## Prérequis

- Python 3.10+
- Compte et clé API Groq: https://console.groq.com/
- Modèles LLaMA 3 disponibles: "llama3-8b-8192" ou "llama3-70b-8192"

## Installation

```bash
git clone https://github.com/votre-compte/academic-orient-bot.git
cd academic-orient-bot
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate sous Windows
pip install -r requirements.txt
cp .env.example .env
# Éditez .env et ajoutez votre GROQ_API_KEY
```
