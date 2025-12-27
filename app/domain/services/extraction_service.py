"""Service d'extraction de contenu."""

from typing import Protocol

from app.domain.value_objects.extraction_result import ExtractionResult


class ExtractionService(Protocol):
    """Interface pour le service d'extraction."""

    async def extract(self, file_path: str) -> ExtractionResult:
        """Extraire le contenu d'un fichier."""
        ...

