"""Schemas pour le contenu."""

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ContentBlockResponse(BaseModel):
    """Schéma de réponse pour un bloc de contenu."""

    id: UUID
    content_type: str
    content: dict[str, Any]
    metadata: dict[str, Any]
    entities: list[dict[str, Any]] = Field(default_factory=list)
    relevance_score: float | None = None
    parent_block_id: Optional[UUID] = Field(None, description="ID du bloc parent")
    previous_block_id: Optional[UUID] = Field(None, description="ID du bloc précédent")
    next_block_id: Optional[UUID] = Field(None, description="ID du bloc suivant")


class ContentResponse(BaseModel):
    """Schéma de réponse pour le contenu d'un document."""

    document_id: UUID
    text_blocks: list[ContentBlockResponse] = Field(default_factory=list)
    tables: list[ContentBlockResponse] = Field(default_factory=list)
    images: list[ContentBlockResponse] = Field(default_factory=list)


class StructuredDataResponse(BaseModel):
    """Schéma de réponse pour les données structurées."""

    document_id: UUID
    data: dict[str, Any]
    schema_version: str


class DocumentDataResponse(BaseModel):
    """Schéma de réponse complet avec toutes les données traitées d'un document."""

    document_id: UUID
    document_info: dict[str, Any]
    structured_data: StructuredDataResponse | None = None
    content_blocks: ContentResponse
    statistics: dict[str, Any] | None = None

