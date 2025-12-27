"""Repository pour ContentBlock."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.content_block import ContentType
from app.infrastructure.database.models.content_block import ContentBlockModel
from app.infrastructure.database.repositories.base import BaseRepository


class ContentRepository(BaseRepository[ContentBlockModel]):
    """Repository pour ContentBlock."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialiser le repository."""
        super().__init__(session, ContentBlockModel)

    async def get_by_document_id(self, document_id: UUID | str) -> list[ContentBlockModel]:
        """Obtenir tous les blocs d'un document."""
        # Convertir UUID en string pour compatibilité SQLite
        doc_id_str = str(document_id) if isinstance(document_id, UUID) else document_id
        result = await self.session.execute(
            select(self.model)
            .where(self.model.document_id == doc_id_str)
            .order_by(self.model.created_at)
        )
        return list(result.scalars().all())

    async def get_by_type(
        self, document_id: UUID | str, content_type: ContentType
    ) -> list[ContentBlockModel]:
        """Obtenir les blocs d'un type spécifique pour un document."""
        # Convertir UUID en string pour compatibilité SQLite
        doc_id_str = str(document_id) if isinstance(document_id, UUID) else document_id
        result = await self.session.execute(
            select(self.model).where(
                self.model.document_id == doc_id_str,
                self.model.content_type == content_type.value,
            )
        )
        return list(result.scalars().all())

    async def get_by_page(
        self, document_id: UUID | str, page_number: int
    ) -> list[ContentBlockModel]:
        """Obtenir les blocs d'une page spécifique."""
        # Convertir UUID en string pour compatibilité SQLite
        doc_id_str = str(document_id) if isinstance(document_id, UUID) else document_id
        result = await self.session.execute(
            select(self.model).where(
                self.model.document_id == doc_id_str,
                self.model.meta_data["page_number"].astext == str(page_number),
            )
        )
        return list(result.scalars().all())

