"""
Processeur sémantique pour chunking intelligent et métadonnées enrichies
Amélioration majeure du système RAG d'OrientaBot
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Types de contenu détectés dans les documents"""
    PRESENTATION_GENERALE = "presentation_generale"
    CONDITIONS_ADMISSION = "conditions_admission"
    PROCEDURES_CANDIDATURE = "procedures_candidature"
    SEUILS_NOTES = "seuils_notes"
    DEBOUCHES_METIERS = "debouches_metiers"
    PROGRAMME_FORMATION = "programme_formation"
    VIE_ETUDIANTE = "vie_etudiante"
    FRAIS_SCOLARITE = "frais_scolarite"
    INFRASTRUCTURE = "infrastructure"
    PARTENARIATS = "partenariats"
    CONTACT_INFO = "contact_info"
    AUTRE = "autre"

class InstitutionType(Enum):
    """Types d'établissements"""
    ENSA = "ensa"              # École Nationale des Sciences Appliquées
    EMSI = "emsi"              # École Marocaine des Sciences de l'Ingénieur  
    EMI = "emi"                # École Mohammadia d'Ingénieurs
    ENSIAS = "ensias"          # École Nationale Supérieure d'Informatique
    ENCG = "encg"              # École Nationale de Commerce et de Gestion
    EST = "est"                # École Supérieure de Technologie
    FST = "fst"                # Faculté des Sciences et Techniques
    FSJES = "fsjes"            # Faculté des Sciences Juridiques, Économiques et Sociales
    ISPITS = "ispits"          # Institut Spécialisé des Technologies
    UNIVERSITE_PRIVE = "universite_prive"
    AUTRE = "autre"

@dataclass
class SemanticChunk:
    """Chunk sémantique enrichi avec métadonnées structurées"""
    content: str
    source: str
    page_number: int
    chunk_id: str
    
    # Métadonnées sémantiques
    content_type: ContentType
    institution_type: InstitutionType
    institution_name: str
    
    # Entités extraites
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    
    # Métadonnées techniques
    confidence_score: float = 0.0
    section_title: str = ""
    keywords: List[str] = field(default_factory=list)
    
    # Métadonnées originales pour compatibilité
    metadata: Dict[str, Any] = field(default_factory=dict)

class SemanticDocumentProcessor:
    """Processeur de documents avec analyse sémantique"""
    
    def __init__(self):
        self.section_patterns = self._initialize_section_patterns()
        self.entity_patterns = self._initialize_entity_patterns()
        self.institution_patterns = self._initialize_institution_patterns()
        
    def _initialize_section_patterns(self) -> Dict[ContentType, List[str]]:
        """Patterns pour identifier les sections de contenu"""
        return {
            ContentType.PRESENTATION_GENERALE: [
                r'présentation|à propos|histoire|création|mission|vision|valeurs',
                r'qui sommes nous|notre école|notre établissement',
                r'introduction|overview|general',
            ],
            
            ContentType.CONDITIONS_ADMISSION: [
                r'conditions?\s+d[\'e]?\s*admission|critères?\s+d[\'e]?\s*admission',
                r'prérequis|requirements|eligibility',
                r'conditions?\s+d[\'e]?\s*accès|modalités?\s+d[\'e]?\s*admission',
                r'profil?\s+requis|diplômes?\s+requis',
            ],
            
            ContentType.PROCEDURES_CANDIDATURE: [
                r'procédures?\s+de\s+candidature|comment\s+candidater',
                r'inscription|candidature|application',
                r'étapes?\s+d[\'e]?\s*inscription|démarches?',
                r'concours|sélection|recrutement',
            ],
            
            ContentType.SEUILS_NOTES: [
                r'seuils?|notes?\s+minimum|moyennes?\s+requises?',
                r'barème|notation|évaluation',
                r'notes?\s+d[\'e]?\s*admission|résultats?\s+requis',
                r'moyenne\s+générale|mentions?',
            ],
            
            ContentType.DEBOUCHES_METIERS: [
                r'débouchés?|métiers?|carrières?|emplois?',
                r'opportunités?\s+professionnelles?|perspectives?\s+d[\'e]?\s*emploi',
                r'secteurs?\s+d[\'e]?\s*activité|domaines?\s+d[\'e]?\s*intervention',
                r'après\s+la\s+formation|que\s+faire\s+après',
            ],
            
            ContentType.PROGRAMME_FORMATION: [
                r'programme|formation|cursus|modules?',
                r'matières?|disciplines?|enseignements?',
                r'spécialisations?|options?|parcours',
                r'plan\s+d[\'e]?\s*études|structure\s+pédagogique',
            ],
            
            ContentType.VIE_ETUDIANTE: [
                r'vie\s+étudiante|campus|résidence|logement',
                r'activités?\s+extra.?scolaires?|clubs?|associations?',
                r'services?\s+aux\s+étudiants|restauration',
                r'sport|culture|loisirs?',
            ],
            
            ContentType.FRAIS_SCOLARITE: [
                r'frais|coûts?|tarifs?|prix',
                r'scolarité|financement|bourses?',
                r'droits?\s+d[\'e]?\s*inscription|droits?\s+universitaires?',
                r'paiement|facturation',
            ],
            
            ContentType.INFRASTRUCTURE: [
                r'infrastructure|équipements?|installations?',
                r'laboratoires?|bibliothèques?|salles?',
                r'matériel|technologies?|outils',
                r'locaux|bâtiments?|campus',
            ],
            
            ContentType.PARTENARIATS: [
                r'partenariats?|partenaires?|conventions?',
                r'entreprises?\s+partenaires?|collaborations?',
                r'accords?|coopération|échanges?',
                r'international|stages?|alternance',
            ],
            
            ContentType.CONTACT_INFO: [
                r'contact|coordonnées|adresse',
                r'téléphone|email|site\s+web',
                r'comment\s+nous\s+joindre|nous\s+contacter',
                r'localisation|plan\s+d[\'e]?\s*accès',
            ]
        }
    
    def _initialize_entity_patterns(self) -> Dict[str, List[str]]:
        """Patterns pour extraire des entités spécifiques"""
        return {
            'dates_importantes': [
                r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}',
                r'\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}',
                r'(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}',
            ],
            'seuils_notes': [
                r'(?:moyenne|note|seuil).*?(\d{1,2}(?:[.,]\d{1,2})?)\s*(?:/20|sur 20)',
                r'(\d{1,2}(?:[.,]\d{1,2})?)\s*(?:/20|sur 20).*?(?:minimum|requis|exigé)',
                r'au moins\s+(\d{1,2}(?:[.,]\d{1,2})?)',
            ],
            'frais_montants': [
                r'(\d+(?:\s?\d{3})*)\s*(?:dh|dirhams?|mad)',
                r'(\d+(?:[.,]\d+)?)\s*(?:mille|millions?)',
            ],
            'duree_formation': [
                r'(\d+)\s*ans?',
                r'(\d+)\s*années?',
                r'(\d+)\s*semestres?',
            ],
            'capacite_accueil': [
                r'(\d+)\s*(?:places?|étudiants?|candidats?)',
                r'capacité.*?(\d+)',
                r'accueille.*?(\d+)',
            ]
        }
    
    def _initialize_institution_patterns(self) -> Dict[InstitutionType, List[str]]:
        """Patterns pour identifier le type d'établissement"""
        return {
            InstitutionType.ENSA: [
                r'école nationale des sciences appliquées|ensa',
                r'national school of applied sciences',
            ],
            InstitutionType.EMSI: [
                r'école marocaine des sciences de l\'ingénieur|emsi',
                r'moroccan school of engineering sciences',
            ],
            InstitutionType.EMI: [
                r'école mohammadia d\'ingénieurs|emi',
                r'mohammadia school of engineers',
            ],
            InstitutionType.ENSIAS: [
                r'école nationale supérieure d\'informatique|ensias',
                r'national school of computer science',
            ],
            InstitutionType.ENCG: [
                r'école nationale de commerce et de gestion|encg',
                r'national school of business and management',
            ],
            InstitutionType.EST: [
                r'école supérieure de technologie|est',
                r'higher school of technology',
            ],
            InstitutionType.FST: [
                r'faculté des sciences et techniques|fst',
                r'faculty of science and technology',
            ],
            InstitutionType.FSJES: [
                r'faculté des sciences juridiques|fsjes',
                r'faculty of legal economic and social sciences',
            ],
            InstitutionType.ISPITS: [
                r'institut spécialisé des technologies|ispits',
                r'specialized institute of technology',
            ]
        }
    
    def detect_content_type(self, text: str, section_title: str = "") -> Tuple[ContentType, float]:
        """
        Détecte le type de contenu d'un texte
        
        Args:
            text: Texte à analyser
            section_title: Titre de section si disponible
            
        Returns:
            Tuple (type_contenu, score_confiance)
        """
        text_lower = (text + " " + section_title).lower()
        best_match = ContentType.AUTRE
        best_score = 0.0
        
        for content_type, patterns in self.section_patterns.items():
            score = 0.0
            
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                # Pondération plus forte pour les titres
                if section_title and re.search(pattern, section_title.lower()):
                    matches += 3
                score += matches
            
            # Normaliser le score
            normalized_score = min(score / len(patterns), 1.0)
            
            if normalized_score > best_score:
                best_score = normalized_score
                best_match = content_type
        
        return best_match, best_score
    
    def detect_institution_type(self, source_filename: str, text: str) -> Tuple[InstitutionType, str]:
        """
        Détecte le type d'établissement et son nom
        
        Args:
            source_filename: Nom du fichier source
            text: Texte du document
            
        Returns:
            Tuple (type_institution, nom_institution)
        """
        combined_text = (source_filename + " " + text[:1000]).lower()
        
        for institution_type, patterns in self.institution_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined_text):
                    # Extraire le nom spécifique
                    institution_name = self._extract_specific_institution_name(
                        source_filename, text, institution_type
                    )
                    return institution_type, institution_name
        
        return InstitutionType.AUTRE, self._extract_generic_institution_name(source_filename)
    
    def _extract_specific_institution_name(self, filename: str, text: str, inst_type: InstitutionType) -> str:
        """Extrait le nom spécifique de l'établissement"""
        
        # Patterns spécifiques pour extraire les noms complets
        name_patterns = {
            InstitutionType.ENSA: [
                r'ensa[- ](\w+)',
                r'école nationale des sciences appliquées[- ](\w+)',
            ],
            InstitutionType.ENCG: [
                r'encg[- ](\w+)',
                r'école nationale de commerce et de gestion[- ](\w+)',
            ],
            InstitutionType.EST: [
                r'est[- ](\w+)',
                r'école supérieure de technologie[- ](\w+)',
            ]
        }
        
        if inst_type in name_patterns:
            combined_text = (filename + " " + text[:500]).lower()
            for pattern in name_patterns[inst_type]:
                match = re.search(pattern, combined_text)
                if match:
                    city = match.group(1).title()
                    return f"{inst_type.value.upper()} {city}"
        
        # Fallback vers le nom du fichier nettoyé
        return self._extract_generic_institution_name(filename)
    
    def _extract_generic_institution_name(self, filename: str) -> str:
        """Extrait un nom générique depuis le nom de fichier"""
        # Nettoyer le nom de fichier
        name = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
        # Capitaliser
        return ' '.join(word.capitalize() for word in name.split())
    
    def extract_entities(self, text: str, content_type: ContentType) -> Dict[str, Any]:
        """
        Extrait les entités pertinentes selon le type de contenu
        
        Args:
            text: Texte à analyser
            content_type: Type de contenu détecté
            
        Returns:
            Dictionnaire des entités extraites
        """
        entities = {}
        
        # Extraction générale pour tous les types
        for entity_type, patterns in self.entity_patterns.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, text, re.IGNORECASE)
                matches.extend(found)
            
            if matches:
                entities[entity_type] = matches
        
        # Extraction spécialisée selon le type de contenu
        if content_type == ContentType.CONDITIONS_ADMISSION:
            entities.update(self._extract_admission_requirements(text))
        elif content_type == ContentType.PROCEDURES_CANDIDATURE:
            entities.update(self._extract_procedure_steps(text))
        elif content_type == ContentType.DEBOUCHES_METIERS:
            entities.update(self._extract_career_info(text))
        
        return entities
    
    def _extract_admission_requirements(self, text: str) -> Dict[str, Any]:
        """Extrait les conditions d'admission spécifiques"""
        requirements = {}
        
        # Filières acceptées
        filiere_patterns = [
            r'(?:filières?|bac|bachelier).*?(sciences? math|sm|sciences? physiques?|sp|svt|st|se|lsh)',
        ]
        
        filieres = []
        for pattern in filiere_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            filieres.extend(matches)
        
        if filieres:
            requirements['filieres_acceptees'] = list(set(filieres))
        
        return requirements
    
    def _extract_procedure_steps(self, text: str) -> Dict[str, Any]:
        """Extrait les étapes de procédures"""
        procedures = {}
        
        # Étapes numérotées
        step_pattern = r'(\d+)[\.\-\)]\s*([^\.]+(?:\.[^\.]+)*)'
        steps = re.findall(step_pattern, text)
        
        if steps:
            procedures['etapes'] = [{"numero": num, "description": desc.strip()} for num, desc in steps]
        
        return procedures
    
    def _extract_career_info(self, text: str) -> Dict[str, Any]:
        """Extrait les informations sur les débouchés"""
        career_info = {}
        
        # Métiers mentionnés
        metier_patterns = [
            r'ingénieur\s+(\w+)',
            r'développeur\s+(\w+)',
            r'chef\s+de\s+(\w+)',
            r'responsable\s+(\w+)',
        ]
        
        metiers = []
        for pattern in metier_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            metiers.extend(matches)
        
        if metiers:
            career_info['metiers_mentionnes'] = list(set(metiers))
        
        return career_info
    
    def extract_keywords(self, text: str, content_type: ContentType) -> List[str]:
        """Extrait les mots-clés pertinents"""
        
        # Mots-clés spécialisés selon le type de contenu
        specialized_keywords = {
            ContentType.PRESENTATION_GENERALE: ['école', 'formation', 'mission', 'vision', 'établissement'],
            ContentType.CONDITIONS_ADMISSION: ['admission', 'conditions', 'prérequis', 'critères', 'bac'],
            ContentType.PROCEDURES_CANDIDATURE: ['candidature', 'inscription', 'dossier', 'concours', 'sélection'],
            ContentType.SEUILS_NOTES: ['seuil', 'moyenne', 'note', 'minimum', 'barème'],
            ContentType.DEBOUCHES_METIERS: ['métier', 'emploi', 'carrière', 'débouché', 'profession'],
            ContentType.PROGRAMME_FORMATION: ['programme', 'module', 'matière', 'cursus', 'spécialisation'],
        }
        
        keywords = specialized_keywords.get(content_type, [])
        
        # Extraction automatique des mots importants
        # Mots fréquents et significatifs (longueur > 4, pas de mots vides)
        words = re.findall(r'\b[a-zA-ZàâäéèêëïîôùûüÿçÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ]{5,}\b', text.lower())
        word_freq = {}
        
        stop_words = {'cette', 'dans', 'avec', 'pour', 'sont', 'leurs', 'nous', 'vous', 'elle', 'elles', 'tous', 'toutes'}
        
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Prendre les 5 mots les plus fréquents
        frequent_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        keywords.extend([word for word, freq in frequent_words])
        
        return list(set(keywords))
    
    def semantic_chunking(self, text: str, source: str, page_number: int) -> List[SemanticChunk]:
        """
        Découpage sémantique intelligent du texte
        
        Args:
            text: Texte de la page
            source: Source du document
            page_number: Numéro de page
            
        Returns:
            Liste des chunks sémantiques
        """
        chunks = []
        
        # Détecter le type d'établissement
        institution_type, institution_name = self.detect_institution_type(source, text)
        
        # Diviser le texte par sections si possible
        sections = self._split_by_sections(text)
        
        if len(sections) <= 1:
            # Pas de sections détectées, chunking classique amélioré
            sections = self._smart_split_text(text)
        
        for i, (section_title, section_text) in enumerate(sections):
            if not section_text.strip():
                continue
                
            # Détecter le type de contenu
            content_type, confidence = self.detect_content_type(section_text, section_title)
            
            # Extraire les entités
            entities = self.extract_entities(section_text, content_type)
            
            # Extraire les mots-clés
            keywords = self.extract_keywords(section_text, content_type)
            
            # Créer le chunk sémantique
            chunk = SemanticChunk(
                content=section_text,
                source=source,
                page_number=page_number,
                chunk_id=f"{source}_page_{page_number}_semantic_{i+1}",
                content_type=content_type,
                institution_type=institution_type,
                institution_name=institution_name,
                extracted_entities=entities,
                confidence_score=confidence,
                section_title=section_title,
                keywords=keywords,
                metadata={
                    'source_file': source,
                    'page_number': page_number,
                    'chunk_size': len(section_text),
                    'chunk_index': i+1,
                    'processing_type': 'semantic',
                    'content_type': content_type.value,
                    'institution_type': institution_type.value,
                    'confidence_score': confidence
                }
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _split_by_sections(self, text: str) -> List[Tuple[str, str]]:
        """Divise le texte par sections détectées"""
        
        # Patterns pour détecter les titres de sections
        section_patterns = [
            r'^[A-ZÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ][^.]*$',  # Ligne en majuscules
            r'^\d+\.?\s+[A-ZÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ][^.]*$',  # Numérotation
            r'^[IVX]+\.?\s+[A-ZÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ][^.]*$',  # Numérotation romaine
            r'^[A-Z]\)\s+[A-ZÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ][^.]*$',  # Lettres
        ]
        
        lines = text.split('\n')
        sections = []
        current_title = ""
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Vérifier si c'est un titre de section
            is_title = False
            for pattern in section_patterns:
                if re.match(pattern, line) and len(line) < 100:  # Titres généralement courts
                    is_title = True
                    break
            
            if is_title:
                # Sauvegarder la section précédente
                if current_content:
                    sections.append((current_title, '\n'.join(current_content)))
                
                # Commencer une nouvelle section
                current_title = line
                current_content = []
            else:
                current_content.append(line)
        
        # Ajouter la dernière section
        if current_content:
            sections.append((current_title, '\n'.join(current_content)))
        
        return sections
    
    def _smart_split_text(self, text: str, max_chunk_size: int = 800) -> List[Tuple[str, str]]:
        """Découpage intelligent sans sections détectées"""
        
        # Essayer de diviser par paragraphes
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        chunk_count = 1
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # Si ajouter ce paragraphe dépasse la taille max, finaliser le chunk actuel
            if current_chunk and len(current_chunk + para) > max_chunk_size:
                chunks.append((f"Section {chunk_count}", current_chunk))
                current_chunk = para
                chunk_count += 1
            else:
                current_chunk += ("\n\n" if current_chunk else "") + para
        
        # Ajouter le dernier chunk
        if current_chunk:
            chunks.append((f"Section {chunk_count}", current_chunk))
        
        return chunks

from .pdf_processor import DocumentChunk
def convert_to_document_chunk(semantic_chunk: SemanticChunk) -> 'DocumentChunk':
    """
    Convertit un SemanticChunk en DocumentChunk pour compatibilité
    
    Args:
        semantic_chunk: Chunk sémantique à convertir
        
    Returns:
        DocumentChunk compatible avec l'ancien système
    """
    
    
    return DocumentChunk(
        content=semantic_chunk.content,
        source=semantic_chunk.source,
        page_number=semantic_chunk.page_number,
        chunk_id=semantic_chunk.chunk_id,
        metadata=semantic_chunk.metadata
    )