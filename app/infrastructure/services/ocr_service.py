"""Service OCR réutilisable pour l'extraction de texte depuis des images."""

import asyncio
import os
import platform
import shutil
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

import pytesseract
from PIL import Image

from app.config import get_settings
from app.core.logging import get_logger
from app.infrastructure.services.image_preprocessor import ImagePreprocessor
from app.infrastructure.services.ocr_corrector import OcrCorrector

logger = get_logger(__name__)
settings = get_settings()


class OcrService:
    """Service OCR pour extraire le texte depuis des images avec Tesseract."""

    def __init__(
        self,
        tesseract_cmd: Optional[str] = None,
        use_advanced_preprocessing: bool = True,
        use_correction: bool = True,
        multi_attempt: bool = True,
    ) -> None:
        """
        Initialiser le service OCR.

        Args:
            tesseract_cmd: Chemin vers l'exécutable Tesseract (optionnel)
            use_advanced_preprocessing: Utiliser le preprocessing avancé (défaut: True)
            use_correction: Utiliser la correction post-OCR (défaut: True)
            multi_attempt: Essayer plusieurs configurations (défaut: True)
        """
        self.logger = logger
        self._tesseract_available: Optional[bool] = None
        self.use_advanced_preprocessing = use_advanced_preprocessing
        self.use_correction = use_correction
        self.multi_attempt = multi_attempt
        
        # Initialiser les services
        if self.use_advanced_preprocessing:
            self.image_preprocessor = ImagePreprocessor()
        else:
            self.image_preprocessor = None
            
        if self.use_correction:
            self.ocr_corrector = OcrCorrector()
        else:
            self.ocr_corrector = None
        
        # Vérifier d'abord si pytesseract est déjà configuré (par DependenciesChecker)
        existing_cmd = getattr(pytesseract.pytesseract, 'tesseract_cmd', None)
        if existing_cmd and Path(existing_cmd).exists():
            self._tesseract_cmd = existing_cmd
            self.logger.debug(f"Utilisation du chemin Tesseract déjà configuré: {existing_cmd}")
        else:
            # Sinon, utiliser le paramètre fourni ou celui des settings
            self._tesseract_cmd = tesseract_cmd or settings.tesseract_cmd
            
            # Si aucun chemin n'est fourni, essayer de détecter automatiquement
            if not self._tesseract_cmd:
                self._tesseract_cmd = self._find_tesseract()

        # Configurer le chemin Tesseract si trouvé
        if self._tesseract_cmd:
            try:
                # S'assurer que c'est le chemin complet vers l'exécutable
                tesseract_path = Path(self._tesseract_cmd)
                if platform.system() == "Windows":
                    # Si c'est un dossier, chercher tesseract.exe dedans
                    if tesseract_path.is_dir():
                        potential_exe = tesseract_path / "tesseract.exe"
                        if potential_exe.exists():
                            self._tesseract_cmd = str(potential_exe)
                            tesseract_path = Path(self._tesseract_cmd)
                    # Vérifier que le fichier existe et est un exécutable
                    elif not tesseract_path.exists() or not tesseract_path.name.endswith(".exe"):
                        # Essayer de trouver tesseract.exe dans le même dossier
                        if tesseract_path.parent.exists():
                            potential_exe = tesseract_path.parent / "tesseract.exe"
                            if potential_exe.exists():
                                self._tesseract_cmd = str(potential_exe)
                                tesseract_path = Path(self._tesseract_cmd)
                
                # Vérifier que le fichier existe avant de configurer
                if not tesseract_path.exists():
                    self.logger.warning(
                        f"Le chemin Tesseract n'existe pas: {self._tesseract_cmd}, "
                        "tentative de détection automatique"
                    )
                    self._tesseract_cmd = self._find_tesseract()
                    if self._tesseract_cmd:
                        tesseract_path = Path(self._tesseract_cmd)
                
                if tesseract_path.exists():
                    pytesseract.pytesseract.tesseract_cmd = str(tesseract_path)
                    self.logger.info(f"Tesseract configuré: {tesseract_path}")
                else:
                    self.logger.warning("Impossible de trouver l'exécutable Tesseract")
            except Exception as e:
                self.logger.warning(f"Impossible de configurer le chemin Tesseract: {e}")

    def _find_tesseract(self) -> Optional[str]:
        """
        Détecter automatiquement l'emplacement de Tesseract.

        Returns:
            Chemin vers l'exécutable Tesseract ou None si non trouvé
        """
        # Vérifier d'abord si tesseract est dans le PATH
        tesseract_path = shutil.which("tesseract")
        if tesseract_path:
            self.logger.debug(f"Tesseract trouvé dans PATH: {tesseract_path}")
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
                    self.logger.debug(f"Tesseract trouvé: {path}")
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
                    self.logger.debug(f"Tesseract trouvé: {path}")
                    return path

        self.logger.debug("Tesseract non trouvé automatiquement")
        return None

    async def is_available(self) -> bool:
        """
        Vérifier si Tesseract OCR est disponible.

        Returns:
            True si Tesseract est disponible, False sinon
        """
        if self._tesseract_available is not None:
            return self._tesseract_available

        # Si aucun chemin n'a été configuré, essayer de le trouver
        if not self._tesseract_cmd:
            found_path = self._find_tesseract()
            if found_path:
                self._tesseract_cmd = found_path
                try:
                    pytesseract.pytesseract.tesseract_cmd = found_path
                    self.logger.info(f"Tesseract détecté automatiquement: {found_path}")
                except Exception as e:
                    self.logger.warning(f"Impossible de configurer Tesseract: {e}")

        try:
            loop = asyncio.get_event_loop()
            version = await loop.run_in_executor(
                None, pytesseract.get_tesseract_version
            )
            self._tesseract_available = version is not None
            if self._tesseract_available:
                self.logger.info(
                    f"Tesseract OCR disponible (version: {version})"
                )
            else:
                self.logger.warning("Tesseract OCR non disponible")
            return self._tesseract_available
        except Exception as e:
            self.logger.warning(f"Tesseract OCR non disponible: {e}")
            # Si l'erreur indique que le chemin n'est pas trouvé, essayer de le détecter
            if "tesseract" in str(e).lower() or "not found" in str(e).lower():
                if not self._tesseract_cmd:
                    found_path = self._find_tesseract()
                    if found_path:
                        self._tesseract_cmd = found_path
                        try:
                            pytesseract.pytesseract.tesseract_cmd = found_path
                            # Réessayer après avoir configuré le chemin
                            version = await loop.run_in_executor(
                                None, pytesseract.get_tesseract_version
                            )
                            self._tesseract_available = version is not None
                            if self._tesseract_available:
                                self.logger.info(
                                    f"Tesseract détecté et configuré: {found_path} (version: {version})"
                                )
                            return self._tesseract_available
                        except Exception as e2:
                            self.logger.debug(f"Échec après détection automatique: {e2}")

            self._tesseract_available = False
            return False

    async def extract_text(
        self, image_data: bytes, lang: str = "fra+eng"
    ) -> Tuple[str, float]:
        """
        Extraire le texte d'une image avec OCR (amélioré avec multi-tentatives).

        Args:
            image_data: Données binaires de l'image
            lang: Langues à utiliser pour l'OCR (défaut: fra+eng)

        Returns:
            Tuple contenant le texte extrait et le niveau de confiance (0.0-1.0)

        Raises:
            ValueError: Si Tesseract n'est pas disponible
            RuntimeError: Si l'extraction échoue
        """
        if not await self.is_available():
            raise ValueError(
                "Tesseract OCR n'est pas disponible. "
                "Veuillez installer Tesseract pour utiliser cette fonctionnalité."
            )

        try:
            loop = asyncio.get_event_loop()
            if self.multi_attempt:
                result = await loop.run_in_executor(
                    None, self._extract_text_multi_attempt, image_data, lang
                )
            else:
                result = await loop.run_in_executor(
                    None, self._extract_text_sync, image_data, lang
                )
            return result
        except Exception as e:
            self.logger.exception(f"Erreur lors de l'extraction OCR: {e}")
            raise RuntimeError(f"Échec de l'extraction OCR: {str(e)}") from e

    def _extract_text_multi_attempt(
        self, image_data: bytes, lang: str
    ) -> Tuple[str, float]:
        """
        Extraction avec plusieurs tentatives pour obtenir le meilleur résultat.

        Args:
            image_data: Données binaires de l'image
            lang: Langues à utiliser

        Returns:
            Tuple (texte, confiance) du meilleur résultat
        """
        # Charger l'image originale
        original_image = Image.open(BytesIO(image_data))

        # PSM modes à tester (Page Segmentation Modes)
        # 3 = Segmentation automatique complète (défaut)
        # 6 = Bloc uniforme de texte
        # 11 = Texte dense
        # 12 = Texte avec OSD (Orientation and Script Detection)
        psm_modes = [6, 11, 3, 12] if self.multi_attempt else [3]

        # Méthodes de preprocessing à tester
        preprocessing_methods = (
            ["advanced", "aggressive", "basic"]
            if self.use_advanced_preprocessing
            else ["basic"]
        )

        results: list[Tuple[str, float, dict]] = []

        # Essayer différentes combinaisons
        for preprocess_method in preprocessing_methods:
            # Préprocesser l'image
            if self.use_advanced_preprocessing and self.image_preprocessor:
                processed_image = self.image_preprocessor.preprocess(
                    original_image.copy(), method=preprocess_method
                )
            else:
                processed_image = self._preprocess_image_basic(original_image.copy())

            # Essayer chaque PSM mode
            for psm in psm_modes:
                try:
                    # Configuration Tesseract
                    config = f"--psm {psm} --oem 3"  # OEM 3 = LSTM OCR Engine

                    # Extraire le texte
                    ocr_text = pytesseract.image_to_string(
                        processed_image, lang=lang, config=config
                    )
                    ocr_data = pytesseract.image_to_data(
                        processed_image,
                        output_type=pytesseract.Output.DICT,
                        lang=lang,
                        config=config,
                    )

                    # Calculer la confiance
                    confidences = [
                        int(conf) for conf in ocr_data.get("conf", []) if conf != "-1"
                    ]
                    avg_confidence = (
                        sum(confidences) / len(confidences) / 100.0
                        if confidences
                        else 0.0
                    )

                    # Nettoyer le texte
                    text = ocr_text.strip() if ocr_text else ""

                    if text:
                        results.append(
                            (
                                text,
                                avg_confidence,
                                {"psm": psm, "preprocess": preprocess_method},
                            )
                        )
                except Exception as e:
                    self.logger.debug(
                        f"Erreur avec PSM {psm} et preprocessing {preprocess_method}: {e}"
                    )
                    continue

        # Si aucun résultat, essayer sans preprocessing
        if not results:
            try:
                ocr_text = pytesseract.image_to_string(original_image, lang=lang)
                ocr_data = pytesseract.image_to_data(
                    original_image, output_type=pytesseract.Output.DICT, lang=lang
                )
                confidences = [
                    int(conf) for conf in ocr_data.get("conf", []) if conf != "-1"
                ]
                avg_confidence = (
                    sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
                )
                text = ocr_text.strip() if ocr_text else ""
                if text:
                    results.append((text, avg_confidence, {"psm": 3, "preprocess": "none"}))
            except Exception as e:
                self.logger.warning(f"Erreur lors de l'extraction de base: {e}")

        if not results:
            return "", 0.0

        # Choisir le meilleur résultat (par confiance, puis par longueur de texte)
        results.sort(key=lambda x: (x[1], len(x[0])), reverse=True)
        best_text, best_confidence, best_config = results[0]

        self.logger.debug(
            f"Meilleur résultat OCR: confiance={best_confidence:.2f}, "
            f"config={best_config}, longueur={len(best_text)}"
        )

        # Appliquer la correction post-OCR si activée
        if self.use_correction and self.ocr_corrector:
            corrected_text, adjusted_confidence = self.ocr_corrector.correct_with_confidence(
                best_text, best_confidence
            )
            return corrected_text, adjusted_confidence

        return best_text, best_confidence

    def _extract_text_sync(self, image_data: bytes, lang: str) -> Tuple[str, float]:
        """Extraction synchrone du texte (méthode simple, sans multi-tentatives)."""
        # Charger l'image depuis les bytes
        image = Image.open(BytesIO(image_data))

        # Préprocesser l'image
        if self.use_advanced_preprocessing and self.image_preprocessor:
            processed_image = self.image_preprocessor.preprocess(image, method="advanced")
        else:
            processed_image = self._preprocess_image_basic(image)

        # Extraire le texte avec OCR
        try:
            config = "--psm 6 --oem 3"  # PSM 6 pour texte uniforme, OEM 3 pour LSTM
            ocr_text = pytesseract.image_to_string(
                processed_image, lang=lang, config=config
            )
            ocr_data = pytesseract.image_to_data(
                processed_image,
                output_type=pytesseract.Output.DICT,
                lang=lang,
                config=config,
            )
        except Exception as e:
            self.logger.warning(
                f"Erreur OCR avec preprocessing: {e}, tentative sans preprocessing"
            )
            # Fallback: essayer sans preprocessing
            ocr_text = pytesseract.image_to_string(image, lang=lang)
            ocr_data = pytesseract.image_to_data(
                image, output_type=pytesseract.Output.DICT, lang=lang
            )

        # Calculer la confiance moyenne
        confidences = [
            int(conf) for conf in ocr_data.get("conf", []) if conf != "-1"
        ]
        avg_confidence = (
            sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
        )

        # Nettoyer le texte
        text = ocr_text.strip() if ocr_text else ""

        # Appliquer la correction si activée
        if self.use_correction and self.ocr_corrector:
            text, avg_confidence = self.ocr_corrector.correct_with_confidence(
                text, avg_confidence
            )

        return text, avg_confidence

    def _preprocess_image_basic(self, image: Image.Image) -> Image.Image:
        """
        Préprocesser l'image de manière basique (fallback).

        Args:
            image: Image PIL à préprocesser

        Returns:
            Image préprocessée
        """
        from PIL import ImageEnhance, ImageFilter

        # Convertir en niveaux de gris si nécessaire
        if image.mode != "L":
            image = image.convert("L")

        # Améliorer le contraste
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Améliorer la netteté
        image = image.filter(ImageFilter.SHARPEN)

        # Réduire le bruit (débruitage)
        image = image.filter(ImageFilter.MedianFilter(size=3))

        return image

    async def extract_text_from_file(
        self, file_path: str, lang: str = "fra+eng"
    ) -> Tuple[str, float]:
        """
        Extraire le texte d'un fichier image avec OCR.

        Args:
            file_path: Chemin vers le fichier image
            lang: Langues à utiliser pour l'OCR (défaut: fra+eng)

        Returns:
            Tuple contenant le texte extrait et le niveau de confiance (0.0-1.0)
        """
        with open(file_path, "rb") as f:
            image_data = f.read()
        return await self.extract_text(image_data, lang=lang)

