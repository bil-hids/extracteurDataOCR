"""Extracteur PDF utilisant PyMuPDF (fitz)."""

import asyncio
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from app.core.exceptions import ExtractionFailedError
from app.core.logging import get_logger
from app.domain.value_objects.content_metadata import ContentMetadata
from app.domain.value_objects.extraction_result import (
    ExtractionResult,
    ImageBlock,
    TextBlock,
)
from app.infrastructure.extractors.base import BaseExtractor


class PyMuPdfExtractor(BaseExtractor):
    """Extracteur PDF avec PyMuPDF (bon pour structure et images)."""

    def __init__(self, logger: Any = None) -> None:
        """Initialiser l'extracteur."""
        super().__init__(logger or get_logger(__name__))

    async def extract(self, file_path: str) -> ExtractionResult:
        """Extraire le contenu d'un PDF avec PyMuPDF."""
        self._validate_file(file_path)

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._extract_sync, file_path)
            return result
        except Exception as e:
            self.logger.exception(f"Erreur lors de l'extraction PDF: {e}")
            raise ExtractionFailedError(f"Échec de l'extraction PDF: {str(e)}")

    def _extract_sync(self, file_path: str) -> ExtractionResult:
        """Extraction synchrone."""
        text_blocks: list[TextBlock] = []
        images: list[ImageBlock] = []

        doc = fitz.open(file_path)
        try:
            # Extraire métadonnées
            metadata = doc.metadata

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Extraire le texte avec structure
                text_dict = page.get_text("dict")
                page_text = page.get_text()

                if page_text and page_text.strip():
                    # Détecter la structure (titres, paragraphes)
                    blocks = text_dict.get("blocks", [])
                    structure = self._extract_structure(blocks)

                    metadata_obj = ContentMetadata(
                        page_number=page_num + 1,
                        order=len(text_blocks),
                        extraction_method="pymupdf",
                        additional_metadata={"structure": structure, "raw_metadata": metadata},
                    )
                    text_blocks.append(TextBlock(content=page_text.strip(), metadata=metadata_obj))

                # Extraire les images
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]

                        metadata_obj = ContentMetadata(
                            page_number=page_num + 1,
                            order=len(images),
                            extraction_method="pymupdf",
                        )
                        images.append(
                            ImageBlock(
                                image_data=image_bytes,
                                metadata=metadata_obj,
                            )
                        )
                    except Exception as e:
                        self.logger.warning(f"Impossible d'extraire l'image {img_index}: {e}")

        finally:
            doc.close()

        return ExtractionResult(text_blocks=text_blocks, images=images, raw_metadata=metadata or {})

    def _extract_structure(self, blocks: list[dict]) -> dict:
        """Extraire la structure du document depuis les blocs."""
        structure = {"headings": [], "paragraphs": []}

        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        font_size = span.get("size", 0)
                        text = span.get("text", "").strip()

                        # Détecter les titres (généralement plus grands)
                        if font_size > 12 and text:
                            structure["headings"].append({"text": text, "size": font_size})
                        elif text:
                            structure["paragraphs"].append(text)

        return structure

    async def extract_tables(self, file_path: str) -> list[Any]:
        """PyMuPDF n'est pas optimal pour les tableaux."""
        return []

    async def extract_images(self, file_path: str) -> list[Any]:
        """Extraire uniquement les images."""
        result = await self.extract(file_path)
        return result.images

    def supports(self, file_type: str) -> bool:
        """Vérifier si le type PDF est supporté."""
        return file_type == "application/pdf"

