"""Repository pour StructuredData."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.structured_data import StructuredDataModel
from app.infrastructure.database.repositories.base import BaseRepository


class StructuredDataRepository(BaseRepository[StructuredDataModel]):
    """Repository pour StructuredData."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialiser le repository."""
        super().__init__(session, StructuredDataModel)

    async def get_by_document_id(self, document_id: UUID | str) -> StructuredDataModel | None:
        """Obtenir les données structurées d'un document."""
        # Convertir UUID en string pour compatibilité SQLite
        doc_id_str = str(document_id) if isinstance(document_id, UUID) else document_id
        result = await self.session.execute(
            select(self.model).where(self.model.document_id == doc_id_str)
        )
        return result.scalar_one_or_none()

