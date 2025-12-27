"""Classe de base pour les structurateurs."""

from abc import ABC, abstractmethod
from typing import Any


class BaseStructurer(ABC):
    """Classe de base abstraite pour tous les structurateurs."""

    def __init__(self, logger: Any) -> None:
        """Initialiser le structurateur."""
        self.logger = logger

    @abstractmethod
    async def structure(self, *args: Any, **kwargs: Any) -> Any:
        """Structurer les données."""
        pass

