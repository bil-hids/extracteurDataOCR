"""Configuration du logging structuré."""

import logging
import sys
from datetime import datetime
from typing import Any, Optional

from pythonjsonlogger import jsonlogger


class StructuredLogger:
    """Logger structuré avec format JSON."""

    def __init__(self, name: str, level: int = logging.INFO) -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Handler pour stdout avec format JSON
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _log(
        self,
        level: int,
        message: str,
        extra: Optional[dict[str, Any]] = None,
        exc_info: Optional[Any] = None,
    ) -> None:
        """Log avec contexte supplémentaire."""
        extra_data = extra or {}
        extra_data["timestamp"] = datetime.utcnow().isoformat()
        self.logger.log(level, message, extra=extra_data, exc_info=exc_info)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log niveau debug."""
        self._log(logging.DEBUG, message, kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log niveau info."""
        self._log(logging.INFO, message, kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log niveau warning."""
        self._log(logging.WARNING, message, kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log niveau error."""
        self._log(logging.ERROR, message, kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception avec traceback."""
        self._log(logging.ERROR, message, kwargs, exc_info=True)


def get_logger(name: str) -> StructuredLogger:
    """Obtenir un logger structuré."""
    return StructuredLogger(name)

