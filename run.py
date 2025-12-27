"""Script de démarrage simplifié de l'application."""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire au path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.dependencies_checker import DependenciesChecker
from app.core.logging import get_logger

logger = get_logger(__name__)


async def check_dependencies() -> bool:
    """Vérifier les dépendances avant de démarrer."""
    print("\n" + "=" * 60)
    print("Vérification des dépendances...")
    print("=" * 60 + "\n")

    checker = DependenciesChecker()
    success = await checker.check_and_install_all()

    if success:
        print("\n✓ Toutes les dépendances sont prêtes !\n")
    else:
        print("\n⚠ Certaines dépendances sont manquantes.")
        print("L'application va démarrer mais certaines fonctionnalités peuvent ne pas fonctionner.\n")

    return True  # On continue même si certaines dépendances manquent


if __name__ == "__main__":
    # Vérifier les dépendances
    asyncio.run(check_dependencies())

    # Démarrer l'application
    print("Démarrage de l'application...\n")
    
    try:
        import uvicorn
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    except ImportError:
        print("ERREUR: uvicorn n'est pas installé")
        print("Veuillez exécuter: pip install -r requirements/base.txt")
        sys.exit(1)

