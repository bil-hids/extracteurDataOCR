"""Dépendances FastAPI réutilisables."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_logger_dependency() -> Any:
    """Dépendance pour obtenir un logger."""
    return logger


async def verify_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
) -> str:
    """Vérifier la clé API (optionnel pour le moment)."""
    # TODO: Implémenter vérification API key si nécessaire
    return x_api_key or "default"

