"""Value object pour le résultat d'extraction."""

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.value_objects.content_metadata import ContentMetadata


class TextBlock(BaseModel):
    """Bloc de texte extrait."""

    content: str = Field(..., description="Contenu textuel")
    metadata: ContentMetadata = Field(..., description="Métadonnées du bloc")


class TableBlock(BaseModel):
    """Tableau extrait."""

    headers: list[str] = Field(default_factory=list, description="En-têtes du tableau")
    rows: list[list[Any]] = Field(default_factory=list, description="Lignes du tableau")
    metadata: ContentMetadata = Field(..., description="Métadonnées du tableau")

    @field_validator("headers", mode="before")
    @classmethod
    def clean_headers(cls, v: Any) -> list[str]:
        """Nettoyer les headers : convertir None en chaîne vide."""
        if not isinstance(v, list):
            return []
        return [
            str(h).strip() if h is not None else ""
            for h in v
        ]

    @field_validator("rows", mode="before")
    @classmethod
    def clean_rows(cls, v: Any) -> list[list[Any]]:
        """Nettoyer les rows : convertir None en chaîne vide."""
        if not isinstance(v, list):
            return []
        return [
            [
                str(cell).strip() if cell is not None else ""
                for cell in row
            ]
            for row in v
        ]

    @model_validator(mode="before")
    @classmethod
    def clean_none_values(cls, data: Any) -> Any:
        """Nettoyer les valeurs None dans les headers et rows avant validation (fallback)."""
        if isinstance(data, dict):
            # Nettoyer les headers : convertir None en chaîne vide
            if "headers" in data and data["headers"]:
                data["headers"] = [
                    str(h).strip() if h is not None else ""
                    for h in data["headers"]
                ]
            # Nettoyer les rows : convertir None en chaîne vide
            if "rows" in data and data["rows"]:
                data["rows"] = [
                    [
                        str(cell).strip() if cell is not None else ""
                        for cell in row
                    ]
                    for row in data["rows"]
                ]
        return data


class ImageBlock(BaseModel):
    """Image extraite."""

    image_path: Optional[str] = Field(None, description="Chemin vers l'image extraite")
    image_data: Optional[bytes] = Field(None, description="Données de l'image")
    ocr_text: Optional[str] = Field(None, description="Texte extrait par OCR")
    metadata: ContentMetadata = Field(..., description="Métadonnées de l'image")


class ExtractionResult(BaseModel):
    """Résultat complet d'une extraction."""

    text_blocks: list[TextBlock] = Field(default_factory=list, description="Blocs de texte")
    tables: list[TableBlock] = Field(default_factory=list, description="Tableaux")
    images: list[ImageBlock] = Field(default_factory=list, description="Images")
    structure: Optional[dict[str, Any]] = Field(
        None, description="Structure hiérarchique du document"
    )
    raw_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Métadonnées brutes du document"
    )

    def has_content(self) -> bool:
        """Vérifier si le résultat contient du contenu."""
        return bool(self.text_blocks or self.tables or self.images)

