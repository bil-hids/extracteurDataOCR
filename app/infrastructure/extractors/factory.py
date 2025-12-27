"""Factory pour créer les extracteurs appropriés."""

import mimetypes
from pathlib import Path
from typing import Optional

from app.core.exceptions import ExtractionNotSupportedError
from app.core.logging import get_logger
from app.infrastructure.extractors.base import BaseExtractor

logger = get_logger(__name__)


class ExtractorFactory:
    """Factory pour créer des extracteurs selon le type de fichier."""

    def __init__(self) -> None:
        """Initialiser la factory."""
        self._extractors: list[BaseExtractor] = []
        self._logger = logger

    def register(self, extractor: BaseExtractor) -> None:
        """Enregistrer un extracteur."""
        self._extractors.append(extractor)
        self._logger.debug(f"Extracteur enregistré: {extractor.__class__.__name__}")

    def create(self, file_path: str) -> BaseExtractor:
        """
        Créer un extracteur approprié pour un fichier.

        Args:
            file_path: Chemin vers le fichier

        Returns:
            Extracteur approprié

        Raises:
            ExtractionNotSupportedError: Si aucun extracteur ne supporte le fichier
        """
        file_type, _ = mimetypes.guess_type(file_path)
        if not file_type:
            # Essayer de deviner depuis l'extension
            ext = Path(file_path).suffix.lower()
            file_type = self._guess_from_extension(ext)

        if not file_type:
            raise ExtractionNotSupportedError(
                f"Impossible de déterminer le type de fichier: {file_path}"
            )

        # Chercher un extracteur qui supporte ce type
        for extractor in self._extractors:
            if extractor.supports(file_type):
                self._logger.info(
                    f"Extracteur sélectionné: {extractor.__class__.__name__} pour {file_type}"
                )
                return extractor

        raise ExtractionNotSupportedError(
            f"Aucun extracteur disponible pour le type: {file_type}"
        )

    def _guess_from_extension(self, extension: str) -> Optional[str]:
        """Deviner le type MIME depuis l'extension."""
        extension_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
        }
        return extension_map.get(extension)

