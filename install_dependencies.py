"""Script d'installation automatique des dépendances."""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire app au path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.dependencies_checker import DependenciesChecker
from app.core.logging import get_logger

logger = get_logger(__name__)


async def main() -> None:
    """Fonction principale."""
    print("=" * 60)
    print("Installation des dépendances pour Extracteur de Données")
    print("=" * 60)
    print()

    checker = DependenciesChecker()
    success = await checker.check_and_install_all()

    print()
    if success:
        print("✓ Toutes les dépendances sont installées et prêtes !")
        print()
        print("Vous pouvez maintenant démarrer l'application avec :")
        print("  uvicorn app.main:app --reload")
    else:
        print("⚠ Certaines dépendances n'ont pas pu être installées automatiquement.")
        print("Veuillez consulter les logs ci-dessus pour plus de détails.")
        print()
        print("Installation manuelle :")
        print("  1. pip install -r requirements/base.txt")
        print("  2. python -m spacy download fr_core_news_md")
        print("  3. Installer Tesseract OCR (voir README.md)")

    print()


if __name__ == "__main__":
    asyncio.run(main())

