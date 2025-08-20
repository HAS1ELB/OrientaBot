# OrientaBot - Conseiller d'orientation Maroc 🎓

Application Streamlit pour conseiller les lycéens marocains dans leurs choix d'orientation post-bac.

## Structure du projet

```
orientabot/
│
├── app.py                 # Application principale
├── config.py             # Configuration et variables d'environnement
├── components.py         # Composants UI
├── styles.py            # Styles CSS et HTML
├── prompts.py           # Prompts système et templates
├── chat_handler.py      # Gestion des interactions chat
├── session_manager.py   # Gestion de l'état de session
├── requirements.txt     # Dépendances Python
├── .env                # Variables d'environnement (à créer)
└── README.md           # Ce fichier
```

## Installation

1. Cloner le projet
2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
3. Créer un fichier `.env` avec votre clé API Groq :
   ```
   GROQ_API_KEY=your_groq_api_key_hereGROQ_MODEL=llama3-70b-8192
   ```
4. Lancer l'application :
   ```bash
   streamlit run app.py
   ```

## Architecture

### Fichiers principaux

* **app.py** : Point d'entrée principal de l'application
* **config.py** : Centralise toute la configuration
* **components.py** : Contient tous les composants UI réutilisables
* **styles.py** : Gère les styles CSS et le HTML statique
* **prompts.py** : Centralise tous les prompts et templates
* **chat_handler.py** : Gère l'API Groq et le streaming
* **session_manager.py** : Gère l'état de session Streamlit

### Avantages de cette structure

1. **Séparation des responsabilités** : Chaque fichier a un rôle spécifique
2. **Réutilisabilité** : Les composants peuvent être réutilisés
3. **Maintenabilité** : Plus facile de modifier et déboguer
4. **Évolutivité** : Facile d'ajouter de nouvelles fonctionnalités
5. **Testabilité** : Chaque module peut être testé indépendamment

## Fonctionnalités

* Interface chat intuitive
* Streaming des réponses en temps réel
* Gestion de l'historique de conversation
* Paramètres configurables (température)
* Design responsive avec CSS personnalisé
* Conseils d'orientation spécialisés pour le système éducatif marocain

## Configuration

Modifiez `config.py` pour ajuster :

* Les paramètres de l'API Groq
* Les configurations de l'application
* Les valeurs par défaut

## Personnalisation

* **Styles** : Modifiez `styles.py` pour changer l'apparence
* **Prompts** : Ajustez `prompts.py` pour modifier le comportement de l'IA
* **UI** : Modifiez `components.py` pour changer la structure de l'interface
