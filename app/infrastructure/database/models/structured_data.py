"""Modèle SQLAlchemy pour StructuredData."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.connection import Base


class StructuredDataModel(Base):
    """Modèle SQLAlchemy pour StructuredData."""

    __tablename__ = "structured_data"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True, index=True
    )
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), default="1.0")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

