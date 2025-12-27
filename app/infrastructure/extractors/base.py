"""Interface abstraite pour les extracteurs."""

from abc import ABC, abstractmethod
from typing import Any

from app.core.exceptions import ExtractionError
from app.domain.value_objects.extraction_result import ExtractionResult


class BaseExtractor(ABC):
    """Classe de base abstraite pour tous les extracteurs."""

    def __init__(self, logger: Any) -> None:
        """Initialiser l'extracteur."""
        self.logger = logger

    @abstractmethod
    async def extract(self, file_path: str) -> ExtractionResult:
        """
        Extraire le contenu d'un fichier.

        Args:
            file_path: Chemin vers le fichier à extraire

        Returns:
            ExtractionResult avec le contenu extrait

        Raises:
            ExtractionError: Si l'extraction échoue
        """
        pass

    @abstractmethod
    async def extract_tables(self, file_path: str) -> list[Any]:
        """
        Extraire les tableaux d'un fichier.

        Args:
            file_path: Chemin vers le fichier

        Returns:
            Liste de tableaux extraits
        """
        pass

    @abstractmethod
    async def extract_images(self, file_path: str) -> list[Any]:
        """
        Extraire les images d'un fichier.

        Args:
            file_path: Chemin vers le fichier

        Returns:
            Liste d'images extraites
        """
        pass

    @abstractmethod
    def supports(self, file_type: str) -> bool:
        """
        Vérifier si l'extracteur supporte un type de fichier.

        Args:
            file_type: Type MIME du fichier

        Returns:
            True si le type est supporté
        """
        pass

    def _validate_file(self, file_path: str) -> None:
        """Valider l'existence du fichier."""
        from pathlib import Path

        path = Path(file_path)
        if not path.exists():
            raise ExtractionError(f"Le fichier n'existe pas: {file_path}")
        if not path.is_file():
            raise ExtractionError(f"Le chemin n'est pas un fichier: {file_path}")

