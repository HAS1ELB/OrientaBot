"""
Gestionnaire de base vectorielle pour la recherche sémantique dans le RAG
"""

import os
import json
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from .pdf_processor import DocumentChunk

logger = logging.getLogger(__name__)

class VectorStore:
    """Gestionnaire de base vectorielle avec FAISS et sentence-transformers"""
    
    def __init__(self, 
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 vector_db_path: str = "vector_db"):
        """
        Initialise le store vectoriel
        
        Args:
            embedding_model: Modèle d'embeddings à utiliser
            vector_db_path: Chemin vers le dossier de la base vectorielle
        """
        self.embedding_model_name = embedding_model
        self.vector_db_path = Path(vector_db_path)
        self.vector_db_path.mkdir(exist_ok=True)
        
        # Fichiers de persistance
        self.index_path = self.vector_db_path / "faiss_index.bin"
        self.chunks_path = self.vector_db_path / "chunks.pkl"
        self.metadata_path = self.vector_db_path / "metadata.json"
        
        # Initialiser le modèle d'embeddings
        self._load_embedding_model()
        
        # Charger la base existante si elle existe
        self.index = None
        self.chunks = []
        self.metadata = {}
        
        if self._database_exists():
            self.load_database()
    
    def _load_embedding_model(self):
        """Charge le modèle d'embeddings"""
        try:
            logger.info(f"Chargement du modèle d'embeddings: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
            logger.info(f"Dimension des embeddings: {self.embedding_dimension}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle d'embeddings: {e}")
            raise
    
    def _database_exists(self) -> bool:
        """Vérifie si une base vectorielle existe déjà"""
        return (self.index_path.exists() and 
                self.chunks_path.exists() and 
                self.metadata_path.exists())
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Crée des embeddings pour une liste de textes
        
        Args:
            texts: Liste des textes à encoder
            
        Returns:
            Array numpy des embeddings
        """
        try:
            embeddings = self.embedding_model.encode(
                texts, 
                show_progress_bar=True,
                normalize_embeddings=True
            )
            return embeddings
        except Exception as e:
            logger.error(f"Erreur lors de la création des embeddings: {e}")
            raise
    
    def build_index(self, chunks: List[DocumentChunk]) -> None:
        """
        Construit l'index vectoriel à partir des chunks
        
        Args:
            chunks: Liste des chunks de documents
        """
        if not chunks:
            logger.warning("Aucun chunk fourni pour construire l'index")
            return
        
        logger.info(f"Construction de l'index vectoriel avec {len(chunks)} chunks...")
        
        # Extraire les textes
        texts = [chunk.content for chunk in chunks]
        
        # Créer les embeddings
        logger.info("Création des embeddings...")
        embeddings = self.create_embeddings(texts)
        
        # Créer l'index FAISS
        logger.info("Construction de l'index FAISS...")
        self.index = faiss.IndexFlatIP(self.embedding_dimension)  # Inner Product pour similarité cosine
        self.index.add(embeddings.astype('float32'))
        
        # Stocker les chunks
        self.chunks = chunks
        
        # Créer les métadonnées
        from datetime import datetime
        self.metadata = {
            'total_chunks': len(chunks),
            'embedding_model': self.embedding_model_name,
            'embedding_dimension': self.embedding_dimension,
            'sources': list(set(chunk.source for chunk in chunks)),
            'creation_time': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Index vectoriel créé avec {len(chunks)} chunks")
        logger.info(f"📁 Sources: {', '.join(self.metadata['sources'])}")
    
    def save_database(self) -> None:
        """Sauvegarde la base vectorielle sur disque"""
        try:
            logger.info("Sauvegarde de la base vectorielle...")
            
            # Sauvegarder l'index FAISS
            if self.index is not None:
                faiss.write_index(self.index, str(self.index_path))
            
            # Sauvegarder les chunks
            with open(self.chunks_path, 'wb') as f:
                pickle.dump(self.chunks, f)
            
            # Sauvegarder les métadonnées
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            
            logger.info("✅ Base vectorielle sauvegardée")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            raise
    
    def load_database(self) -> None:
        """Charge la base vectorielle depuis le disque"""
        try:
            logger.info("Chargement de la base vectorielle existante...")
            
            # Charger l'index FAISS
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
            
            # Charger les chunks
            if self.chunks_path.exists():
                with open(self.chunks_path, 'rb') as f:
                    self.chunks = pickle.load(f)
            
            # Charger les métadonnées
            if self.metadata_path.exists():
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            
            logger.info(f"✅ Base vectorielle chargée: {len(self.chunks)} chunks")
            if self.metadata.get('sources'):
                logger.info(f"📁 Sources: {', '.join(self.metadata['sources'])}")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement: {e}")
            raise
    
    def search(self, query: str, top_k: int = 5, score_threshold: float = 0.5) -> List[Tuple[DocumentChunk, float]]:
        """
        Recherche sémantique dans la base vectorielle
        
        Args:
            query: Requête de recherche
            top_k: Nombre de résultats à retourner
            score_threshold: Score minimum pour les résultats
            
        Returns:
            Liste des chunks trouvés avec leurs scores
        """
        if self.index is None or not self.chunks:
            logger.warning("Base vectorielle non initialisée")
            return []
        
        try:
            # Créer l'embedding de la requête
            query_embedding = self.create_embeddings([query])
            
            # Rechercher dans l'index
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
            
            # Filtrer et formater les résultats
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if score >= score_threshold and idx < len(self.chunks):
                    chunk = self.chunks[idx]
                    results.append((chunk, float(score)))
            
            logger.info(f"Recherche pour '{query[:50]}...': {len(results)} résultat(s)")
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la base vectorielle"""
        stats = {
            'total_chunks': len(self.chunks),
            'index_size': self.index.ntotal if self.index else 0,
            'embedding_dimension': self.embedding_dimension,
            'sources': self.metadata.get('sources', []),
            'database_exists': self._database_exists()
        }
        
        if self.chunks:
            # Statistiques sur les chunks
            chunk_sizes = [len(chunk.content) for chunk in self.chunks]
            stats.update({
                'avg_chunk_size': np.mean(chunk_sizes),
                'min_chunk_size': np.min(chunk_sizes),
                'max_chunk_size': np.max(chunk_sizes)
            })
        
        return stats
    
    def rebuild_index(self, chunks: List[DocumentChunk]) -> None:
        """Reconstruit complètement l'index vectoriel"""
        logger.info("Reconstruction complète de l'index vectoriel...")
        
        # Supprimer l'ancienne base
        self.clear_database()
        
        # Construire la nouvelle base
        self.build_index(chunks)
        
        # Sauvegarder
        self.save_database()
        
        logger.info("✅ Index vectoriel reconstruit")
    
    def clear_database(self) -> None:
        """Supprime la base vectorielle"""
        logger.info("Suppression de la base vectorielle...")
        
        # Supprimer les fichiers
        for file_path in [self.index_path, self.chunks_path, self.metadata_path]:
            if file_path.exists():
                file_path.unlink()
        
        # Réinitialiser les variables
        self.index = None
        self.chunks = []
        self.metadata = {}
        
        logger.info("✅ Base vectorielle supprimée")