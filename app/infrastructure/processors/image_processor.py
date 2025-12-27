"""Processeur d'images."""

from pathlib import Path
from typing import Any, Optional

from PIL import Image

from app.core.logging import get_logger
from app.domain.value_objects.content_metadata import ContentMetadata
from app.domain.value_objects.extraction_result import ImageBlock, TextBlock
from app.infrastructure.processors.base import BaseProcessor
from app.infrastructure.services.ocr_service import OcrService


class ImageProcessor(BaseProcessor):
    """Processeur d'images pour extraction de métadonnées, détection de type et OCR."""

    def __init__(
        self, ocr_service: Optional[OcrService] = None, logger: Any = None
    ) -> None:
        """
        Initialiser le processeur.

        Args:
            ocr_service: Service OCR optionnel pour extraire le texte des images
            logger: Logger optionnel
        """
        super().__init__(logger or get_logger(__name__))
        self.ocr_service = ocr_service

    async def process(
        self, image_block: ImageBlock
    ) -> tuple[ImageBlock, Optional[TextBlock]]:
        """
        Traiter une image pour extraire métadonnées, détecter le type et appliquer OCR.

        Args:
            image_block: Bloc d'image à traiter

        Returns:
            Tuple contenant le bloc d'image enrichi et un TextBlock optionnel créé depuis l'OCR
        """
        try:
            processed_image, text_block = await self._process_async(image_block)
            return processed_image, text_block
        except Exception as e:
            self.logger.warning(f"Erreur lors du traitement d'image: {e}")
            return (
                image_block,
                None,
            )  # Retourner l'image non traitée en cas d'erreur

    async def _process_async(
        self, image_block: ImageBlock
    ) -> tuple[ImageBlock, Optional[TextBlock]]:
        """Traitement asynchrone avec OCR."""
        # Charger l'image
        image = None
        if image_block.image_data:
            from io import BytesIO

            image = Image.open(BytesIO(image_block.image_data))
        elif image_block.image_path:
            image = Image.open(image_block.image_path)

        if not image:
            return image_block, None

        # Extraire les métadonnées
        metadata = {
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "mode": image.mode,
            "size_bytes": len(image_block.image_data) if image_block.image_data else 0,
        }

        # Détecter le type de contenu
        content_type = self._detect_content_type(image)

        # Appliquer OCR si disponible
        ocr_text: Optional[str] = None
        ocr_confidence: float = 0.0
        text_block: Optional[TextBlock] = None

        if self.ocr_service and image_block.image_data:
            try:
                if await self.ocr_service.is_available():
                    ocr_text, ocr_confidence = await self.ocr_service.extract_text(
                        image_block.image_data
                    )

                    # Créer un TextBlock si du texte significatif a été extrait
                    if ocr_text and ocr_text.strip():
                        # Créer un TextBlock pour que le texte OCR soit traité par le pipeline NLP
                        ocr_metadata = ContentMetadata(
                            page_number=image_block.metadata.page_number,
                            order=image_block.metadata.order,
                            extraction_method="tesseract_ocr",
                            confidence=ocr_confidence,
                            additional_metadata={
                                **image_block.metadata.additional_metadata,
                                "source": "image_ocr",
                                "image_width": image.width,
                                "image_height": image.height,
                                "image_format": image.format,
                            },
                        )
                        text_block = TextBlock(
                            content=ocr_text.strip(), metadata=ocr_metadata
                        )
                        self.logger.debug(
                            f"Texte OCR extrait: {len(ocr_text)} caractères "
                            f"(confiance: {ocr_confidence:.2f})"
                        )
                else:
                    self.logger.debug(
                        "Tesseract OCR non disponible, traitement sans OCR"
                    )
            except Exception as e:
                self.logger.warning(
                    f"Erreur lors de l'extraction OCR de l'image: {e}"
                )
                # Continuer sans OCR

        # Mettre à jour les métadonnées
        image_block.metadata.additional_metadata.update(
            {
                **metadata,
                "content_type": content_type,
                "processed": True,
            }
        )

        # Mettre à jour le champ ocr_text de l'ImageBlock
        if ocr_text:
            image_block.ocr_text = ocr_text
            image_block.metadata.confidence = ocr_confidence
            image_block.metadata.extraction_method = "tesseract_ocr"

        return image_block, text_block

    def _detect_content_type(self, image: Image.Image) -> str:
        """Détecter le type de contenu de l'image."""
        # Analyse basique basée sur les caractéristiques de l'image
        width, height = image.size
        aspect_ratio = width / height if height > 0 else 1

        # Images très larges ou très hautes sont souvent des graphiques
        if aspect_ratio > 3 or aspect_ratio < 0.33:
            return "graphique"

        # Images carrées ou presque sont souvent des diagrammes
        if 0.8 < aspect_ratio < 1.2:
            # Vérifier la complexité (nombre de couleurs uniques)
            if image.mode == "RGB":
                colors = image.getcolors(maxcolors=256)
                if colors and len(colors) < 50:
                    return "diagramme"

        # Par défaut, considérer comme photo ou image générale
        return "image"

    async def process_batch(
        self, image_blocks: list[ImageBlock]
    ) -> tuple[list[ImageBlock], list[TextBlock]]:
        """
        Traiter plusieurs images.

        Returns:
            Tuple contenant la liste des images traitées et la liste des TextBlocks créés depuis l'OCR
        """
        processed_images: list[ImageBlock] = []
        ocr_text_blocks: list[TextBlock] = []

        for block in image_blocks:
            processed_image, text_block = await self.process(block)
            processed_images.append(processed_image)
            if text_block:
                ocr_text_blocks.append(text_block)

        return processed_images, ocr_text_blocks

