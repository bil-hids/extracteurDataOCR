"""Use case pour extraire le contenu d'un document."""

from uuid import UUID

from app.core.logging import get_logger
from app.domain.value_objects.extraction_result import ExtractionResult
from app.infrastructure.extractors.base import BaseExtractor

logger = get_logger(__name__)


class ExtractContentUseCase:
    """Use case pour extraire le contenu d'un document."""

    def __init__(self, extractor: BaseExtractor) -> None:
        """Initialiser le use case."""
        self.extractor = extractor

    async def execute(self, file_path: str) -> ExtractionResult:
        """
        Extraire le contenu d'un fichier.

        Args:
            file_path: Chemin vers le fichier

        Returns:
            Résultat d'extraction
        """
        logger.info(f"Début extraction: {file_path}")
        result = await self.extractor.extract(file_path)
        logger.info(f"Extraction terminée: {result.has_content()}")
        return result

