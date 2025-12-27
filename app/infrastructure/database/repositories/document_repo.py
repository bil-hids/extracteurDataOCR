"""Repository pour Document."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.document import DocumentStatus
from app.infrastructure.database.models.document import DocumentModel
from app.infrastructure.database.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[DocumentModel]):
    """Repository pour Document."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialiser le repository."""
        super().__init__(session, DocumentModel)

    async def get_by_status(self, status: DocumentStatus) -> list[DocumentModel]:
        """Obtenir les documents par statut."""
        result = await self.session.execute(
            select(self.model).where(self.model.status == status.value)
        )
        return list(result.scalars().all())

    async def get_by_file_type(self, file_type: str) -> list[DocumentModel]:
        """Obtenir les documents par type de fichier."""
        result = await self.session.execute(
            select(self.model).where(self.model.file_type == file_type)
        )
        return list(result.scalars().all())

