"""Middleware de gestion d'erreurs."""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    DatabaseError,
    ExtractionError,
    ExtractionNotSupportedError,
    ProcessingError,
    StorageError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


async def error_handler(request: Request, call_next) -> JSONResponse:
    """Gérer les erreurs globalement."""
    try:
        response = await call_next(request)
        return response
    except ExtractionNotSupportedError as e:
        logger.warning(f"Format non supporté: {e.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Format non supporté", "message": e.message},
        )
    except ExtractionError as e:
        logger.error(f"Erreur d'extraction: {e.message}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "Erreur d'extraction", "message": e.message},
        )
    except ProcessingError as e:
        logger.error(f"Erreur de traitement: {e.message}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Erreur de traitement", "message": e.message},
        )
    except StorageError as e:
        logger.error(f"Erreur de stockage: {e.message}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Erreur de stockage", "message": e.message},
        )
    except DatabaseError as e:
        logger.error(f"Erreur de base de données: {e.message}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Erreur de base de données", "message": e.message},
        )
    except Exception as e:
        logger.exception(f"Erreur inattendue: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Erreur interne", "message": str(e)},
        )

