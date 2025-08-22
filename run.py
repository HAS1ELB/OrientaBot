#!/usr/bin/env python3
"""
Script de lancement pour OrientaBot avec la nouvelle structure
"""

import sys
from pathlib import Path

# Ajouter le dossier src au PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

# Importer et lancer l'application principale
if __name__ == "__main__":
    from main import main
    main()