"""Application-wide logging setup.

Ensures every module logs through a consistent format and respects the
configured `LOG_LEVEL`. Callers should never log full employee names,
national IDs, account numbers, or salary figures at default levels -- see
docs/SDD.md "Non-Functional Requirements / Privacy".
"""

from __future__ import annotations

import logging

from loan_restructuring_sdk.config.settings import get_settings


def configure_logging() -> None:
    """Configure the root logger. Call once at process startup (API entrypoint)."""
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
