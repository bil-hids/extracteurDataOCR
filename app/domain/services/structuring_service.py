"""Service de structuration de données."""

from typing import Protocol

from app.domain.entities.content_block import ContentBlock
from app.domain.entities.structured_data import StructuredData
from app.domain.value_objects.extraction_result import ExtractionResult


class StructuringService(Protocol):
    """Interface pour le service de structuration."""

    async def structure(
        self, extraction_result: ExtractionResult, document_id: str
    ) -> StructuredData:
        """Structurer les données extraites."""
        ...

    async def create_content_blocks(
        self, extraction_result: ExtractionResult, document_id: str
    ) -> list[ContentBlock]:
        """Créer les blocs de contenu à partir du résultat d'extraction."""
        ...

