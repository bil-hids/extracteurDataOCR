"""Schemas pour Document."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """Schéma de réponse pour un document."""

    id: UUID
    filename: str
    file_type: str
    file_size: int
    status: str
    created_at: datetime
    updated_at: datetime


class DocumentUploadResponse(BaseModel):
    """Schéma de réponse pour l'upload."""

    document_id: UUID
    filename: str
    status: str
    message: str


class DocumentStatusResponse(BaseModel):
    """Schéma de réponse pour le statut."""

    id: UUID
    status: str
    error_message: str | None = None
    processing_started_at: datetime | None = None
    processing_completed_at: datetime | None = None

