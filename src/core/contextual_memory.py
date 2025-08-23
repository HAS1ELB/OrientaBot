"""
Système de mémoire contextuelle pour OrientaBot
Gère le profil utilisateur persistant et l'historique des conversations
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import re
import streamlit as st
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class StudentFiliere(Enum):
    """Filières du baccalauréat marocain"""
    SM_A = "sm-a"                          # Sciences Math A
    SM_B = "sm-b"                          # Sciences Math B
    SCIENCES_PHYSIQUES = "sp"              # Sciences Physiques
    SVT = "svt"                            # Sciences de la Vie et de la Terre
    SCIENCES_TECHNIQUES = "st"             # Sciences et Technologies
    SCIENCES_ECONOMIQUES = "se"            # Sciences Économiques
    LETTRES_SCIENCES_HUMAINES = "lsh"      # Lettres et Sciences Humaines
    ARTS_APPLIQUES = "arts"                # Arts Appliqués
    BAC_PRO = "bac_pro"                    # Bac Professionnel
    AUTRE = "autre"                        # Autre filière

class PersonalityTrait(Enum):
    """Traits de personnalité détectés"""
    ANXIOUS = "anxieux"                    # Tendance à l'anxiété
    CONFIDENT = "confiant"                 # Confiance en soi
    ANALYTICAL = "analytique"              # Approche analytique
    CREATIVE = "creatif"                   # Esprit créatif
    PRACTICAL = "pragmatique"              # Approche pratique
    AMBITIOUS = "ambitieux"                # Grandes ambitions
    CAUTIOUS = "prudent"                   # Approche prudente
    SOCIAL = "social"                      # Orienté relations
    INDEPENDENT = "independant"            # Esprit d'indépendance

@dataclass
class StudentProfile:
    """Profil complet de l'étudiant"""
    # Informations académiques
    filiere: Optional[StudentFiliere] = None
    moyenne_generale: Optional[float] = None
    matieres_fortes: List[str] = field(default_factory=list)
    matieres_faibles: List[str] = field(default_factory=list)
    niveau_francais: str = "bon"           # bon, moyen, faible
    niveau_anglais: str = "moyen"          # bon, moyen, faible
    
    # Informations personnelles
    interets: List[str] = field(default_factory=list)
    valeurs: List[str] = field(default_factory=list)
    traits_personnalite: List[PersonalityTrait] = field(default_factory=list)
    
    # Contexte familial et social
    ville: Optional[str] = None
    region: Optional[str] = None
    situation_familiale: str = "normale"    # normale, monoparentale, difficile
    niveau_socio_economique: str = "moyen"  # aise, moyen, modeste
    soutien_familial: str = "positif"      # positif, neutre, pression, conflit
    
    # Contraintes et préférences
    budget_formation: str = "flexible"      # gratuit_priorite, modeste, flexible, aise
    mobilite_geographique: str = "flexible" # locale_uniquement, regionale, nationale, internationale
    preferences_secteur: List[str] = field(default_factory=list)
    contraintes_specifiques: List[str] = field(default_factory=list)
    
    # Évolution du profil
    confiance_orientation: int = 3          # 1-5, niveau de confiance dans ses choix
    ouverture_changement: int = 3           # 1-5, ouverture aux nouvelles idées
    niveau_information: int = 2             # 1-5, niveau de connaissance du système
    
    # Métadonnées
    creation_date: str = field(default_factory=lambda: datetime.now().isoformat())
    derniere_mise_a_jour: str = field(default_factory=lambda: datetime.now().isoformat())
    nombre_conversations: int = 0

@dataclass
class ConversationTurn:
    """Un échange dans la conversation"""
    timestamp: str
    user_message: str
    assistant_response: str
    detected_intent: Optional[str] = None
    extracted_info: Dict[str, Any] = field(default_factory=dict)
    user_satisfaction: Optional[int] = None  # 1-5 si feedback donné
    
@dataclass
class ConversationSession:
    """Session de conversation complète"""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    turns: List[ConversationTurn] = field(default_factory=list)
    session_topic: Optional[str] = None     # orientation_generale, procedure_specifique, etc.
    progress_made: bool = False             # Est-ce que l'étudiant a progressé?
    next_steps: List[str] = field(default_factory=list)

class InformationExtractor:
    """Extracteur d'informations depuis les messages utilisateur"""
    
    def __init__(self):
        self.extraction_patterns = self._initialize_extraction_patterns()
        self.value_patterns = self._initialize_value_patterns()
    
    def _initialize_extraction_patterns(self) -> Dict[str, List[str]]:
        """Patterns pour extraire des informations spécifiques"""
        return {
            'filiere': [
                r'(?:je suis|filière|bac)\s+(?:en\s+)?([a-zA-Z\-]+)',
                r'(?:sciences?\s+math|sm)[\-\s]*([ab]?)',
                r'(?:sciences?\s+physiques?|sp)',
                r'(?:svt|sciences?\s+vie)',
                r'(?:sciences?\s+(?:et\s+)?techniques?|st)',
                r'(?:sciences?\s+économiques?|se)',
                r'(?:lettres?|lsh|sciences?\s+humaines?)',
                r'(?:arts?\s+appliqués?)',
            ],
            
            'moyenne': [
                r'(?:moyenne|note|résultat).*?(\d{1,2}(?:[.,]\d{1,2})?)',
                r'(\d{1,2}(?:[.,]\d{1,2})?)\s*(?:/20|sur 20)',
                r'j\'ai\s+(\d{1,2}(?:[.,]\d{1,2})?)',
            ],
            
            'ville': [
                r'(?:je vis|j\'habite|je suis).*?(?:à|dans|de)\s+([A-Za-zÀ-ÿ\-\s]+)',
                r'(?:ville|région).*?([A-Za-zÀ-ÿ\-\s]+)',
                r'(?:casablanca|rabat|marrakech|fès|tanger|agadir|oujda|kenitra|tétouan|salé|jadida|khouribga)',
            ],
            
            'interets': [
                r'(?:j\'aime|passion|intéresse|plais).*?(informatique|médecine|ingénierie|commerce|art|sport|science)',
                r'(?:domaine|secteur).*?(informatique|médecine|ingénierie|commerce|art|sport|science)',
            ],
            
            'contraintes': [
                r'(?:budget|argent|financier).*?(limité|serré|modeste|problème)',
                r'(?:famille|parents).*?(contre|pression|conflit|impose)',
                r'(?:ne peux pas|impossible).*?(déménager|partir|bouger)',
            ],
            
            'emotions': [
                r'(stress|anxieux|inquiet|peur|angoisse|nerveux)',
                r'(confus|perdu|ne sais pas|hésit|indécis)',
                r'(motivé|confiant|déterminé|sûr)',
                r'(découragé|déçu|triste)',
            ]
        }
    
    def _initialize_value_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Patterns pour détecter les valeurs et traits"""
        return {
            'valeurs': {
                'famille': ['famille', 'parents', 'proches'],
                'argent': ['argent', 'salaire', 'financier', 'riche'],
                'prestige': ['prestige', 'reconnaissance', 'statut'],
                'aide': ['aider', 'utile', 'service', 'social'],
                'creativite': ['créatif', 'création', 'artistique', 'innovation'],
                'stabilite': ['stable', 'sécurité', 'sûr', 'garanti'],
                'aventure': ['aventure', 'voyage', 'découvrir', 'nouveau'],
            },
            
            'traits': {
                PersonalityTrait.ANXIOUS: ['stress', 'inquiet', 'peur', 'angoisse'],
                PersonalityTrait.CONFIDENT: ['confiant', 'sûr', 'déterminé'],
                PersonalityTrait.ANALYTICAL: ['analyser', 'logique', 'réfléchir'],
                PersonalityTrait.CREATIVE: ['créatif', 'imagination', 'artistique'],
                PersonalityTrait.PRACTICAL: ['pratique', 'concret', 'utile'],
                PersonalityTrait.AMBITIOUS: ['ambition', 'réussir', 'excellence'],
                PersonalityTrait.CAUTIOUS: ['prudent', 'réfléchi', 'sécurité'],
                PersonalityTrait.SOCIAL: ['équipe', 'groupe', 'social', 'contact'],
                PersonalityTrait.INDEPENDENT: ['indépendant', 'autonome', 'seul'],
            }
        }
    
    def extract_from_message(self, message: str) -> Dict[str, Any]:
        """
        Extrait les informations depuis un message utilisateur
        
        Args:
            message: Message à analyser
            
        Returns:
            Dictionnaire des informations extraites
        """
        extracted = {}
        message_lower = message.lower()
        
        # Extraction des informations factuelles
        for info_type, patterns in self.extraction_patterns.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, message_lower)
                matches.extend(found)
            
            if matches:
                extracted[info_type] = self._clean_extracted_values(info_type, matches)
        
        # Extraction des valeurs et traits
        extracted['valeurs_detectees'] = self._detect_values(message_lower)
        extracted['traits_detectes'] = self._detect_traits(message_lower)
        
        return extracted
    
    def _clean_extracted_values(self, info_type: str, values: List[str]) -> Any:
        """Nettoie et normalise les valeurs extraites"""
        if info_type == 'moyenne':
            # Convertir en float et prendre la plus récente/pertinente
            float_values = []
            for val in values:
                try:
                    float_val = float(val.replace(',', '.'))
                    if 0 <= float_val <= 20:  # Vérification de plausibilité
                        float_values.append(float_val)
                except ValueError:
                    continue
            return max(float_values) if float_values else None
        
        elif info_type == 'filiere':
            # Normaliser les filières
            for val in values:
                val_clean = val.lower().strip()
                if 'math' in val_clean or 'sm' in val_clean:
                    if 'a' in val_clean:
                        return StudentFiliere.SM_A
                    elif 'b' in val_clean:
                        return StudentFiliere.SM_B
                    else:
                        return StudentFiliere.SM_A  # Par défaut
                elif 'physique' in val_clean or 'sp' in val_clean:
                    return StudentFiliere.SCIENCES_PHYSIQUES
                elif 'svt' in val_clean or 'vie' in val_clean:
                    return StudentFiliere.SVT
                elif 'technique' in val_clean or 'st' in val_clean:
                    return StudentFiliere.SCIENCES_TECHNIQUES
                elif 'économique' in val_clean or 'se' in val_clean:
                    return StudentFiliere.SCIENCES_ECONOMIQUES
                elif 'lettre' in val_clean or 'lsh' in val_clean or 'humaine' in val_clean:
                    return StudentFiliere.LETTRES_SCIENCES_HUMAINES
            return None
        
        elif info_type == 'ville':
            # Nettoyer et capitaliser les noms de ville
            for val in values:
                val_clean = val.strip().title()
                if len(val_clean) > 2:  # Éviter les matches trop courts
                    return val_clean
            return None
        
        else:
            # Pour les autres types, retourner la liste nettoyée
            return [val.strip() for val in values if val.strip()]
    
    def _detect_values(self, message: str) -> List[str]:
        """Détecte les valeurs mentionnées dans le message"""
        detected_values = []
        
        for value, keywords in self.value_patterns['valeurs'].items():
            for keyword in keywords:
                if keyword in message:
                    detected_values.append(value)
                    break
        
        return detected_values
    
    def _detect_traits(self, message: str) -> List[PersonalityTrait]:
        """Détecte les traits de personnalité dans le message"""
        detected_traits = []
        
        for trait, keywords in self.value_patterns['traits'].items():
            for keyword in keywords:
                if keyword in message:
                    detected_traits.append(trait)
                    break
        
        return detected_traits

class ContextualMemorySystem:
    """Système de mémoire contextuelle principal"""
    
    def __init__(self, storage_path: str = "data/user_profiles"):
        """
        Initialise le système de mémoire contextuelle
        
        Args:
            storage_path: Chemin de stockage des profils utilisateur
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.extractor = InformationExtractor()
        self.current_profile: Optional[StudentProfile] = None
        self.current_session: Optional[ConversationSession] = None
        
        # Cache pour les sessions récentes
        self.session_cache = {}
        self.max_cache_size = 50
        
        logger.info(f"Système de mémoire contextuelle initialisé: {self.storage_path}")
    
    def get_user_id(self) -> str:
        """Obtient l'ID utilisateur depuis la session Streamlit"""
        # Utiliser l'ID de session Streamlit ou en créer un
        if 'user_id' not in st.session_state:
            from uuid import uuid4
            st.session_state.user_id = str(uuid4())
        
        return st.session_state.user_id
    
    def load_user_profile(self, user_id: Optional[str] = None) -> StudentProfile:
        """
        Charge le profil utilisateur depuis le stockage
        
        Args:
            user_id: ID de l'utilisateur (optionnel, utilise session si None)
            
        Returns:
            Profil utilisateur chargé ou nouveau
        """
        if user_id is None:
            user_id = self.get_user_id()
        
        profile_path = self.storage_path / f"profile_{user_id}.json"
        
        if profile_path.exists():
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                
                # Convertir back les enums
                if profile_data.get('filiere'):
                    try:
                        profile_data['filiere'] = StudentFiliere(profile_data['filiere'])
                    except ValueError:
                        profile_data['filiere'] = None
                
                if profile_data.get('traits_personnalite'):
                    traits = []
                    for trait_value in profile_data['traits_personnalite']:
                        try:
                            traits.append(PersonalityTrait(trait_value))
                        except ValueError:
                            continue
                    profile_data['traits_personnalite'] = traits
                
                self.current_profile = StudentProfile(**profile_data)
                logger.info(f"Profil utilisateur chargé pour {user_id}")
                
            except Exception as e:
                logger.warning(f"Erreur lors du chargement du profil {user_id}: {e}")
                self.current_profile = StudentProfile()
        else:
            self.current_profile = StudentProfile()
            logger.info(f"Nouveau profil utilisateur créé pour {user_id}")
        
        return self.current_profile
    
    def save_user_profile(self, user_id: Optional[str] = None) -> None:
        """
        Sauvegarde le profil utilisateur
        
        Args:
            user_id: ID de l'utilisateur (optionnel)
        """
        if user_id is None:
            user_id = self.get_user_id()
        
        if self.current_profile is None:
            return
        
        profile_path = self.storage_path / f"profile_{user_id}.json"
        
        try:
            # Préparer les données pour JSON
            profile_data = asdict(self.current_profile)
            
            # Convertir les enums en strings
            if profile_data.get('filiere'):
                profile_data['filiere'] = profile_data['filiere'].value
            
            if profile_data.get('traits_personnalite'):
                profile_data['traits_personnalite'] = [t.value for t in self.current_profile.traits_personnalite]
            
            # Mettre à jour la timestamp
            profile_data['derniere_mise_a_jour'] = datetime.now().isoformat()
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Profil utilisateur sauvegardé pour {user_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du profil {user_id}: {e}")
    
    def start_conversation_session(self, topic: Optional[str] = None) -> str:
        """
        Démarre une nouvelle session de conversation
        
        Args:
            topic: Sujet de la session (optionnel)
            
        Returns:
            ID de la session créée
        """
        from uuid import uuid4
        session_id = str(uuid4())
        
        self.current_session = ConversationSession(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            session_topic=topic
        )
        
        # Ajouter au cache
        self.session_cache[session_id] = self.current_session
        
        logger.info(f"Session de conversation démarrée: {session_id}")
        
        return session_id
    
    def add_conversation_turn(self, 
                             user_message: str, 
                             assistant_response: str,
                             detected_intent: Optional[str] = None) -> None:
        """
        Ajoute un échange à la session courante
        
        Args:
            user_message: Message de l'utilisateur
            assistant_response: Réponse de l'assistant
            detected_intent: Intention détectée (optionnel)
        """
        if self.current_session is None:
            self.start_conversation_session()
        
        # Extraire les informations du message utilisateur
        extracted_info = self.extractor.extract_from_message(user_message)
        
        # Créer le turn
        turn = ConversationTurn(
            timestamp=datetime.now().isoformat(),
            user_message=user_message,
            assistant_response=assistant_response,
            detected_intent=detected_intent,
            extracted_info=extracted_info
        )
        
        self.current_session.turns.append(turn)
        
        # Mettre à jour le profil avec les nouvelles informations
        self.update_profile_from_turn(turn)
        
        logger.info(f"Turn ajouté à la session {self.current_session.session_id}")
    
    def update_profile_from_turn(self, turn: ConversationTurn) -> None:
        """
        Met à jour le profil utilisateur avec les informations d'un turn
        
        Args:
            turn: Tour de conversation à analyser
        """
        if self.current_profile is None:
            self.current_profile = StudentProfile()
        
        extracted = turn.extracted_info
        
        # Mettre à jour les informations factuelles
        if extracted.get('filiere') and self.current_profile.filiere is None:
            self.current_profile.filiere = extracted['filiere']
        
        if extracted.get('moyenne') and self.current_profile.moyenne_generale is None:
            self.current_profile.moyenne_generale = extracted['moyenne']
        
        if extracted.get('ville') and self.current_profile.ville is None:
            self.current_profile.ville = extracted['ville']
        
        # Ajouter les intérêts (sans doublons)
        if extracted.get('interets'):
            for interet in extracted['interets']:
                if interet not in self.current_profile.interets:
                    self.current_profile.interets.append(interet)
        
        # Ajouter les valeurs détectées
        if extracted.get('valeurs_detectees'):
            for valeur in extracted['valeurs_detectees']:
                if valeur not in self.current_profile.valeurs:
                    self.current_profile.valeurs.append(valeur)
        
        # Ajouter les traits de personnalité
        if extracted.get('traits_detectes'):
            for trait in extracted['traits_detectes']:
                if trait not in self.current_profile.traits_personnalite:
                    self.current_profile.traits_personnalite.append(trait)
        
        # Incrémenter le compteur de conversations
        self.current_profile.nombre_conversations += 1
        
        # Sauvegarder le profil mis à jour
        self.save_user_profile()
    
    def get_contextual_info_for_prompt(self) -> Dict[str, Any]:
        """
        Génère les informations contextuelles pour enrichir le prompt
        
        Returns:
            Dictionnaire des informations contextuelles
        """
        if self.current_profile is None:
            self.load_user_profile()
        
        context = {
            'profile_available': self.current_profile is not None,
            'conversation_history': len(self.current_session.turns) if self.current_session else 0
        }
        
        if self.current_profile:
            context.update({
                'academic_info': {
                    'filiere': self.current_profile.filiere.value if self.current_profile.filiere else None,
                    'moyenne': self.current_profile.moyenne_generale,
                    'matieres_fortes': self.current_profile.matieres_fortes,
                    'niveau_information': self.current_profile.niveau_information
                },
                'personal_info': {
                    'ville': self.current_profile.ville,
                    'interets': self.current_profile.interets,
                    'valeurs': self.current_profile.valeurs,
                    'traits_personnalite': [t.value for t in self.current_profile.traits_personnalite]
                },
                'context_info': {
                    'soutien_familial': self.current_profile.soutien_familial,
                    'budget_formation': self.current_profile.budget_formation,
                    'mobilite_geographique': self.current_profile.mobilite_geographique,
                    'confiance_orientation': self.current_profile.confiance_orientation,
                    'nombre_conversations': self.current_profile.nombre_conversations
                }
            })
        
        return context
    
    def generate_contextual_prompt_addition(self) -> str:
        """
        Génère l'addition au prompt système basée sur le contexte
        
        Returns:
            Addition au prompt système
        """
        context = self.get_contextual_info_for_prompt()
        
        if not context['profile_available']:
            return ""
        
        prompt_addition = "\n\n# CONTEXTE UTILISATEUR PERSONNALISÉ\n"
        
        # Informations académiques
        academic = context.get('academic_info', {})
        if academic.get('filiere'):
            prompt_addition += f"**Filière actuelle:** {academic['filiere']}\n"
        if academic.get('moyenne'):
            prompt_addition += f"**Moyenne générale:** {academic['moyenne']}/20\n"
        if academic.get('matieres_fortes'):
            prompt_addition += f"**Matières fortes:** {', '.join(academic['matieres_fortes'])}\n"
        
        # Informations personnelles
        personal = context.get('personal_info', {})
        if personal.get('ville'):
            prompt_addition += f"**Ville:** {personal['ville']}\n"
        if personal.get('interets'):
            prompt_addition += f"**Centres d'intérêt:** {', '.join(personal['interets'])}\n"
        if personal.get('valeurs'):
            prompt_addition += f"**Valeurs importantes:** {', '.join(personal['valeurs'])}\n"
        if personal.get('traits_personnalite'):
            prompt_addition += f"**Traits détectés:** {', '.join(personal['traits_personnalite'])}\n"
        
        # Contexte situationnel
        context_info = context.get('context_info', {})
        adaptations = []
        
        if context_info.get('soutien_familial') in ['pression', 'conflit']:
            adaptations.append("⚠️ **CONFLIT FAMILIAL DÉTECTÉ** - Privilégier la médiation et les solutions équilibrées")
        
        if context_info.get('budget_formation') in ['gratuit_priorite', 'modeste']:
            adaptations.append("💰 **CONTRAINTE BUDGÉTAIRE** - Mettre l'accent sur les formations gratuites/accessibles")
        
        if context_info.get('confiance_orientation', 3) <= 2:
            adaptations.append("🤗 **MANQUE DE CONFIANCE** - Renforcer la confiance et rassurer")
        
        if context_info.get('nombre_conversations', 0) > 5:
            adaptations.append("🎯 **UTILISATEUR RÉCURRENT** - Adapter le niveau de détail et éviter les répétitions")
        
        if adaptations:
            prompt_addition += "\n**ADAPTATIONS REQUISES:**\n"
            for adaptation in adaptations:
                prompt_addition += f"- {adaptation}\n"
        
        # Historique de conversation
        if context['conversation_history'] > 0:
            prompt_addition += f"\n**Conversation en cours:** {context['conversation_history']} échange(s) précédent(s)\n"
        
        prompt_addition += "\n**INSTRUCTIONS:** Utilise ces informations pour personnaliser tes réponses et éviter de redemander des informations déjà connues.\n"
        
        return prompt_addition
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du système de mémoire"""
        return {
            'profile_loaded': self.current_profile is not None,
            'session_active': self.current_session is not None,
            'turns_in_session': len(self.current_session.turns) if self.current_session else 0,
            'cache_size': len(self.session_cache),
            'user_id': self.get_user_id() if hasattr(st, 'session_state') else 'unknown'
        }
    
    def clear_user_data(self, user_id: Optional[str] = None) -> None:
        """
        Supprime toutes les données utilisateur (RGPD compliance)
        
        Args:
            user_id: ID de l'utilisateur à supprimer (optionnel)
        """
        if user_id is None:
            user_id = self.get_user_id()
        
        # Supprimer le profil
        profile_path = self.storage_path / f"profile_{user_id}.json"
        if profile_path.exists():
            profile_path.unlink()
        
        # Nettoyer le cache
        sessions_to_remove = [sid for sid, session in self.session_cache.items() 
                             if sid.startswith(user_id)]
        for sid in sessions_to_remove:
            del self.session_cache[sid]
        
        # Réinitialiser les variables courantes
        self.current_profile = None
        self.current_session = None
        
        logger.info(f"Données utilisateur supprimées pour {user_id}")

# Fonctions utilitaires pour l'intégration
def get_contextual_memory_system() -> ContextualMemorySystem:
    """
    Obtient l'instance du système de mémoire contextuelle (singleton)
    
    Returns:
        Instance du système de mémoire
    """
    if 'contextual_memory' not in st.session_state:
        st.session_state.contextual_memory = ContextualMemorySystem()
    
    return st.session_state.contextual_memory

def get_user_context_for_prompt() -> str:
    """
    Fonction utilitaire pour obtenir le contexte utilisateur pour le prompt
    
    Returns:
        Addition au prompt système avec contexte utilisateur
    """
    memory_system = get_contextual_memory_system()
    return memory_system.generate_contextual_prompt_addition()