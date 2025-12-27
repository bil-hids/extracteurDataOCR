"""Extracteur PDF utilisant pdfplumber."""

import asyncio
from pathlib import Path
from typing import Any

import pdfplumber

from app.core.exceptions import ExtractionFailedError
from app.core.logging import get_logger
from app.domain.value_objects.content_metadata import ContentMetadata
from app.domain.value_objects.extraction_result import (
    ExtractionResult,
    TableBlock,
    TextBlock,
)
from app.infrastructure.extractors.base import BaseExtractor


class PdfPlumberExtractor(BaseExtractor):
    """Extracteur PDF avec pdfplumber (précis pour tableaux et texte)."""

    def __init__(self, logger: Any = None) -> None:
        """Initialiser l'extracteur."""
        super().__init__(logger or get_logger(__name__))

    async def extract(self, file_path: str) -> ExtractionResult:
        """Extraire le contenu d'un PDF avec pdfplumber."""
        self._validate_file(file_path)

        try:
            # Exécuter dans un thread pool car pdfplumber est synchrone
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._extract_sync, file_path)
            return result
        except Exception as e:
            self.logger.exception(f"Erreur lors de l'extraction PDF: {e}")
            raise ExtractionFailedError(f"Échec de l'extraction PDF: {str(e)}")

    def _extract_sync(self, file_path: str) -> ExtractionResult:
        """Extraction synchrone."""
        text_blocks: list[TextBlock] = []
        tables: list[TableBlock] = []

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # Extraire le texte
                text = page.extract_text()
                if text and text.strip():
                    metadata = ContentMetadata(
                        page_number=page_num,
                        order=len(text_blocks),
                        extraction_method="pdfplumber",
                    )
                    text_blocks.append(TextBlock(content=text.strip(), metadata=metadata))

                # Extraire les tableaux
                page_tables = page.extract_tables()
                for table_data in page_tables:
                    if table_data and len(table_data) > 0:
                        # Nettoyer les headers : convertir None en chaîne vide
                        raw_headers = table_data[0] if table_data else []
                        # S'assurer que raw_headers est une liste et nettoyer chaque élément
                        if not isinstance(raw_headers, list):
                            raw_headers = []
                        headers = []
                        for header in raw_headers:
                            if header is None:
                                headers.append("")
                            else:
                                try:
                                    headers.append(str(header).strip())
                                except Exception:
                                    headers.append("")
                        
                        # Nettoyer les rows : convertir None en chaîne vide
                        raw_rows = table_data[1:] if len(table_data) > 1 else []
                        rows = []
                        for row in raw_rows:
                            if not isinstance(row, list):
                                continue
                            cleaned_row = []
                            for cell in row:
                                if cell is None:
                                    cleaned_row.append("")
                                else:
                                    try:
                                        cleaned_row.append(str(cell).strip())
                                    except Exception:
                                        cleaned_row.append("")
                            rows.append(cleaned_row)
                        
                        metadata = ContentMetadata(
                            page_number=page_num,
                            order=len(tables),
                            extraction_method="pdfplumber",
                        )
                        tables.append(
                            TableBlock(headers=headers, rows=rows, metadata=metadata)
                        )

        return ExtractionResult(text_blocks=text_blocks, tables=tables)

    async def extract_tables(self, file_path: str) -> list[Any]:
        """Extraire uniquement les tableaux."""
        result = await self.extract(file_path)
        return result.tables

    async def extract_images(self, file_path: str) -> list[Any]:
        """pdfplumber ne supporte pas l'extraction d'images."""
        return []

    def supports(self, file_type: str) -> bool:
        """Vérifier si le type PDF est supporté."""
        return file_type == "application/pdf"

