"""Extracteur de métadonnées."""

from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.infrastructure.processors.base import BaseProcessor


class MetadataExtractor(BaseProcessor):
    """Extracteur de métadonnées de fichiers et de contenu."""

    def __init__(self, logger: Any = None) -> None:
        """Initialiser l'extracteur."""
        super().__init__(logger or get_logger(__name__))

    async def extract_file_metadata(self, file_path: str) -> dict[str, Any]:
        """
        Extraire les métadonnées d'un fichier.

        Args:
            file_path: Chemin vers le fichier

        Returns:
            Dictionnaire de métadonnées
        """
        path = Path(file_path)
        if not path.exists():
            return {}

        stat = path.stat()
        metadata = {
            "filename": path.name,
            "file_size": stat.st_size,
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
            "extension": path.suffix,
        }

        return metadata

    async def extract_content_metadata(
        self, extraction_result: Any
    ) -> dict[str, Any]:
        """
        Extraire les métadonnées du contenu extrait.

        Args:
            extraction_result: Résultat d'extraction

        Returns:
            Dictionnaire de métadonnées de contenu
        """
        metadata = {
            "text_block_count": len(extraction_result.text_blocks),
            "table_count": len(extraction_result.tables),
            "image_count": len(extraction_result.images),
            "has_content": extraction_result.has_content(),
        }

        # Compter les entités si disponibles
        total_entities = 0
        for block in extraction_result.text_blocks:
            entities = block.metadata.additional_metadata.get("entities", [])
            total_entities += len(entities)

        metadata["total_entities"] = total_entities

        return metadata

