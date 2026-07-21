"""Thin wrapper around the standard `logging` module for consistent logger creation.

Actual handler/format/level configuration lives in `config.logging_config`
(configuration is a Configuration-module concern, not a Utilities one) --
this module only standardizes *how* a module obtains its logger.
"""

from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger. Usage: `logger = get_logger(__name__)`."""
    return logging.getLogger(name)
