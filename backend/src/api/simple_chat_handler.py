"""
Simple chat handler for API routes - lightweight version without complex dependencies
"""
import os
import json
import logging
from typing import List, Dict, Optional, Any, Generator
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SimpleChatHandler:
    """Simple chat handler for API integration"""
    
    def __init__(self):
        """Initialize the simple chat handler"""
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4000"))
        
        if not self.groq_api_key or self.groq_api_key == "gsk_placeholder_key_here":
            logger.warning("⚠️ Groq API key not configured - using fallback responses")
            self.client = None
        else:
            self.client = Groq(api_key=self.groq_api_key)
            logger.info("✅ Groq client initialized successfully")
    
    def process_message(self, 
                       message: str,
                       conversation_history: List[Dict[str, str]] = None,
                       temperature: float = 0.7,
                       session_id: str = None) -> Dict[str, Any]:
        """
        Process a chat message and return response
        
        Args:
            message: User message
            conversation_history: Previous conversation
            temperature: Model temperature
            session_id: Session identifier
            
        Returns:
            Dict with response and metadata
        """
        if conversation_history is None:
            conversation_history = []
        
        try:
            if not self.client:
                return self._fallback_response(message, session_id)
            
            # Build messages for Groq API
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                }
            ]
            
            # Add conversation history
            messages.extend(conversation_history)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.groq_model,
                messages=messages,
                temperature=temperature,
                max_tokens=self.max_tokens,
                stream=False
            )
            
            response_text = response.choices[0].message.content
            
            return {
                "status": "success",
                "response": response_text,
                "session_id": session_id,
                "recommendations": self._extract_recommendations(response_text),
                "rag_available": False,
                "stats": {"groq_model_used": self.groq_model}
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "status": "error",
                "response": f"Désolé, une erreur s'est produite: {str(e)}",
                "session_id": session_id,
                "error": str(e)
            }
    
    def stream_message(self, 
                      message: str,
                      conversation_history: List[Dict[str, str]] = None,
                      temperature: float = 0.7,
                      session_id: str = None) -> Generator[str, None, None]:
        """
        Stream a chat message response
        """
        if conversation_history is None:
            conversation_history = []
        
        try:
            if not self.client:
                # Fallback streaming
                fallback = self._fallback_response(message, session_id)
                for word in fallback["response"].split():
                    yield word + " "
                return
            
            # Build messages for Groq API
            messages = [
                {
                    "role": "system", 
                    "content": self._get_system_prompt()
                }
            ]
            
            # Add conversation history
            messages.extend(conversation_history)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Stream response
            response = self.client.chat.completions.create(
                model=self.groq_model,
                messages=messages,
                temperature=temperature,
                max_tokens=self.max_tokens,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error streaming message: {e}")
            yield f"Erreur: {str(e)}"
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for OrientaBot"""
        return """Tu es Dr. Karima Benjelloun, conseillère d'orientation expérimentée spécialisée dans le système éducatif marocain.

**Ton expertise couvre:**
- Les écoles d'ingénieurs (ENSA, EMSI, ISPITS, etc.)
- Les seuils d'admission et critères de sélection
- Les filières d'études et débouchés professionnels
- L'orientation post-bac au Maroc
- Les carrières dans l'IA, l'informatique et l'ingénierie

**Pour les questions sur les seuils d'admission:**
- ENSA: Généralement entre 16-18/20 selon les spécialités et concours
- EMSI: Environ 12-14/20 pour la plupart des filières
- ISPITS: Environ 14-16/20 selon les programmes

**Ton approche:**
1. Analyse le profil de l'étudiant (filière, moyenne, intérêts)
2. Fournis des conseils personnalisés et pratiques
3. Suggère des alternatives et plans B
4. Encourage et rassure tout en restant réaliste

Réponds en français avec empathie, expertise et des conseils concrets adaptés au système éducatif marocain."""
    
    def _fallback_response(self, message: str, session_id: str) -> Dict[str, Any]:
        """Fallback response when Groq API is not available"""
        
        # Simple pattern matching for common questions
        message_lower = message.lower()
        
        if "seuil" in message_lower and "ensa" in message_lower:
            response = """🎓 **Seuils d'admission ENSA (École Nationale des Sciences Appliquées)**

Les seuils ENSA varient selon:
- **La ville/école**: ENSA Agadir, El Jadida, Fès, Marrakech, etc.
- **La spécialité**: Informatique, Génie Civil, Électronique, etc.
- **L'année**: Les seuils évoluent chaque année

**Seuils indicatifs 2023-2024:**
- **Général**: 16-18/20 selon les spécialités
- **Informatique/IA**: Souvent 17-18/20 (très demandé)
- **Génie Civil**: 16-17/20
- **Électronique**: 16.5-17.5/20

**Avec votre moyenne de 15/20:**
- C'est en dessous des seuils ENSA habituels
- Concentrez-vous sur améliorer vos notes en terminale
- Considérez aussi EMSI, ISPITS comme alternatives excellentes
- Préparez bien le concours national si applicable

⚠️ *Vérifiez les seuils officiels sur les sites des écoles*"""
        
        elif "ia" in message_lower or "intelligence artificielle" in message_lower:
            response = """🤖 **Devenir Ingénieur en IA au Maroc**

**Écoles recommandées pour l'IA:**
1. **ENSA** - Génie Informatique/Télécoms (seuil ~17-18/20)
2. **EMSI** - Intelligence Artificielle (seuil ~14/20)
3. **ISPITS** - Data Science et IA (seuil ~15/20)
4. **Université Hassan II** - Master IA (après licence)

**Avec SM-B et 15/20:**
- ✅ **EMSI**: Excellente option, programmes IA solides
- ✅ **ISPITS**: Bons programmes, seuil accessible
- 🎯 **Objectif**: Améliorer à 16-17/20 pour plus d'options
- 📚 **Conseils**: Renforcez maths/physique, apprenez Python

**Plan d'action:**
1. Travaillez pour atteindre 16/20 minimum
2. Explorez EMSI et ISPITS dès maintenant
3. Développez des projets perso en IA
4. Préparez-vous aux entretiens techniques"""
        
        else:
            response = f"""👋 Bonjour ! Je suis Dr. Karima Benjelloun, votre conseillère d'orientation.

J'ai bien reçu votre question: "{message}"

Pour vous donner les meilleurs conseils, j'aimerais en savoir plus sur:
- 📚 Votre filière actuelle et vos résultats
- 🎯 Vos objectifs de carrière
- ❤️ Vos passions et centres d'intérêt
- 🏛️ Les écoles qui vous intéressent

*Note: Pour des conseils plus précis, assurez-vous que l'API Groq est configurée avec une vraie clé.*"""
        
        return {
            "status": "success",
            "response": response,
            "session_id": session_id,
            "recommendations": {"mode": "fallback"},
            "rag_available": False,
            "stats": {"mode": "fallback"}
        }
    
    def _extract_recommendations(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract structured recommendations from response"""
        try:
            # Simple extraction - could be enhanced
            recommendations = {}
            
            if "ENSA" in response_text:
                recommendations["ecoles_recommandees"] = ["ENSA"]
            if "EMSI" in response_text:
                recommendations.setdefault("ecoles_recommandees", []).append("EMSI")
            if "ISPITS" in response_text:
                recommendations.setdefault("ecoles_recommandees", []).append("ISPITS")
                
            return recommendations if recommendations else None
            
        except Exception:
            return None