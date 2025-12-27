"""Repository de base."""

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Repository de base avec opérations CRUD communes."""

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        """Initialiser le repository."""
        self.session = session
        self.model = model

    async def get_by_id(self, id: UUID | str) -> T | None:
        """Obtenir un enregistrement par ID."""
        # Convertir UUID en string pour compatibilité SQLite
        id_str = str(id) if isinstance(id, UUID) else id
        result = await self.session.execute(select(self.model).where(self.model.id == id_str))
        return result.scalar_one_or_none()

    async def get_all(self, limit: int | None = None, offset: int = 0) -> list[T]:
        """Obtenir tous les enregistrements."""
        query = select(self.model).offset(offset)
        if limit:
            query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, entity: T) -> T:
        """Créer un nouvel enregistrement."""
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: T) -> T:
        """Mettre à jour un enregistrement."""
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def delete(self, id: UUID | str) -> bool:
        """Supprimer un enregistrement."""
        entity = await self.get_by_id(id)
        if entity:
            await self.session.delete(entity)
            await self.session.commit()
            return True
        return False

