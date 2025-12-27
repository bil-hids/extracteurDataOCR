"""Entité Document."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.value_objects.file_metadata import FileMetadata


class DocumentStatus(str, Enum):
    """Statut d'un document."""

    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    ENRICHING = "enriching"
    ENRICHED = "enriched"
    STRUCTURING = "structuring"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(BaseModel):
    """Entité Document avec métadonnées."""

    id: UUID = Field(default_factory=uuid4, description="ID unique du document")
    file_metadata: FileMetadata = Field(..., description="Métadonnées du fichier")
    status: DocumentStatus = Field(
        default=DocumentStatus.UPLOADED, description="Statut du traitement"
    )
    error_message: Optional[str] = Field(None, description="Message d'erreur si échec")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Date de création")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Date de mise à jour")
    processing_started_at: Optional[datetime] = Field(
        None, description="Début du traitement"
    )
    processing_completed_at: Optional[datetime] = Field(
        None, description="Fin du traitement"
    )

    def update_status(self, status: DocumentStatus) -> None:
        """Mettre à jour le statut du document."""
        self.status = status
        self.updated_at = datetime.utcnow()

    def mark_processing_started(self) -> None:
        """Marquer le début du traitement."""
        self.processing_started_at = datetime.utcnow()
        self.update_status(DocumentStatus.EXTRACTING)

    def mark_processing_completed(self) -> None:
        """Marquer la fin du traitement."""
        self.processing_completed_at = datetime.utcnow()
        self.update_status(DocumentStatus.COMPLETED)

    def mark_failed(self, error_message: str) -> None:
        """Marquer le document comme échoué."""
        self.error_message = error_message
        self.update_status(DocumentStatus.FAILED)

