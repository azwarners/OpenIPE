"""Logging configuration for OpenIPE."""

from __future__ import annotations

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure simple process-wide logging for the Core application."""

    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Unknown log level: {level}")
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
