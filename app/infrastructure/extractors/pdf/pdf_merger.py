"""Fusion intelligente des résultats d'extraction PDF."""

from typing import Any

from app.core.logging import get_logger
from app.domain.value_objects.extraction_result import ExtractionResult


class PdfMerger:
    """Fusionne les résultats de pdfplumber et PyMuPDF."""

    def __init__(self, logger: Any = None) -> None:
        """Initialiser le merger."""
        self.logger = logger or get_logger(__name__)

    def merge(
        self, pdfplumber_result: ExtractionResult, pymupdf_result: ExtractionResult
    ) -> ExtractionResult:
        """
        Fusionner les résultats des deux extracteurs.

        Stratégie:
        - Tableaux: Priorité à pdfplumber (plus précis)
        - Texte: Combiner en évitant les doublons
        - Images: Utiliser PyMuPDF uniquement
        - Structure: Utiliser PyMuPDF (meilleur pour structure)
        """
        # Tableaux: pdfplumber uniquement
        tables = pdfplumber_result.tables

        # Images: PyMuPDF uniquement
        images = pymupdf_result.images

        # Texte: Fusionner intelligemment
        text_blocks = self._merge_text_blocks(
            pdfplumber_result.text_blocks, pymupdf_result.text_blocks
        )

        # Structure: PyMuPDF (plus riche)
        structure = pymupdf_result.structure

        # Métadonnées: Combiner
        raw_metadata = {**pdfplumber_result.raw_metadata, **pymupdf_result.raw_metadata}

        return ExtractionResult(
            text_blocks=text_blocks,
            tables=tables,
            images=images,
            structure=structure,
            raw_metadata=raw_metadata,
        )

    def _merge_text_blocks(
        self, blocks1: list, blocks2: list
    ) -> list:  # type: ignore
        """Fusionner les blocs de texte en évitant les doublons."""
        merged: list = []
        seen_pages: set[int] = set()

        # Priorité aux blocs avec structure (PyMuPDF)
        for block in blocks2:
            page = block.metadata.page_number
            if page and page not in seen_pages:
                merged.append(block)
                if page:
                    seen_pages.add(page)

        # Ajouter les blocs pdfplumber pour les pages non couvertes
        for block in blocks1:
            page = block.metadata.page_number
            if page and page not in seen_pages:
                merged.append(block)
                if page:
                    seen_pages.add(page)

        # Trier par page et ordre
        merged.sort(key=lambda b: (b.metadata.page_number or 0, b.metadata.order))

        return merged

