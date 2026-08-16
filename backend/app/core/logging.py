"""Structured logging configuration for the application.

Supports both JSON and human-readable log formats.
"""

from __future__ import annotations

import logging
import sys
from typing import Any


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured log output."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import datetime, timezone

        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "investigation_id"):
            log_entry["investigation_id"] = record.investigation_id

        return json.dumps(log_entry, default=str)


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configure application logging.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: The log format — "json" for structured output, "text" for human-readable.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)

    if log_format.lower() == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if log_level.upper() == "DEBUG" else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """Get a named logger instance.

    Args:
        name: The logger name (typically __name__).

    Returns:
        Configured Logger instance.
    """
    return logging.getLogger(name)
