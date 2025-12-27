"""Entité ContentBlock."""

from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.value_objects.content_metadata import ContentMetadata


class ContentType(str, Enum):
    """Type de contenu."""

    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    LIST = "list"
    HEADING = "heading"


class ContentBlock(BaseModel):
    """Bloc de contenu extrait et traité."""

    id: UUID = Field(default_factory=uuid4, description="ID unique du bloc")
    document_id: UUID = Field(..., description="ID du document parent")
    content_type: ContentType = Field(..., description="Type de contenu")
    content: dict[str, Any] = Field(..., description="Contenu du bloc (structure variable)")
    metadata: ContentMetadata = Field(..., description="Métadonnées du bloc")
    parent_block_id: Optional[UUID] = Field(None, description="ID du bloc parent")
    previous_block_id: Optional[UUID] = Field(None, description="ID du bloc précédent")
    next_block_id: Optional[UUID] = Field(None, description="ID du bloc suivant")
    entities: list[dict[str, Any]] = Field(
        default_factory=list, description="Entités nommées extraites"
    )
    relevance_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Score de pertinence"
    )

