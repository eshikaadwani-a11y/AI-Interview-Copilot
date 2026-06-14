"""Structured application logging.

Provides a single ``configure_logging`` entry point and a ``get_logger``
helper so every module logs consistently with timestamps, levels, and the
logger name.
"""

from __future__ import annotations

import logging
import sys

from app.core.config import settings

_CONFIGURED = False

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging() -> None:
    """Configure root logging once for the whole application."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    level = logging.DEBUG if settings.debug else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT))

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers on reload.
    root.handlers.clear()
    root.addHandler(handler)

    # Tame noisy third-party loggers.
    for noisy in ("pymongo", "httpx", "httpcore", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger."""
    return logging.getLogger(name)
