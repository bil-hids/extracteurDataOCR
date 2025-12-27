"""Extracteur d'images avec Tesseract OCR."""

import asyncio
from pathlib import Path
from typing import Any

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

from app.core.exceptions import ExtractionFailedError
from app.core.logging import get_logger
from app.domain.value_objects.content_metadata import ContentMetadata
from app.domain.value_objects.extraction_result import ExtractionResult, ImageBlock, TextBlock
from app.infrastructure.extractors.base import BaseExtractor


class OcrExtractor(BaseExtractor):
    """Extracteur d'images avec Tesseract OCR et preprocessing."""

    def __init__(self, tesseract_cmd: str | None = None, logger: Any = None) -> None:
        """Initialiser l'extracteur."""
        super().__init__(logger or get_logger(__name__))
        
        # Si un chemin est fourni, l'utiliser
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        # Sinon, vérifier si Tesseract est déjà configuré globalement
        elif not hasattr(pytesseract.pytesseract, 'tesseract_cmd') or not pytesseract.pytesseract.tesseract_cmd:
            # Essayer de détecter automatiquement
            from app.infrastructure.services.ocr_service import OcrService
            ocr_service = OcrService()
            # La détection se fera lors de is_available() si nécessaire

    async def extract(self, file_path: str) -> ExtractionResult:
        """Extraire le texte d'une image avec OCR."""
        self._validate_file(file_path)

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._extract_sync, file_path)
            return result
        except Exception as e:
            self.logger.exception(f"Erreur lors de l'extraction OCR: {e}")
            raise ExtractionFailedError(f"Échec de l'extraction OCR: {str(e)}")

    def _extract_sync(self, file_path: str) -> ExtractionResult:
        """Extraction synchrone."""
        # Charger et préprocesser l'image
        image = Image.open(file_path)
        processed_image = self._preprocess_image(image)

        # Extraire le texte avec OCR
        try:
            ocr_text = pytesseract.image_to_string(processed_image, lang="fra+eng")
            ocr_data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
        except Exception as e:
            self.logger.warning(f"Erreur OCR: {e}, tentative sans preprocessing")
            ocr_text = pytesseract.image_to_string(image, lang="fra+eng")
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        # Calculer la confiance moyenne
        confidences = [int(conf) for conf in ocr_data.get("conf", []) if conf != "-1"]
        avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0

        # Créer les blocs
        text_blocks: list[TextBlock] = []
        if ocr_text and ocr_text.strip():
            metadata = ContentMetadata(
                order=0,
                extraction_method="tesseract_ocr",
                confidence=avg_confidence,
                additional_metadata={
                    "image_path": str(file_path),
                    "image_size": image.size,
                    "image_format": image.format,
                },
            )
            text_blocks.append(TextBlock(content=ocr_text.strip(), metadata=metadata))

        # Créer un bloc image avec le texte OCR
        image_blocks: list[ImageBlock] = []
        with open(file_path, "rb") as f:
            image_data = f.read()

        metadata = ContentMetadata(
            order=0,
            extraction_method="tesseract_ocr",
            confidence=avg_confidence,
        )
        image_blocks.append(
            ImageBlock(
                image_path=str(file_path),
                image_data=image_data,
                ocr_text=ocr_text.strip() if ocr_text else None,
                metadata=metadata,
            )
        )

        return ExtractionResult(text_blocks=text_blocks, images=image_blocks)

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Préprocesser l'image pour améliorer l'OCR."""
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

    async def extract_tables(self, file_path: str) -> list[Any]:
        """OCR peut détecter des tableaux mais c'est complexe."""
        return []

    async def extract_images(self, file_path: str) -> list[Any]:
        """Extraire l'image avec texte OCR."""
        result = await self.extract(file_path)
        return result.images

    def supports(self, file_type: str) -> bool:
        """Vérifier si le type d'image est supporté."""
        return file_type in ["image/png", "image/jpeg", "image/tiff", "image/jpg"]

