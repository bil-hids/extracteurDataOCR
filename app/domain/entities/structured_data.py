"""Entité StructuredData."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class StructuredData(BaseModel):
    """Données structurées finales d'un document."""

    id: UUID = Field(default_factory=uuid4, description="ID unique")
    document_id: UUID = Field(..., description="ID du document")
    data: dict[str, Any] = Field(..., description="Données structurées (JSON)")
    schema_version: str = Field(default="1.0", description="Version du schéma")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Date de création")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Date de mise à jour")

    def to_json(self) -> str:
        """Convertir en JSON."""
        import json

        return json.dumps(self.data, ensure_ascii=False, indent=2)

