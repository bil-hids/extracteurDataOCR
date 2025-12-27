"""Extracteur PDF unifié utilisant pdfplumber et PyMuPDF."""

import asyncio
from typing import Any

from app.core.logging import get_logger
from app.domain.value_objects.extraction_result import ExtractionResult
from app.infrastructure.extractors.base import BaseExtractor
from app.infrastructure.extractors.pdf.pdf_merger import PdfMerger
from app.infrastructure.extractors.pdf.pdfplumber_extractor import PdfPlumberExtractor
from app.infrastructure.extractors.pdf.pymupdf_extractor import PyMuPdfExtractor


class PdfExtractor(BaseExtractor):
    """Extracteur PDF unifié combinant pdfplumber et PyMuPDF."""

    def __init__(self, logger: Any = None) -> None:
        """Initialiser l'extracteur."""
        super().__init__(logger or get_logger(__name__))
        self.pdfplumber_extractor = PdfPlumberExtractor(logger)
        self.pymupdf_extractor = PyMuPdfExtractor(logger)
        self.merger = PdfMerger(logger)

    async def extract(self, file_path: str) -> ExtractionResult:
        """Extraire le contenu en utilisant les deux extracteurs et fusionner."""
        self._validate_file(file_path)

        # Extraire avec les deux méthodes en parallèle
        pdfplumber_result, pymupdf_result = await asyncio.gather(
            self.pdfplumber_extractor.extract(file_path),
            self.pymupdf_extractor.extract(file_path),
        )

        # Fusionner les résultats
        merged_result = self.merger.merge(pdfplumber_result, pymupdf_result)

        self.logger.info(
            f"Extraction PDF terminée: {len(merged_result.text_blocks)} blocs texte, "
            f"{len(merged_result.tables)} tableaux, {len(merged_result.images)} images"
        )

        return merged_result

    async def extract_tables(self, file_path: str) -> list[Any]:
        """Extraire uniquement les tableaux (pdfplumber est meilleur)."""
        return await self.pdfplumber_extractor.extract_tables(file_path)

    async def extract_images(self, file_path: str) -> list[Any]:
        """Extraire uniquement les images (PyMuPDF)."""
        return await self.pymupdf_extractor.extract_images(file_path)

    def supports(self, file_type: str) -> bool:
        """Vérifier si le type PDF est supporté."""
        return file_type == "application/pdf"

