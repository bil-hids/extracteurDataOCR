"""Value object pour les métadonnées de fichier."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class FileMetadata(BaseModel):
    """Métadonnées d'un fichier."""

    filename: str = Field(..., description="Nom du fichier")
    file_path: Path = Field(..., description="Chemin du fichier")
    file_type: str = Field(..., description="Type MIME du fichier")
    file_size: int = Field(..., description="Taille du fichier en bytes")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Date d'upload")
    author: Optional[str] = Field(None, description="Auteur du document")
    title: Optional[str] = Field(None, description="Titre du document")
    created_at: Optional[datetime] = Field(None, description="Date de création du document")
    modified_at: Optional[datetime] = Field(None, description="Date de modification du document")

    @field_validator("file_size")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """Valider la taille du fichier."""
        if v <= 0:
            raise ValueError("La taille du fichier doit être positive")
        return v

    @field_validator("file_type")
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        """Valider le type de fichier."""
        if not v:
            raise ValueError("Le type de fichier ne peut pas être vide")
        return v

