"""Stockage local de fichiers."""

import aiofiles
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.core.exceptions import StorageError
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class LocalStorage:
    """Stockage local de fichiers."""

    def __init__(self, base_dir: Path | None = None) -> None:
        """Initialiser le stockage."""
        self.base_dir = base_dir or settings.upload_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file_content: bytes, filename: str) -> Path:
        """
        Sauvegarder un fichier.

        Args:
            file_content: Contenu du fichier
            filename: Nom du fichier

        Returns:
            Chemin vers le fichier sauvegardé
        """
        file_path = self.base_dir / filename

        try:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(file_content)
            logger.info(f"Fichier sauvegardé: {file_path}")
            return file_path
        except Exception as e:
            logger.exception(f"Erreur lors de la sauvegarde: {e}")
            raise StorageError(f"Impossible de sauvegarder le fichier: {str(e)}")

    async def read_file(self, file_path: Path | str) -> bytes:
        """
        Lire un fichier.

        Args:
            file_path: Chemin vers le fichier

        Returns:
            Contenu du fichier
        """
        path = Path(file_path)
        if not path.exists():
            raise StorageError(f"Fichier non trouvé: {path}")

        try:
            async with aiofiles.open(path, "rb") as f:
                content = await f.read()
            return content
        except Exception as e:
            logger.exception(f"Erreur lors de la lecture: {e}")
            raise StorageError(f"Impossible de lire le fichier: {str(e)}")

    async def delete_file(self, file_path: Path | str) -> None:
        """
        Supprimer un fichier.

        Args:
            file_path: Chemin vers le fichier
        """
        path = Path(file_path)
        if path.exists():
            try:
                path.unlink()
                logger.info(f"Fichier supprimé: {path}")
            except Exception as e:
                logger.exception(f"Erreur lors de la suppression: {e}")
                raise StorageError(f"Impossible de supprimer le fichier: {str(e)}")

