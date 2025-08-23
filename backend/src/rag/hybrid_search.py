"""
Système de recherche hybride combinant recherche vectorielle et recherche par mots-clés
Optimisé pour OrientaBot - données factuelles + recherche sémantique
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import math
from collections import defaultdict, Counter

# Import des modules existants
from .vector_store import VectorStore, DocumentChunk
from .semantic_processor import SemanticChunk, ContentType, InstitutionType

logger = logging.getLogger(__name__)

class SearchMode(Enum):
    """Modes de recherche disponibles"""
    VECTOR_ONLY = "vector_only"           # Recherche vectorielle uniquement
    KEYWORD_ONLY = "keyword_only"         # Recherche par mots-clés uniquement
    HYBRID = "hybrid"                     # Combinaison des deux
    AUTO = "auto"                         # Sélection automatique selon la requête

class QueryType(Enum):
    """Types de requêtes détectées"""
    FACTUAL = "factual"                   # Questions factuelles (seuils, dates, frais)
    CONCEPTUAL = "conceptual"             # Questions conceptuelles (débouchés, programmes)
    PROCEDURAL = "procedural"             # Questions procédurales (comment faire)
    COMPARATIVE = "comparative"           # Questions comparatives (A vs B)

@dataclass
class SearchResult:
    """Résultat de recherche enrichi"""
    chunk: DocumentChunk
    vector_score: float = 0.0
    keyword_score: float = 0.0
    hybrid_score: float = 0.0
    matched_keywords: List[str] = field(default_factory=list)
    content_type: Optional[ContentType] = None
    institution_type: Optional[InstitutionType] = None
    relevance_factors: Dict[str, float] = field(default_factory=dict)

class HybridSearchEngine:
    """Moteur de recherche hybride pour OrientaBot"""
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialise le moteur de recherche hybride
        
        Args:
            vector_store: Instance du store vectoriel existant
        """
        self.vector_store = vector_store
        
        # Patterns pour la détection du type de requête
        self.query_patterns = self._initialize_query_patterns()
        
        # Mots-clés factuels pour recherche directe
        self.factual_keywords = self._initialize_factual_keywords()
        
        # Index inversé pour recherche rapide par mots-clés
        self.keyword_index = defaultdict(set)
        self.tf_idf_cache = {}
        
        # Configuration de scoring
        self.vector_weight = 0.6        # Poids de la recherche vectorielle
        self.keyword_weight = 0.4       # Poids de la recherche par mots-clés
        self.boost_factors = self._initialize_boost_factors()
        
        logger.info("Moteur de recherche hybride initialisé")
    
    def _initialize_query_patterns(self) -> Dict[QueryType, List[str]]:
        """Patterns pour détecter le type de requête"""
        return {
            QueryType.FACTUAL: [
                r'(?:seuil|note|moyenne|minimum).*?(\d+)',
                r'combien.*?(?:coûte|frais|prix)',
                r'quand.*?(?:inscription|candidature)',
                r'(?:date|deadline|échéance)',
                r'(\d+)\s*(?:/20|sur 20)',
                r'(?:frais|coût|tarif).*?(\d+)',
                r'capacité.*?(\d+)',
                r'durée.*?(\d+).*?(?:ans?|années?)',
            ],
            
            QueryType.CONCEPTUAL: [
                r'qu[e\']?est[- ]ce que',
                r'expliquez?.*?moi',
                r'définition|signification',
                r'pourquoi.*?(?:choisir|important)',
                r'avantages?|inconvénients?',
                r'différence.*?entre',
            ],
            
            QueryType.PROCEDURAL: [
                r'comment.*?(?:faire|procéder|candidater|inscrire)',
                r'étapes?.*?(?:inscription|candidature)',
                r'procédure|démarche|processus',
                r'quelles.*?sont.*?étapes?',
                r'je dois.*?(?:faire|préparer)',
            ],
            
            QueryType.COMPARATIVE: [
                r'(?:mieux|meilleur).*?(?:entre|que)',
                r'comparer|comparaison',
                r'différence.*?entre',
                r'(?:ensa|emsi|est).*?(?:vs|versus|ou)',
                r'choisir.*?entre',
                r'lequel.*?(?:choisir|mieux)',
            ]
        }
    
    def _initialize_factual_keywords(self) -> Dict[str, List[str]]:
        """Mots-clés pour données factuelles"""
        return {
            'seuils_admission': [
                'seuil', 'moyenne', 'minimum', 'note', 'exigé', 'requis',
                'barème', 'notation', 'sur 20', '/20'
            ],
            'frais_scolarite': [
                'frais', 'coût', 'prix', 'tarif', 'paiement', 'scolarité',
                'dh', 'dirham', 'euro', 'gratuit', 'payant'
            ],
            'dates_procedures': [
                'date', 'inscription', 'candidature', 'deadline', 'échéance',
                'calendrier', 'planning', 'quand', 'période'
            ],
            'duree_formation': [
                'durée', 'ans', 'années', 'semestres', 'formation',
                'cursus', 'programme', 'cycle'
            ],
            'capacite_accueil': [
                'places', 'étudiants', 'candidats', 'capacité', 'accueil',
                'nombre', 'effectif', 'promotion'
            ]
        }
    
    def _initialize_boost_factors(self) -> Dict[str, float]:
        """Facteurs de boost selon le type de contenu"""
        return {
            ContentType.SEUILS_NOTES.value: 1.5,           # Boost pour questions sur seuils
            ContentType.CONDITIONS_ADMISSION.value: 1.3,    # Boost pour conditions
            ContentType.PROCEDURES_CANDIDATURE.value: 1.3,  # Boost pour procédures
            ContentType.FRAIS_SCOLARITE.value: 1.4,        # Boost pour frais
            ContentType.DEBOUCHES_METIERS.value: 1.2,      # Boost pour débouchés
            ContentType.PRESENTATION_GENERALE.value: 0.9,   # Moins de priorité
            ContentType.VIE_ETUDIANTE.value: 0.8,          # Moins de priorité
        }
    
    def build_keyword_index(self, chunks: List[DocumentChunk]) -> None:
        """
        Construit l'index inversé pour la recherche par mots-clés
        
        Args:
            chunks: Liste des chunks à indexer
        """
        logger.info(f"Construction de l'index mots-clés pour {len(chunks)} chunks...")
        
        # Réinitialiser l'index
        self.keyword_index.clear()
        self.tf_idf_cache.clear()
        
        # Document frequencies pour TF-IDF
        doc_count = len(chunks)
        word_doc_count = defaultdict(int)
        
        # Premier passage : compter les documents contenant chaque mot
        for i, chunk in enumerate(chunks):
            words = self._extract_keywords(chunk.content)
            unique_words = set(words)
            
            for word in unique_words:
                word_doc_count[word] += 1
        
        # Deuxième passage : construire l'index avec scores TF-IDF
        for i, chunk in enumerate(chunks):
            words = self._extract_keywords(chunk.content)
            word_count = Counter(words)
            doc_length = len(words)
            
            for word, count in word_count.items():
                # Calculer TF-IDF
                tf = count / doc_length
                idf = math.log(doc_count / (word_doc_count[word] + 1))
                tf_idf = tf * idf
                
                # Ajouter au cache
                if (i, word) not in self.tf_idf_cache:
                    self.tf_idf_cache[(i, word)] = tf_idf
                
                # Ajouter à l'index inversé
                self.keyword_index[word.lower()].add(i)
        
        logger.info(f"Index mots-clés construit: {len(self.keyword_index)} termes indexés")
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extrait les mots-clés pertinents d'un texte
        
        Args:
            text: Texte à analyser
            
        Returns:
            Liste des mots-clés extraits
        """
        # Normaliser le texte
        text = text.lower()
        
        # Extraire les mots (y compris les nombres et expressions spéciales)
        words = re.findall(r'\b(?:\d+(?:[.,]\d+)?(?:/20|sur 20)?|\w{3,})\b', text)
        
        # Filtrer les mots vides français
        stop_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou',
            'mais', 'donc', 'car', 'ni', 'or', 'dans', 'sur', 'avec', 'par',
            'pour', 'sans', 'sous', 'vers', 'chez', 'entre', 'jusqu', 'depuis',
            'pendant', 'avant', 'après', 'ce', 'ces', 'cette', 'cet', 'son',
            'sa', 'ses', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'notre',
            'nos', 'votre', 'vos', 'leur', 'leurs', 'qui', 'que', 'quoi',
            'dont', 'où', 'il', 'elle', 'ils', 'elles', 'nous', 'vous',
            'je', 'tu', 'on', 'être', 'avoir', 'faire', 'aller', 'venir',
            'voir', 'savoir', 'pouvoir', 'vouloir', 'devoir', 'falloir',
            'très', 'plus', 'moins', 'aussi', 'bien', 'mieux', 'beaucoup',
            'peu', 'pas', 'non', 'oui', 'si'
        }
        
        # Filtrer et garder les mots pertinents
        keywords = []
        for word in words:
            if len(word) >= 3 and word not in stop_words:
                keywords.append(word)
        
        return keywords
    
    def detect_query_type(self, query: str) -> QueryType:
        """
        Détecte le type de requête
        
        Args:
            query: Requête à analyser
            
        Returns:
            Type de requête détecté
        """
        query_lower = query.lower()
        
        # Scores pour chaque type
        type_scores = {}
        
        for query_type, patterns in self.query_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query_lower))
                score += matches
            
            # Normaliser le score
            type_scores[query_type] = score / len(patterns)
        
        # Retourner le type avec le meilleur score
        best_type = max(type_scores, key=type_scores.get)
        
        # Si aucun pattern ne matche bien, c'est conceptuel par défaut
        if type_scores[best_type] == 0:
            return QueryType.CONCEPTUAL
        
        return best_type
    
    def select_search_mode(self, query: str, query_type: QueryType) -> SearchMode:
        """
        Sélectionne le mode de recherche optimal
        
        Args:
            query: Requête utilisateur
            query_type: Type de requête détecté
            
        Returns:
            Mode de recherche optimal
        """
        # Questions factuelles privilégient les mots-clés
        if query_type == QueryType.FACTUAL:
            # Mais utiliser hybride si la question est complexe
            if len(query.split()) > 8:
                return SearchMode.HYBRID
            else:
                return SearchMode.KEYWORD_ONLY
        
        # Questions comparatives privilégient le vectoriel
        elif query_type == QueryType.COMPARATIVE:
            return SearchMode.HYBRID  # Hybride pour capturer les nuances
        
        # Questions procédurales peuvent bénéficier des deux
        elif query_type == QueryType.PROCEDURAL:
            return SearchMode.HYBRID
        
        # Questions conceptuelles privilégient le vectoriel
        else:
            return SearchMode.VECTOR_ONLY
    
    def keyword_search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        Recherche par mots-clés avec scoring TF-IDF
        
        Args:
            query: Requête de recherche
            top_k: Nombre max de résultats
            
        Returns:
            Liste des résultats de recherche
        """
        if not self.keyword_index:
            logger.warning("Index mots-clés non construit")
            return []
        
        # Extraire les mots-clés de la requête
        query_keywords = self._extract_keywords(query)
        
        if not query_keywords:
            return []
        
        # Scores des documents
        doc_scores = defaultdict(float)
        doc_matched_keywords = defaultdict(list)
        
        # Calculer les scores pour chaque document
        for keyword in query_keywords:
            keyword_lower = keyword.lower()
            
            # Trouver les documents contenant ce mot-clé
            if keyword_lower in self.keyword_index:
                for doc_idx in self.keyword_index[keyword_lower]:
                    # Score TF-IDF depuis le cache
                    if (doc_idx, keyword_lower) in self.tf_idf_cache:
                        score = self.tf_idf_cache[(doc_idx, keyword_lower)]
                        doc_scores[doc_idx] += score
                        doc_matched_keywords[doc_idx].append(keyword)
        
        # Normaliser les scores et créer les résultats
        results = []
        
        for doc_idx, score in doc_scores.items():
            if doc_idx < len(self.vector_store.chunks):
                chunk = self.vector_store.chunks[doc_idx]
                
                # Normaliser le score par le nombre de mots-clés matchés
                normalized_score = score / len(query_keywords)
                
                result = SearchResult(
                    chunk=chunk,
                    keyword_score=normalized_score,
                    matched_keywords=doc_matched_keywords[doc_idx]
                )
                results.append(result)
        
        # Trier par score décroissant et retourner top_k
        results.sort(key=lambda x: x.keyword_score, reverse=True)
        
        logger.info(f"Recherche mots-clés pour '{query[:50]}...': {len(results)} résultat(s)")
        
        return results[:top_k]
    
    def vector_search(self, query: str, top_k: int = 10, score_threshold: float = 0.5) -> List[SearchResult]:
        """
        Recherche vectorielle avec conversion en SearchResult
        
        Args:
            query: Requête de recherche
            top_k: Nombre max de résultats
            score_threshold: Seuil de score minimum
            
        Returns:
            Liste des résultats de recherche
        """
        # Utiliser la recherche vectorielle existante
        vector_results = self.vector_store.search(query, top_k, score_threshold)
        
        # Convertir en SearchResult
        results = []
        for chunk, score in vector_results:
            result = SearchResult(
                chunk=chunk,
                vector_score=score
            )
            results.append(result)
        
        logger.info(f"Recherche vectorielle pour '{query[:50]}...': {len(results)} résultat(s)")
        
        return results
    
    def hybrid_search(self, 
                     query: str, 
                     top_k: int = 10, 
                     vector_weight: Optional[float] = None,
                     keyword_weight: Optional[float] = None) -> List[SearchResult]:
        """
        Recherche hybride combinant vectoriel et mots-clés
        
        Args:
            query: Requête de recherche
            top_k: Nombre max de résultats
            vector_weight: Poids de la recherche vectorielle (optionnel)
            keyword_weight: Poids de la recherche par mots-clés (optionnel)
            
        Returns:
            Liste des résultats combinés
        """
        # Utiliser les poids par défaut si non spécifiés
        if vector_weight is None:
            vector_weight = self.vector_weight
        if keyword_weight is None:
            keyword_weight = self.keyword_weight
        
        # Recherches séparées
        vector_results = self.vector_search(query, top_k * 2)  # Plus de résultats pour fusion
        keyword_results = self.keyword_search(query, top_k * 2)
        
        # Fusion des résultats
        combined_results = self._merge_search_results(
            vector_results, keyword_results, vector_weight, keyword_weight
        )
        
        # Appliquer les facteurs de boost
        boosted_results = self._apply_content_boost(combined_results, query)
        
        # Trier par score hybride et retourner top_k
        boosted_results.sort(key=lambda x: x.hybrid_score, reverse=True)
        
        logger.info(f"Recherche hybride pour '{query[:50]}...': {len(boosted_results)} résultat(s)")
        
        return boosted_results[:top_k]
    
    def _merge_search_results(self, 
                             vector_results: List[SearchResult],
                             keyword_results: List[SearchResult],
                             vector_weight: float,
                             keyword_weight: float) -> List[SearchResult]:
        """Fusionne les résultats des deux modes de recherche"""
        
        # Index pour retrouver rapidement les résultats par chunk_id
        vector_index = {r.chunk.chunk_id: r for r in vector_results}
        keyword_index = {r.chunk.chunk_id: r for r in keyword_results}
        
        # Tous les chunks uniques
        all_chunk_ids = set(vector_index.keys()) | set(keyword_index.keys())
        
        merged_results = []
        
        for chunk_id in all_chunk_ids:
            # Scores des deux modes (0 si absent)
            vector_score = vector_index[chunk_id].vector_score if chunk_id in vector_index else 0.0
            keyword_score = keyword_index[chunk_id].keyword_score if chunk_id in keyword_index else 0.0
            
            # Score hybride pondéré
            hybrid_score = (vector_score * vector_weight) + (keyword_score * keyword_weight)
            
            # Prendre le chunk du résultat disponible
            chunk = vector_index[chunk_id].chunk if chunk_id in vector_index else keyword_index[chunk_id].chunk
            
            # Mots-clés matchés (de la recherche par mots-clés)
            matched_keywords = keyword_index[chunk_id].matched_keywords if chunk_id in keyword_index else []
            
            result = SearchResult(
                chunk=chunk,
                vector_score=vector_score,
                keyword_score=keyword_score,
                hybrid_score=hybrid_score,
                matched_keywords=matched_keywords
            )
            
            merged_results.append(result)
        
        return merged_results
    
    def _apply_content_boost(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Applique les facteurs de boost selon le type de contenu"""
        
        # Détecter les types de contenu recherchés dans la requête
        query_lower = query.lower()
        
        for result in results:
            boost_factor = 1.0
            
            # Analyser les métadonnées du chunk si disponibles
            if hasattr(result.chunk, 'metadata') and result.chunk.metadata:
                content_type = result.chunk.metadata.get('content_type')
                if content_type and content_type in self.boost_factors:
                    boost_factor = self.boost_factors[content_type]
            
            # Boost contextuel basé sur la requête
            contextual_boost = self._calculate_contextual_boost(query_lower, result.chunk.content)
            
            # Score final avec boost
            result.hybrid_score *= (boost_factor * contextual_boost)
            result.relevance_factors = {
                'content_boost': boost_factor,
                'contextual_boost': contextual_boost,
                'final_boost': boost_factor * contextual_boost
            }
        
        return results
    
    def _calculate_contextual_boost(self, query: str, content: str) -> float:
        """Calcule le boost contextuel selon la correspondance thématique"""
        
        content_lower = content.lower()
        boost = 1.0
        
        # Boost pour correspondance d'établissement
        institutions = ['ensa', 'emsi', 'emi', 'ensias', 'encg', 'est', 'fst', 'fsjes']
        for inst in institutions:
            if inst in query and inst in content_lower:
                boost += 0.2
                break
        
        # Boost pour correspondance de filière
        filieres = ['sciences math', 'sm', 'sciences physiques', 'sp', 'svt', 'st', 'se', 'lsh']
        for filiere in filieres:
            if filiere in query and filiere in content_lower:
                boost += 0.15
                break
        
        # Boost pour données numériques si requête factuelle
        if re.search(r'\d+', query) and re.search(r'\d+', content_lower):
            boost += 0.1
        
        return min(boost, 2.0)  # Limiter le boost maximum
    
    def search(self, 
              query: str, 
              top_k: int = 5, 
              mode: SearchMode = SearchMode.AUTO) -> List[SearchResult]:
        """
        Point d'entrée principal pour la recherche
        
        Args:
            query: Requête de l'utilisateur
            top_k: Nombre max de résultats
            mode: Mode de recherche (AUTO pour sélection automatique)
            
        Returns:
            Liste des résultats de recherche
        """
        logger.info(f"Recherche: '{query[:50]}...', mode: {mode.value}")
        
        # Détecter le type de requête
        query_type = self.detect_query_type(query)
        logger.info(f"Type de requête détecté: {query_type.value}")
        
        # Sélectionner le mode de recherche si AUTO
        if mode == SearchMode.AUTO:
            mode = self.select_search_mode(query, query_type)
            logger.info(f"Mode de recherche sélectionné: {mode.value}")
        
        # Exécuter la recherche selon le mode
        if mode == SearchMode.VECTOR_ONLY:
            return self.vector_search(query, top_k)
        elif mode == SearchMode.KEYWORD_ONLY:
            return self.keyword_search(query, top_k)
        else:  # HYBRID
            return self.hybrid_search(query, top_k)
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du système de recherche"""
        return {
            'vector_store_available': self.vector_store.ml_available,
            'total_documents': len(self.vector_store.chunks),
            'keyword_index_terms': len(self.keyword_index),
            'tf_idf_cache_size': len(self.tf_idf_cache),
            'boost_factors': self.boost_factors,
            'weights': {
                'vector_weight': self.vector_weight,
                'keyword_weight': self.keyword_weight
            }
        }

# Fonctions utilitaires pour l'intégration
def create_hybrid_search_engine(vector_store: VectorStore) -> HybridSearchEngine:
    """
    Crée et initialise le moteur de recherche hybride
    
    Args:
        vector_store: Store vectoriel existant
        
    Returns:
        Instance du moteur de recherche hybride
    """
    engine = HybridSearchEngine(vector_store)
    
    # Construire l'index mots-clés si des chunks sont disponibles
    if vector_store.chunks:
        engine.build_keyword_index(vector_store.chunks)
    
    return engine