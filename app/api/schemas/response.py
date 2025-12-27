"""Schemas de réponse génériques."""

from typing import Any

from pydantic import BaseModel


class SuccessResponse(BaseModel):
    """Réponse de succès générique."""

    success: bool = True
    message: str
    data: Any | None = None


class ErrorResponse(BaseModel):
    """Réponse d'erreur générique."""

    success: bool = False
    error: str
    details: dict[str, Any] | None = None

