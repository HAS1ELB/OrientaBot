#!/usr/bin/env python3
"""
Script pour combiner tous les PDFs d'écoles en un seul document pour le RAG
"""

import os
import sys
from pathlib import Path
from PyPDF2 import PdfMerger
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def combine_pdfs(pdf_folder="pdfs", output_folder="data", output_filename="ecoles_maroc_combined.pdf"):
    """
    Combine tous les PDFs présents dans le dossier pdf_folder en un seul PDF
    
    Args:
        pdf_folder (str): Dossier contenant les PDFs à combiner
        output_folder (str): Dossier de sortie pour le PDF combiné
        output_filename (str): Nom du fichier PDF combiné
    
    Returns:
        bool: True si la combinaison a réussi, False sinon
    """
    
    # Chemins absolus
    script_dir = Path(__file__).parent
    pdf_dir = script_dir / pdf_folder
    output_dir = script_dir / output_folder
    output_path = output_dir / output_filename
    
    # Vérifier que le dossier des PDFs existe
    if not pdf_dir.exists():
        logger.error(f"Le dossier {pdf_dir} n'existe pas")
        return False
    
    # Créer le dossier de sortie s'il n'existe pas
    output_dir.mkdir(exist_ok=True)
    
    # Trouver tous les fichiers PDF
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"Aucun fichier PDF trouvé dans {pdf_dir}")
        return False
    
    logger.info(f"Trouvé {len(pdf_files)} fichier(s) PDF à combiner:")
    for pdf_file in sorted(pdf_files):
        logger.info(f"  - {pdf_file.name}")
    
    try:
        # Créer le merger
        merger = PdfMerger()
        
        # Ajouter chaque PDF au merger
        for pdf_file in sorted(pdf_files):
            logger.info(f"Ajout de {pdf_file.name}...")
            
            try:
                merger.append(str(pdf_file))
            except Exception as e:
                logger.error(f"Erreur lors de l'ajout de {pdf_file.name}: {e}")
                continue
        
        # Sauvegarder le PDF combiné
        logger.info(f"Sauvegarde du PDF combiné: {output_path}")
        with open(output_path, 'wb') as output_file:
            merger.write(output_file)
        
        merger.close()
        
        # Vérifier que le fichier a été créé
        if output_path.exists():
            file_size = output_path.stat().st_size / 1024  # Taille en KB
            logger.info(f"✅ PDF combiné créé avec succès!")
            logger.info(f"   📁 Fichier: {output_path}")
            logger.info(f"   📊 Taille: {file_size:.1f} KB")
            logger.info(f"   📚 Sources: {len(pdf_files)} PDF(s)")
            return True
        else:
            logger.error("❌ Le fichier de sortie n'a pas été créé")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la combinaison des PDFs: {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("🚀 Début de la combinaison des PDFs des écoles")
    logger.info("=" * 50)
    
    success = combine_pdfs()
    
    logger.info("=" * 50)
    if success:
        logger.info("✅ Combinaison terminée avec succès!")
        logger.info("📄 Le PDF combiné est prêt pour le système RAG.")
    else:
        logger.error("❌ Échec de la combinaison des PDFs")
        sys.exit(1)

if __name__ == "__main__":
    main()