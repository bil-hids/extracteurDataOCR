"""Value object pour les métadonnées de contenu."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ContentMetadata(BaseModel):
    """Métadonnées d'un bloc de contenu."""

    page_number: Optional[int] = Field(None, description="Numéro de page")
    position: Optional[dict[str, float]] = Field(
        None, description="Position dans le document (x, y, width, height)"
    )
    order: int = Field(..., description="Ordre dans le document")
    section_id: Optional[str] = Field(None, description="ID de la section parente")
    section_level: Optional[int] = Field(None, description="Niveau hiérarchique")
    section_title: Optional[str] = Field(None, description="Titre de la section")
    language: Optional[str] = Field(None, description="Langue détectée")
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Niveau de confiance de l'extraction"
    )
    extraction_method: Optional[str] = Field(None, description="Méthode d'extraction utilisée")
    additional_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Métadonnées additionnelles"
    )

