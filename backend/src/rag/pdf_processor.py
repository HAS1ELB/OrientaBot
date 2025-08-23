"""
Processeur de PDFs pour l'extraction et le chunking de texte pour le RAG
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any
import PyPDF2
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Représente un chunk de document avec métadonnées"""
    content: str
    source: str
    page_number: int
    chunk_id: str
    metadata: Dict[str, Any]

class PDFProcessor:
    """Classe pour traiter les PDFs et extraire le texte"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialise le processeur PDF
        
        Args:
            chunk_size: Taille maximale des chunks en caractères
            chunk_overlap: Chevauchement entre les chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text_from_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extrait le texte de chaque page d'un PDF
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            
        Returns:
            Liste des pages avec leur texte et métadonnées
        """
        pages = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        text = page.extract_text()
                        
                        # Nettoyer le texte
                        cleaned_text = self._clean_text(text)
                        
                        if cleaned_text.strip():  # Ignorer les pages vides
                            pages.append({
                                'page_number': page_num,
                                'text': cleaned_text,
                                'source': pdf_path.name,
                                'full_path': str(pdf_path)
                            })
                    except Exception as e:
                        logger.warning(f"Erreur lors de l'extraction de la page {page_num} de {pdf_path.name}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du PDF {pdf_path}: {e}")
            
        return pages
    
    def _clean_text(self, text: str) -> str:
        """
        Nettoie le texte extrait du PDF
        
        Args:
            text: Texte brut extrait
            
        Returns:
            Texte nettoyé
        """
        if not text:
            return ""
            
        # Supprimer les caractères de contrôle et normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les caractères spéciaux problématiques
        text = re.sub(r'[^\w\s\-\.,;:!?()\[\]{}\"\'àâäéèêëïîôùûüÿçÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ]', '', text)
        
        # Normaliser les tirets et guillemets
        text = text.replace('–', '-').replace('—', '-')
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text.strip()
    
    def create_chunks(self, pages: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """
        Crée des chunks à partir des pages extraites
        
        Args:
            pages: Liste des pages avec texte et métadonnées
            
        Returns:
            Liste des chunks de documents
        """
        chunks = []
        
        for page in pages:
            text = page['text']
            page_num = page['page_number']
            source = page['source']
            
            # Si le texte est plus court que la taille de chunk, créer un seul chunk
            if len(text) <= self.chunk_size:
                chunk = DocumentChunk(
                    content=text,
                    source=source,
                    page_number=page_num,
                    chunk_id=f"{source}_page_{page_num}_chunk_1",
                    metadata={
                        'source_file': source,
                        'page_number': page_num,
                        'chunk_size': len(text),
                        'chunk_index': 1
                    }
                )
                chunks.append(chunk)
            else:
                # Diviser le texte en chunks avec chevauchement
                page_chunks = self._split_text_into_chunks(text)
                
                for i, chunk_text in enumerate(page_chunks, 1):
                    chunk = DocumentChunk(
                        content=chunk_text,
                        source=source,
                        page_number=page_num,
                        chunk_id=f"{source}_page_{page_num}_chunk_{i}",
                        metadata={
                            'source_file': source,
                            'page_number': page_num,
                            'chunk_size': len(chunk_text),
                            'chunk_index': i,
                            'total_chunks_for_page': len(page_chunks)
                        }
                    )
                    chunks.append(chunk)
        
        return chunks
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        Divise un texte en chunks avec chevauchement intelligent
        
        Args:
            text: Texte à diviser
            
        Returns:
            Liste des chunks de texte
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Si on n'est pas à la fin du texte, essayer de couper à un point naturel
            if end < len(text):
                # Chercher la dernière phrase complète dans le chunk
                last_sentence_end = text.rfind('.', start, end)
                if last_sentence_end > start:
                    end = last_sentence_end + 1
                else:
                    # Chercher le dernier espace
                    last_space = text.rfind(' ', start, end)
                    if last_space > start:
                        end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Calculer le début du prochain chunk avec chevauchement
            start = max(start + self.chunk_size - self.chunk_overlap, end)
            
            # Éviter les boucles infinies
            if start >= len(text):
                break
        
        return chunks
    
    def process_pdf_file(self, pdf_path: Path) -> List[DocumentChunk]:
        """
        Traite un fichier PDF complet et retourne les chunks
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            
        Returns:
            Liste des chunks du document
        """
        logger.info(f"Traitement du PDF: {pdf_path.name}")
        
        # Extraire le texte de toutes les pages
        pages = self.extract_text_from_pdf(pdf_path)
        
        if not pages:
            logger.warning(f"Aucune page extraite du PDF: {pdf_path.name}")
            return []
        
        logger.info(f"  - {len(pages)} page(s) extraite(s)")
        
        # Créer les chunks
        chunks = self.create_chunks(pages)
        
        logger.info(f"  - {len(chunks)} chunk(s) créé(s)")
        
        return chunks
    
    def process_all_pdfs(self, pdf_folder: Path) -> List[DocumentChunk]:
        """
        Traite tous les PDFs dans un dossier
        
        Args:
            pdf_folder: Dossier contenant les PDFs
            
        Returns:
            Liste de tous les chunks de tous les documents
        """
        all_chunks = []
        pdf_files = list(pdf_folder.glob("*.pdf"))
        
        logger.info(f"Traitement de {len(pdf_files)} fichier(s) PDF...")
        
        for pdf_file in sorted(pdf_files):
            chunks = self.process_pdf_file(pdf_file)
            all_chunks.extend(chunks)
        
        logger.info(f"Total: {len(all_chunks)} chunk(s) créé(s) depuis {len(pdf_files)} PDF(s)")
        
        return all_chunks