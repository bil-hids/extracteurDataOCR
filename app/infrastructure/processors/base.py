"""Classe de base pour les processeurs."""

from abc import ABC, abstractmethod
from typing import Any


class BaseProcessor(ABC):
    """Classe de base abstraite pour tous les processeurs."""

    def __init__(self, logger: Any) -> None:
        """Initialiser le processeur."""
        self.logger = logger

    @abstractmethod
    async def process(self, *args: Any, **kwargs: Any) -> Any:
        """Traiter les données."""
        pass

