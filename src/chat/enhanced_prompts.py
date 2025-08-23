"""
Prompts système enrichis avec personas spécialisés et templates de réponses
Amélioration majeure du système de prompts d'OrientaBot
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import re
from datetime import datetime

class StudentProfile(Enum):
    """Types de profils étudiants détectés"""
    SCIENTIFIC = "scientifique"           # Sciences Math, Sciences Physiques, SVT
    TECHNICAL = "technique"               # Sciences & Technologies, BAC Pro
    LITERARY = "litteraire"               # Lettres & Sciences Humaines, Arts
    ECONOMIC = "economique"              # Sciences Économiques, Gestion
    HIGH_ACHIEVER = "excellent"          # Notes > 16/20
    STRUGGLING = "difficulte"            # Notes < 12/20
    UNCERTAIN = "indecis"                # Ne sait pas quoi choisir
    ANXIOUS = "anxieux"                  # Stress, peur, inquiétude
    PRESSURED = "pression"               # Conflit familial, pression externe

class QuestionType(Enum):
    """Classification des types de questions"""
    ORIENTATION_GENERALE = "orientation_generale"      # Que faire après le bac?
    PROCEDURES = "procedures"                          # Comment s'inscrire?
    SEUILS_ADMISSION = "seuils"                       # Quels sont les seuils?
    DEBOUCHES = "debouches"                           # Que faire après cette école?
    COMPARAISON = "comparaison"                       # ENSA vs EMSI?
    REORIENTATION = "reorientation"                   # Changer de filière
    FINANCEMENT = "financement"                       # Bourses, coûts
    LOGEMENT = "logement"                            # Où habiter?
    VIE_ETUDIANTE = "vie_etudiante"                  # Vie sur le campus

class EnhancedPromptSystem:
    """Système de prompts enrichis avec personas et templates"""
    
    def __init__(self):
        self.current_academic_year = "2024-2025"
        self.current_period = self._get_current_period()
    
    def _get_current_period(self) -> str:
        """Déterminer la période académique actuelle"""
        month = datetime.now().month
        if month in [9, 10, 11, 12]:
            return "debut_annee"  # Début d'année scolaire
        elif month in [1, 2, 3]:
            return "orientation"  # Période d'orientation
        elif month in [4, 5]:
            return "examens"      # Période d'examens
        else:
            return "vacances"     # Période de vacances
    
    def detect_student_profile(self, user_input: str, chat_history: List[Dict]) -> List[StudentProfile]:
        """
        Détection intelligente du profil étudiant
        
        Args:
            user_input: Message actuel de l'utilisateur
            chat_history: Historique de la conversation
            
        Returns:
            Liste des profils détectés (peut être multiple)
        """
        profiles = []
        text = user_input.lower()
        
        # Analyser l'historique pour plus de contexte
        full_context = user_input
        for msg in chat_history[-3:]:  # Derniers 3 messages
            if msg.get('role') == 'user':
                full_context += " " + msg.get('content', '')
        
        full_text = full_context.lower()
        
        # Détection des filières
        scientific_keywords = ['sciences math', 'sm-a', 'sm-b', 'sciences physiques', 'sp', 'svt', 'mathématiques', 'physique', 'chimie']
        technical_keywords = ['sciences techniques', 'st', 'bac pro', 'technique', 'technologie']
        literary_keywords = ['lettres', 'lsh', 'sciences humaines', 'littérature', 'philosophie', 'histoire']
        economic_keywords = ['sciences économiques', 'se', 'économie', 'gestion', 'commerce']
        
        if any(keyword in full_text for keyword in scientific_keywords):
            profiles.append(StudentProfile.SCIENTIFIC)
        if any(keyword in full_text for keyword in technical_keywords):
            profiles.append(StudentProfile.TECHNICAL)
        if any(keyword in full_text for keyword in literary_keywords):
            profiles.append(StudentProfile.LITERARY)
        if any(keyword in full_text for keyword in economic_keywords):
            profiles.append(StudentProfile.ECONOMIC)
        
        # Détection des niveaux de performance
        high_grades = re.findall(r'(?:moyenne|note|résultat).{0,10}(?:1[6-9]|20|excellent|très bien)', full_text)
        low_grades = re.findall(r'(?:moyenne|note|résultat).{0,10}(?:1[0-2]|difficile|faible)', full_text)
        
        if high_grades:
            profiles.append(StudentProfile.HIGH_ACHIEVER)
        elif low_grades:
            profiles.append(StudentProfile.STRUGGLING)
        
        # Détection des états émotionnels
        anxiety_keywords = ['stress', 'anxieux', 'peur', 'inquiet', 'angoisse', 'nerveux']
        uncertainty_keywords = ['ne sais pas', 'hésit', 'confus', 'perdu', 'indécis']
        pressure_keywords = ['parents', 'famille', 'conflit', 'pression', 'imposé', 'obligé']
        
        if any(keyword in full_text for keyword in anxiety_keywords):
            profiles.append(StudentProfile.ANXIOUS)
        if any(keyword in full_text for keyword in uncertainty_keywords):
            profiles.append(StudentProfile.UNCERTAIN)
        if any(keyword in full_text for keyword in pressure_keywords):
            profiles.append(StudentProfile.PRESSURED)
        
        return profiles if profiles else [StudentProfile.SCIENTIFIC]  # Par défaut
    
    def classify_question_type(self, user_input: str) -> QuestionType:
        """
        Classification intelligente du type de question
        
        Args:
            user_input: Question de l'utilisateur
            
        Returns:
            Type de question classifié
        """
        text = user_input.lower()
        
        # Patterns pour chaque type
        patterns = {
            QuestionType.PROCEDURES: [
                r'comment.*(?:inscrire|candidater|postuler)',
                r'(?:procédure|démarche|étape).*inscription',
                r'quand.*(?:inscrire|candidater)',
                r'dossier.*(?:inscription|candidature)'
            ],
            QuestionType.SEUILS_ADMISSION: [
                r'(?:seuil|note|moyenne).*(?:admission|accès|entrer)',
                r'combien.*(?:faut|besoin|minimum)',
                r'chance.*(?:avoir|accepté|admis)',
                r'avec.*(?:note|moyenne|résultat)'
            ],
            QuestionType.DEBOUCHES: [
                r'après.*(?:école|formation|diplôme)',
                r'(?:débouché|métier|emploi|carrière)',
                r'que.*faire.*après',
                r'(?:travail|job|profession).*possible'
            ],
            QuestionType.COMPARAISON: [
                r'(?:différence|comparer|choisir).*entre',
                r'(?:mieux|meilleur).*(?:ensa|emsi|est)',
                r'vs|versus|ou bien',
                r'lequel.*(?:choisir|mieux)'
            ],
            QuestionType.REORIENTATION: [
                r'changer.*(?:filière|orientation)',
                r're-?orientation',
                r'autre.*(?:choix|option)',
                r'mal.*choisi'
            ],
            QuestionType.FINANCEMENT: [
                r'(?:coût|prix|tarif|frais)',
                r'(?:bourse|aide|financement)',
                r'combien.*coûte',
                r'gratuit.*payant'
            ],
            QuestionType.LOGEMENT: [
                r'(?:logement|habiter|résidence)',
                r'où.*(?:vivre|loger)',
                r'internat.*externat',
                r'campus.*logé'
            ]
        }
        
        for question_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, text):
                    return question_type
        
        return QuestionType.ORIENTATION_GENERALE
    
    def generate_enhanced_system_prompt(self, 
                                      user_input: str, 
                                      chat_history: List[Dict],
                                      base_prompt: str) -> str:
        """
        Génération du prompt système enrichi
        
        Args:
            user_input: Message actuel
            chat_history: Historique des conversations
            base_prompt: Prompt de base existant
            
        Returns:
            Prompt système enrichi et personnalisé
        """
        # Détection du profil et type de question
        student_profiles = self.detect_student_profile(user_input, chat_history)
        question_type = self.classify_question_type(user_input)
        
        # Construction du prompt enrichi
        enhanced_prompt = self._build_enhanced_prompt(
            base_prompt, 
            student_profiles, 
            question_type,
            user_input,
            chat_history
        )
        
        return enhanced_prompt
    
    def _build_enhanced_prompt(self, 
                              base_prompt: str, 
                              profiles: List[StudentProfile],
                              question_type: QuestionType,
                              user_input: str,
                              chat_history: List[Dict]) -> str:
        """Construction du prompt enrichi final"""
        
        # Persona spécialisé selon le profil
        persona_section = self._get_specialized_persona(profiles)
        
        # Template de réponse selon le type de question
        response_template = self._get_response_template(question_type)
        
        # Contexte temporel
        temporal_context = self._get_temporal_context()
        
        # Instructions spécialisées
        specialized_instructions = self._get_specialized_instructions(profiles, question_type)
        
        # Exemples pertinents
        examples = self._get_relevant_examples(profiles, question_type)
        
        # Assembly final
        enhanced_prompt = f"""{base_prompt}

# PERSONA SPÉCIALISÉ ACTIVÉ
{persona_section}

# CONTEXTE TEMPOREL ({self.current_academic_year})
{temporal_context}

# TEMPLATE DE RÉPONSE - {question_type.value.upper()}
{response_template}

# INSTRUCTIONS SPÉCIALISÉES
{specialized_instructions}

# EXEMPLES DE RÉFÉRENCE
{examples}

## APPROCHE RECOMMANDÉE POUR CETTE CONVERSATION:
- Profil détecté: {', '.join([p.value for p in profiles])}
- Type de question: {question_type.value}
- Période: {self.current_period}

Adapte ton style, ton niveau de détail et tes recommandations à ce profil spécifique.
Utilise le template de réponse fourni pour structurer ta réponse de manière optimale.
"""
        
        return enhanced_prompt
    
    def _get_specialized_persona(self, profiles: List[StudentProfile]) -> str:
        """Génère le persona spécialisé selon les profils détectés"""
        
        personas = {
            StudentProfile.SCIENTIFIC: """
Tu adoptes le rôle de **Dr. Karima Benjelloun, Spécialiste Filières Scientifiques**.
- Tu maîtrises parfaitement les parcours ENSA, EMI, ENSIAS, FST
- Tu connais les spécialisations: Génie Civil, Informatique, Électronique, etc.
- Tu parles avec précision technique mais reste accessible
- Tu mets l'accent sur la logique et les débouchés concrets
            """,
            
            StudentProfile.TECHNICAL: """
Tu adoptes le rôle de **Dr. Karima Benjelloun, Experte Formations Techniques**.
- Tu maîtrises EST, OFPPT, écoles techniques privées
- Tu comprends les parcours professionnalisants
- Tu valorises les compétences pratiques et l'employabilité
- Tu donnes des conseils pragmatiques et concrets
            """,
            
            StudentProfile.LITERARY: """
Tu adoptes le rôle de **Dr. Karima Benjelloun, Conseillère Sciences Humaines**.
- Tu connais les FSJES, écoles de communication, traduction
- Tu valorises la culture générale et les soft skills
- Tu adoptes un style plus nuancé et empathique
- Tu explores les aspects créatifs et humains des métiers
            """,
            
            StudentProfile.HIGH_ACHIEVER: """
Tu adoptes le rôle de **Dr. Karima Benjelloun, Coach Excellence Académique**.
- Tu proposes des défis stimulants et parcours d'élite
- Tu mentionnes les bourses d'excellence et programmes internationaux
- Tu vises haut tout en restant réaliste
- Tu encourages l'ambition mesurée
            """,
            
            StudentProfile.ANXIOUS: """
Tu adoptes le rôle de **Dr. Karima Benjelloun, Coach Bien-être Étudiant**.
- Tu utilises un ton particulièrement rassurant et bienveillant
- Tu décomposes les informations par petites étapes
- Tu normalises les inquiétudes et partages des témoignages
- Tu insistes sur le fait que tout se résout progressivement
            """,
            
            StudentProfile.UNCERTAIN: """
Tu adoptes le rôle de **Dr. Karima Benjelloun, Spécialiste Clarification Vocationnelle**.
- Tu poses des questions ciblées pour révéler les intérêts cachés
- Tu proposes des exercices d'auto-découverte simples
- Tu présentes des profils de métiers variés
- Tu rassures sur le fait qu'hésiter est normal et sain
            """
        }
        
        # Combiner les personas pertinents
        active_personas = []
        for profile in profiles:
            if profile in personas:
                active_personas.append(personas[profile].strip())
        
        if not active_personas:
            return personas[StudentProfile.SCIENTIFIC].strip()
        
        # Si multiple profils, prendre le plus spécifique
        if len(active_personas) == 1:
            return active_personas[0]
        else:
            # Combiner intelligemment
            primary = active_personas[0]
            secondary_traits = " | ".join([p.split('\n')[0].replace("Tu adoptes le rôle de", "Avec expertise en") 
                                         for p in active_personas[1:]])
            return f"{primary}\n\n**Expertises complémentaires:** {secondary_traits}"
    
    def _get_response_template(self, question_type: QuestionType) -> str:
        """Retourne le template de réponse structuré selon le type de question"""
        
        templates = {
            QuestionType.ORIENTATION_GENERALE: """
**STRUCTURE DE RÉPONSE REQUISE:**

🎯 **ANALYSE DE PROFIL** (2-3 phrases)
- Synthèse du profil étudiant détecté

📋 **RECOMMANDATIONS STRATIFIÉES**
- **Choix Prioritaires** (2-3 options principales avec justification)
- **Alternatives Viables** (2-3 options secondaires)  
- **Options de Sécurité** (2-3 choix plus accessibles)

🗺️ **PLAN D'ACTION CONCRET**
- Timeline avec étapes clés
- Démarches immédiates à entreprendre

❓ **QUESTIONS DE CLARIFICATION** (si nécessaire, max 4 questions ciblées)
            """,
            
            QuestionType.PROCEDURES: """
**STRUCTURE DE RÉPONSE REQUISE:**

📅 **TIMELINE DES PROCÉDURES**
- Dates clés et échéances importantes
- Étapes dans l'ordre chronologique

📝 **DÉMARCHES DÉTAILLÉES**
- Documents à préparer
- Plateformes à utiliser (APB, portails écoles)
- Critères d'évaluation

⚠️ **POINTS D'ATTENTION**
- Erreurs fréquentes à éviter
- Conseils pour optimiser le dossier

🔗 **RESSOURCES OFFICIELLES**
- Sites web officiels à consulter
- Contacts utiles
            """,
            
            QuestionType.SEUILS_ADMISSION: """
**STRUCTURE DE RÉPONSE REQUISE:**

📊 **ANALYSE DE COMPATIBILITÉ**
- Évaluation du profil vs exigences typiques
- Facteurs au-delà des notes (motivation, projets, etc.)

🎯 **STRATÉGIE D'ADMISSION**
- Écoles plus/moins sélectives dans le domaine
- Comment renforcer le dossier
- Plan B et alternatives

⚖️ **RÉALISME ET ENCOURAGEMENT**
- Chances objectives basées sur l'expérience
- Témoignages d'étudiants avec profils similaires

⚠️ **AVERTISSEMENT SEUILS**
"Les seuils changent chaque année. Ces estimations sont basées sur les tendances historiques. 
Vérifiez toujours sur les sites officiels des établissements."
            """,
            
            QuestionType.DEBOUCHES: """
**STRUCTURE DE RÉPONSE REQUISE:**

💼 **SECTEURS D'EMPLOI**
- Industries et domaines d'application
- Types d'entreprises qui recrutent

🏢 **MÉTIERS CONCRETS**
- Intitulés de postes précis
- Évolution de carrière typique
- Fourchettes salariales (si pertinent)

📈 **MARCHÉ DE L'EMPLOI**
- Tendances sectorielles au Maroc
- Opportunités à l'international

🎓 **POURSUITE D'ÉTUDES POSSIBLES**
- Masters spécialisés
- Formations complémentaires
            """,
            
            QuestionType.COMPARAISON: """
**STRUCTURE DE RÉPONSE REQUISE:**

⚖️ **TABLEAU COMPARATIF**
- Points forts de chaque option
- Points faibles objectifs
- Différences clés

🎯 **RECOMMANDATION PERSONNALISÉE**
- Meilleur choix selon le profil spécifique
- Justification détaillée

🔄 **CRITÈRES DE DÉCISION**
- Questions à se poser pour choisir
- Facteurs déterminants personnels

📋 **PLAN D'INVESTIGATION**
- Informations supplémentaires à collecter
- Personnes à rencontrer
            """
        }
        
        return templates.get(question_type, templates[QuestionType.ORIENTATION_GENERALE])
    
    def _get_temporal_context(self) -> str:
        """Contexte temporel selon la période académique"""
        
        contexts = {
            "debut_annee": """
**Période: Début d'année scolaire**
- Focus sur l'adaptation et l'évaluation des choix actuels
- Possible réorientation si insatisfaction
- Préparation anticipée pour les candidatures futures
            """,
            
            "orientation": """
**Période: Phase d'orientation active**  
- Candidatures en cours ou à venir
- Urgence des décisions
- Stress naturel et besoin de rassurance
- Focus sur les démarches concrètes
            """,
            
            "examens": """
**Période: Préparation examens**
- Motivation pour la dernière ligne droite
- Projection post-bac comme motivation
- Gestion du stress d'examen
            """,
            
            "vacances": """
**Période: Pause estivale**
- Temps pour réflexion approfondie
- Possible stages de découverte
- Préparation anticipée de l'année suivante
            """
        }
        
        return contexts.get(self.current_period, contexts["orientation"])
    
    def _get_specialized_instructions(self, profiles: List[StudentProfile], question_type: QuestionType) -> str:
        """Instructions spécialisées selon profil et type de question"""
        
        base_instructions = """
- Utilise le template de réponse fourni ci-dessus
- Reste dans le persona spécialisé assigné  
- Cite des sources officielles quand possible
- Fournis des exemples concrets et témoignages
- Adapte le niveau technique au profil détecté
        """
        
        # Instructions spécifiques aux profils anxieux/incertains
        if StudentProfile.ANXIOUS in profiles:
            base_instructions += """
- PRIORITÉ: Ton rassurant et décomposition claire
- Évite les informations qui pourraient augmenter l'anxiété
- Termine toujours sur une note positive et des prochaines étapes simples
- Utilise des formules rassurantes: "C'est tout à fait normal...", "Beaucoup d'étudiants..."
            """
        
        if StudentProfile.UNCERTAIN in profiles:
            base_instructions += """
- PRIORITÉ: Questions de clarification et exploration des intérêts
- Propose des exercices simples d'auto-découverte
- Évite de surcharger avec trop d'options d'un coup
- Focus sur 2-3 pistes maximum par réponse
            """
        
        return base_instructions
    
    def _get_relevant_examples(self, profiles: List[StudentProfile], question_type: QuestionType) -> str:
        """Exemples pertinents selon le profil et type de question"""
        
        examples_bank = {
            (StudentProfile.SCIENTIFIC, QuestionType.ORIENTATION_GENERALE): """
**Exemple de parcours réussi - Profil Scientifique:**
"Ahmed, SM-B avec 15.5 de moyenne, passionné d'informatique mais pas sûr de sa voie.
Après analyse: ENSA Informatique (priorité), ENSIAS (alternative), EST (sécurité).
Stratégie: renforcer projets persos, stage découverte, préparation concours."
            """,
            
            (StudentProfile.ANXIOUS, QuestionType.PROCEDURES): """
**Témoignage rassurant - Gestion stress procédures:**
"Fatima était très anxieuse pour les candidatures. On a décomposé étape par étape:
Semaine 1: rassembler documents, Semaine 2: remplir dossiers, Semaine 3: révision.
Résultat: admise dans ses 3 premiers choix. 'Je pensais que c'était impossible!'"
            """
        }
        
        # Chercher un exemple correspondant
        for profile in profiles:
            key = (profile, question_type)
            if key in examples_bank:
                return examples_bank[key]
        
        # Exemple générique de fallback
        return """
**Exemple général:**
Chaque étudiant est unique. En 15 ans d'expérience, j'ai vu des profils très variés réussir 
leur orientation en suivant une approche méthodique et personnalisée.
        """

# Fonctions utilitaires pour l'intégration
def get_enhanced_system_prompt(user_input: str, chat_history: List[Dict], base_prompt: str) -> str:
    """
    Point d'entrée principal pour générer un prompt système enrichi
    
    Args:
        user_input: Message de l'utilisateur
        chat_history: Historique des conversations
        base_prompt: Prompt système de base
        
    Returns:
        Prompt système enrichi et personnalisé
    """
    prompt_system = EnhancedPromptSystem()
    return prompt_system.generate_enhanced_system_prompt(user_input, chat_history, base_prompt)

def detect_user_profiles(user_input: str, chat_history: List[Dict]) -> List[str]:
    """
    Fonction utilitaire pour détecter les profils utilisateur
    
    Returns:
        Liste des profils détectés sous forme de strings
    """
    prompt_system = EnhancedPromptSystem()
    profiles = prompt_system.detect_student_profile(user_input, chat_history)
    return [profile.value for profile in profiles]

def classify_user_question(user_input: str) -> str:
    """
    Fonction utilitaire pour classifier le type de question
    
    Returns:
        Type de question sous forme de string
    """
    prompt_system = EnhancedPromptSystem()
    question_type = prompt_system.classify_question_type(user_input)
    return question_type.value