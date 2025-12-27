"""Vérification et installation automatique des dépendances."""

import subprocess
import sys
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class DependenciesChecker:
    """Vérificateur et installateur de dépendances."""

    def __init__(self) -> None:
        """Initialiser le vérificateur."""
        self.logger = logger

    async def check_and_install_all(self) -> bool:
        """
        Vérifier et installer toutes les dépendances nécessaires.

        Returns:
            True si tout est OK, False sinon
        """
        self.logger.info("Vérification des dépendances...")

        # Vérifier Python packages
        if not await self._check_python_packages():
            self.logger.warning("Certains packages Python sont manquants")
            if await self._install_python_packages():
                self.logger.info("Packages Python installés")
            else:
                self.logger.error("Échec de l'installation des packages Python")
                return False

        # Vérifier modèle SpaCy
        if not await self._check_spacy_model():
            self.logger.warning("Modèle SpaCy manquant")
            if await self._install_spacy_model():
                self.logger.info("Modèle SpaCy installé")
            else:
                self.logger.error("Échec de l'installation du modèle SpaCy")
                return False

        # Vérifier Tesseract (optionnel mais recommandé)
        if not await self._check_tesseract():
            self.logger.warning(
                "Tesseract OCR n'est pas installé. L'extraction d'images ne fonctionnera pas."
            )
            self.logger.info(
                "Pour installer Tesseract : "
                "Windows: https://github.com/UB-Mannheim/tesseract/wiki | "
                "Linux: sudo apt-get install tesseract-ocr | "
                "macOS: brew install tesseract"
            )

        self.logger.info("Vérification des dépendances terminée")
        return True

    async def _check_python_packages(self) -> bool:
        """Vérifier si les packages Python essentiels sont installés."""
        essential_packages = [
            ("fastapi", "fastapi"),
            ("uvicorn", "uvicorn"),
            ("pydantic", "pydantic"),
            ("sqlalchemy", "sqlalchemy"),
            ("pdfplumber", "pdfplumber"),
            ("fitz", "PyMuPDF"),  # PyMuPDF s'importe comme fitz
            ("openpyxl", "openpyxl"),
            ("docx", "python-docx"),  # python-docx s'importe comme docx
            ("spacy", "spacy"),
            ("pytesseract", "pytesseract"),
            ("PIL", "Pillow"),  # Pillow s'importe comme PIL
        ]

        missing = []
        for import_name, package_name in essential_packages:
            try:
                __import__(import_name)
            except ImportError:
                missing.append(package_name)

        if missing:
            self.logger.warning(f"Packages manquants: {', '.join(missing)}")
            return False

        return True

    async def _install_python_packages(self) -> bool:
        """Installer les packages Python depuis requirements.txt."""
        try:
            requirements_file = Path("requirements/base.txt")
            if not requirements_file.exists():
                self.logger.error("Fichier requirements/base.txt non trouvé")
                return False

            self.logger.info("Installation des packages Python...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                self.logger.info("Packages Python installés avec succès")
                return True
            else:
                self.logger.error(f"Erreur lors de l'installation: {result.stderr}")
                return False

        except Exception as e:
            self.logger.exception(f"Erreur lors de l'installation des packages: {e}")
            return False

    async def _check_spacy_model(self) -> bool:
        """Vérifier si le modèle SpaCy est installé."""
        try:
            import spacy

            model_name = "fr_core_news_md"
            try:
                nlp = spacy.load(model_name)
                self.logger.info(f"Modèle SpaCy '{model_name}' trouvé")
                return True
            except OSError:
                self.logger.warning(f"Modèle SpaCy '{model_name}' non trouvé")
                return False

        except ImportError:
            self.logger.warning("SpaCy n'est pas installé")
            return False

    async def _install_spacy_model(self) -> bool:
        """Installer le modèle SpaCy français."""
        try:
            self.logger.info("Installation du modèle SpaCy français...")
            result = subprocess.run(
                [sys.executable, "-m", "spacy", "download", "fr_core_news_md"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                self.logger.info("Modèle SpaCy installé avec succès")
                return True
            else:
                self.logger.error(f"Erreur lors de l'installation: {result.stderr}")
                return False

        except Exception as e:
            self.logger.exception(f"Erreur lors de l'installation du modèle: {e}")
            return False

    async def _check_tesseract(self) -> bool:
        """Vérifier si Tesseract OCR est installé."""
        try:
            import pytesseract
            import platform
            import os
            import shutil
            from pathlib import Path

            # Essayer d'abord avec la configuration actuelle
            try:
                version = pytesseract.get_tesseract_version()
                if version:
                    self.logger.info(f"Tesseract OCR trouvé (version: {version})")
                    return True
            except Exception:
                pass

            # Si non trouvé, essayer de détecter automatiquement
            tesseract_path = self._find_tesseract()
            if tesseract_path:
                try:
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    version = pytesseract.get_tesseract_version()
                    if version:
                        self.logger.info(
                            f"Tesseract OCR trouvé automatiquement: {tesseract_path} (version: {version})"
                        )
                        return True
                except Exception as e:
                    self.logger.debug(f"Erreur après détection automatique: {e}")

            return False

        except Exception as e:
            self.logger.debug(f"Tesseract non trouvé: {e}")
            return False

    def _find_tesseract(self) -> str | None:
        """
        Détecter automatiquement l'emplacement de Tesseract.

        Returns:
            Chemin vers l'exécutable Tesseract ou None si non trouvé
        """
        import platform
        import os
        import shutil
        from pathlib import Path

        # Vérifier d'abord si tesseract est dans le PATH
        tesseract_path = shutil.which("tesseract")
        if tesseract_path:
            return tesseract_path

        # Sur Windows, chercher dans les emplacements communs
        if platform.system() == "Windows":
            common_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(
                    os.getenv("USERNAME", "")
                ),
                r"C:\Tesseract-OCR\tesseract.exe",
            ]

            for path in common_paths:
                if Path(path).exists():
                    return path

        # Sur Linux/macOS, chercher dans les emplacements standards
        elif platform.system() in ("Linux", "Darwin"):
            common_paths = [
                "/usr/bin/tesseract",
                "/usr/local/bin/tesseract",
                "/opt/homebrew/bin/tesseract",  # macOS avec Homebrew sur Apple Silicon
            ]

            for path in common_paths:
                if Path(path).exists():
                    return path

        return None


async def check_dependencies_on_startup() -> bool:
    """Vérifier les dépendances au démarrage."""
    checker = DependenciesChecker()
    return await checker.check_and_install_all()

