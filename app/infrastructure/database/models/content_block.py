"""Modèle SQLAlchemy pour ContentBlock."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.content_block import ContentType
from app.infrastructure.database.connection import Base


class ContentBlockModel(Base):
    """Modèle SQLAlchemy pour ContentBlock."""

    __tablename__ = "content_blocks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    meta_data: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    parent_block_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    previous_block_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    next_block_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    entities: Mapped[list] = mapped_column(JSON, default=list)
    relevance_score: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

