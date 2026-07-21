"""Centralized, environment-driven configuration for the Loan Restructuring SDK.

Loaded from environment variables / a `.env` file (see `.env.example` at the
repo root). Values are plumbing/config, not business logic, so this module
is fully implemented -- unlike the engines/services it configures.
"""

from __future__ import annotations

from decimal import Decimal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings. See docs/SDD.md section 5.3 / 9 (D-notes) / 12 for rationale."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Mistral OCR / extraction ---
    mistral_api_key: str = ""
    mistral_model: str = "mistral-ocr-latest"
    mistral_api_base_url: str = "https://api.mistral.ai"

    # --- Business rule thresholds (pending stakeholder sign-off, docs/SDD.md section 12) ---
    # max_installment_ratio is Decimal, not float: it's multiplied directly against Decimal
    # money amounts (Scenario 1), and 0.55 has no exact binary float representation.
    max_installment_ratio: Decimal = Decimal("0.55")
    max_loan_duration_months: int = 96
    max_statement_age_days: int = 30

    # --- Logging ---
    log_level: str = "INFO"

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance -- the single source of truth per process."""
    return Settings()
