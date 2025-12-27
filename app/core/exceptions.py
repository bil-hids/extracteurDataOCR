"""Exceptions custom hiérarchisées pour l'application."""

from typing import Any, Optional


class ExtractionError(Exception):
    """Exception de base pour les erreurs d'extraction."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ExtractionNotSupportedError(ExtractionError):
    """Erreur levée quand le format de fichier n'est pas supporté."""

    pass


class ExtractionFailedError(ExtractionError):
    """Erreur levée quand l'extraction échoue."""

    pass


class ProcessingError(Exception):
    """Exception de base pour les erreurs de traitement."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EnrichmentError(ProcessingError):
    """Erreur levée lors de l'enrichissement du contenu."""

    pass


class StructuringError(ProcessingError):
    """Erreur levée lors de la structuration des données."""

    pass


class StorageError(Exception):
    """Exception de base pour les erreurs de stockage."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class FileNotFoundError(StorageError):
    """Erreur levée quand un fichier n'est pas trouvé."""

    pass


class DatabaseError(StorageError):
    """Erreur levée lors d'opérations sur la base de données."""

    pass

