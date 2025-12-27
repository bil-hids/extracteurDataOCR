"""Middleware de logging des requêtes."""

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware pour logger les requêtes."""

    async def dispatch(self, request: Request, call_next):
        """Logger la requête et la réponse."""
        start_time = time.time()

        # Logger la requête
        logger.info(
            f"Requête: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None,
        )

        # Exécuter la requête
        response = await call_next(request)

        # Calculer le temps de traitement
        process_time = time.time() - start_time

        # Logger la réponse
        logger.info(
            f"Réponse: {response.status_code} ({process_time:.3f}s)",
            status_code=response.status_code,
            process_time=process_time,
        )

        return response

