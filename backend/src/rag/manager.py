"""
Gestionnaire RAG principal pour OrientaBot
Coordonne la recherche vectorielle et l'augmentation des prompts
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import re

# Fixed imports - use absolute imports from rag module
from .pdf_processor import PDFProcessor, DocumentChunk
from .vector_store import VectorStore

logger = logging.getLogger(__name__)

class RAGManager:
    """Gestionnaire principal du système RAG pour OrientaBot"""
    
    def __init__(self, 
                 pdf_folder: str = "data/raw",
                 vector_db_path: str = "data/processed",
                 chunk_size: int = 800,
                 chunk_overlap: int = 150,
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialise le gestionnaire RAG
        
        Args:
            pdf_folder: Dossier contenant les PDFs des écoles
            vector_db_path: Chemin vers la base vectorielle
            chunk_size: Taille des chunks de texte
            chunk_overlap: Chevauchement entre chunks
            embedding_model: Modèle d'embeddings à utiliser
        """
        
        # Chemins
        self.pdf_folder = Path(pdf_folder)
        self.vector_db_path = Path(vector_db_path)
        
        # Créer les dossiers s'ils n'existent pas
        self.pdf_folder.mkdir(parents=True, exist_ok=True)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        # Composants
        self.pdf_processor = PDFProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.vector_store = VectorStore(
            embedding_model=embedding_model, 
            vector_db_path=str(vector_db_path)
        )
        
        # Configuration
        self.max_context_chunks = 5
        self.min_relevance_score = 0.6
        self.context_window_size = 3000  # Taille max du contexte en caractères
        
        logger.info("RAGManager initialisé")
        logger.info(f"📂 PDFs: {self.pdf_folder}")
        logger.info(f"🗄️ Base vectorielle: {self.vector_db_path}")
    
    def initialize_knowledge_base(self, force_rebuild: bool = False) -> bool:
        """
        Initialise la base de connaissances à partir des PDFs
        
        Args:
            force_rebuild: Force la reconstruction de la base même si elle existe
            
        Returns:
            True si l'initialisation a réussi
        """
        # Vérifier si les dépendances ML sont disponibles
        if not self.vector_store.ml_available:
            logger.warning("ML dependencies not available. RAG system will be disabled.")
            return False
            
        try:
            # Vérifier si la base existe déjà 
            if not force_rebuild and self.vector_store._database_exists():
                logger.info("Base vectorielle existante trouvée")
                try:
                    self.vector_store.load_database()
                    stats = self.vector_store.get_stats()
                    logger.info(f"📊 Statistiques: {stats['total_chunks']} chunks, {len(stats['sources'])} sources")
                    return True
                except Exception as e:
                    logger.warning(f"Erreur lors du chargement de la base existante: {e}")
                    logger.info("Reconstruction de la base...")
                    force_rebuild = True
            
            # Vérifier que le dossier PDFs existe et contient des fichiers
            if not self.pdf_folder.exists():
                logger.error(f"Dossier PDFs non trouvé: {self.pdf_folder}")
                return False
            
            pdf_files = list(self.pdf_folder.glob("*.pdf"))
            if not pdf_files:
                logger.warning(f"Aucun PDF trouvé dans: {self.pdf_folder}")
                return False
            
            logger.info(f"Initialisation de la base de connaissances avec {len(pdf_files)} PDF(s)")
            
            # Traiter tous les PDFs
            all_chunks = self.pdf_processor.process_all_pdfs(self.pdf_folder)
            
            if not all_chunks:
                logger.error("Aucun chunk créé depuis les PDFs")
                return False
            
            # Construire l'index vectoriel
            self.vector_store.build_index(all_chunks)
            
            # Sauvegarder la base
            self.vector_store.save_database()
            
            logger.info("✅ Base de connaissances initialisée avec succès")
            
            # Afficher les statistiques
            stats = self.vector_store.get_stats()
            logger.info(f"📊 Total: {stats['total_chunks']} chunks créés")
            logger.info(f"📚 Sources: {', '.join(stats['sources'])}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base: {e}")
            return False
    
    def search_knowledge(self, query: str, top_k: int = None) -> List[Tuple[DocumentChunk, float]]:
        """
        Recherche dans la base de connaissances
        
        Args:
            query: Question ou requête de recherche
            top_k: Nombre max de résultats (par défaut: self.max_context_chunks)
            
        Returns:
            Liste des chunks pertinents avec leurs scores
        """
        if not self.vector_store.ml_available:
            logger.warning("Cannot search: ML dependencies not available")
            return []
            
        if top_k is None:
            top_k = self.max_context_chunks
        
        try:
            # Préprocesser la requête
            processed_query = self._preprocess_query(query)
            
            # Rechercher dans la base vectorielle
            results = self.vector_store.search(
                processed_query,
                top_k=top_k,
                score_threshold=self.min_relevance_score
            )
            
            logger.info(f"Recherche: {len(results)} résultat(s) pertinent(s)")
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {e}")
            return []
    
    def get_context_for_query(self, query: str) -> Optional[str]:
        """
        Récupère le contexte pertinent pour une requête donnée
        
        Args:
            query: Question de l'utilisateur
            
        Returns:
            Contexte formaté ou None si aucun contexte trouvé
        """
        # Rechercher les chunks pertinents
        search_results = self.search_knowledge(query)
        
        if not search_results:
            logger.info("Aucun contexte pertinent trouvé")
            return None
        
        # Construire le contexte
        context_parts = []
        total_length = 0
        
        for chunk, score in search_results:
            # Vérifier si l'ajout de ce chunk dépasserait la limite
            chunk_text = f"\n**[{chunk.source} - Page {chunk.page_number}]**\n{chunk.content}\n"
            
            if total_length + len(chunk_text) > self.context_window_size:
                break
            
            context_parts.append({
                'text': chunk_text,
                'score': score,
                'source': chunk.source,
                'page': chunk.page_number
            })
            
            total_length += len(chunk_text)
        
        if not context_parts:
            return None
        
        # Formater le contexte final
        context = "## CONTEXTE SPÉCIALISÉ - ÉCOLES SUPÉRIEURES MAROCAINES\n"
        context += f"*Source: Documentation officielle des établissements*\n\n"
        
        for part in context_parts:
            context += part['text']
        
        logger.info(f"Contexte construit: {len(context_parts)} chunk(s), {total_length} caractères")
        
        return context
    
    def augment_prompt(self, user_query: str, base_prompt: str) -> str:
        """
        Augmente le prompt avec le contexte pertinent
        
        Args:
            user_query: Question de l'utilisateur
            base_prompt: Prompt système de base
            
        Returns:
            Prompt augmenté avec contexte ou prompt de base si pas de contexte
        """
        context = self.get_context_for_query(user_query)
        
        if context:
            # Prompt avec contexte RAG
            augmented_prompt = f"""{base_prompt}

# MODE RAG ACTIVÉ - INFORMATIONS SPÉCIALISÉES DISPONIBLES

{context}

## INSTRUCTIONS IMPORTANTES:
- Tu as accès à des informations OFFICIELLES et DÉTAILLÉES sur les écoles supérieures marocaines
- Utilise PRIORITAIREMENT ces informations pour répondre aux questions sur les établissements mentionnés
- Ces données sont plus récentes et précises que tes connaissances générales
- Cite toujours les sources quand tu utilises ces informations (ex: "Selon la documentation officielle de l'ENSA...")
- Si les informations du contexte ne couvrent pas entièrement la question, combine-les avec tes connaissances générales en précisant la différence
- Reste dans ton rôle de Dr. Karima Benjelloun mais utilise ces données spécialisées

## PRIORITÉ D'INFORMATION:
1. Contexte spécialisé ci-dessus (PRIORITÉ HAUTE)
2. Tes connaissances générales du système éducatif marocain (PRIORITÉ NORMALE)
3. Si aucune information disponible, indique-le clairement et suggère de vérifier sur les sites officiels

"""
            logger.info("✅ Prompt augmenté avec contexte RAG")
            return augmented_prompt
        else:
            # Prompt de fallback vers connaissances générales
            fallback_prompt = f"""{base_prompt}

# MODE CONNAISSANCES GÉNÉRALES
*Aucune information spécialisée trouvée dans la base de données pour cette requête*

Tu réponds avec tes connaissances générales du système éducatif marocain en précisant que:
- Ces informations sont basées sur tes connaissances générales
- Il est recommandé de vérifier sur les sites officiels des établissements
- Tu peux aider avec des conseils généraux d'orientation

"""
            logger.info("📚 Fallback vers connaissances générales LLM")
            return fallback_prompt
    
    def _preprocess_query(self, query: str) -> str:
        """
        Préprocesse la requête pour améliorer la recherche
        
        Args:
            query: Requête brute
            
        Returns:
            Requête préprocessée
        """
        # Normaliser le texte
        query = query.lower().strip()
        
        # Remplacer les abréviations courantes
        abbreviations = {
            'ensa': 'école nationale des sciences appliquées',
            'emsi': 'école marocaine des sciences de l\'ingénieur',
            'ensam': 'école nationale supérieure d\'arts et métiers',
            'emi': 'école mohammadia d\'ingénieurs',
            'ensias': 'école nationale supérieure d\'informatique et d\'analyse des systèmes',
            'encg': 'école nationale de commerce et de gestion',
            'fsjes': 'faculté des sciences juridiques économiques et sociales',
            'fst': 'faculté des sciences et techniques',
            'est': 'école supérieure de technologie',
        }
        
        for abbrev, full_name in abbreviations.items():
            query = re.sub(r'\b' + abbrev + r'\b', full_name, query)
        
        return query
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du système RAG"""
        return {
            'vector_store_stats': self.vector_store.get_stats(),
            'pdf_folder': str(self.pdf_folder),
            'pdf_files_count': len(list(self.pdf_folder.glob("*.pdf"))) if self.pdf_folder.exists() else 0,
            'ml_available': self.vector_store.ml_available,
            'config': {
                'chunk_size': self.pdf_processor.chunk_size,
                'chunk_overlap': self.pdf_processor.chunk_overlap,
                'max_context_chunks': self.max_context_chunks,
                'min_relevance_score': self.min_relevance_score,
                'context_window_size': self.context_window_size
            }
        }
    
    def rebuild_knowledge_base(self) -> bool:
        """Force la reconstruction complète de la base de connaissances"""
        logger.info("🔄 Reconstruction de la base de connaissances...")
        return self.initialize_knowledge_base(force_rebuild=True)