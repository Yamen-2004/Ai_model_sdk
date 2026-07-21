"""The structured output of Stage 1's extraction pipeline (OCR Service + PDF Extraction Engine)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class SalaryStatement(BaseModel):
    """Structured fields extracted from a salary-statement PDF via Mistral OCR.

    Fields are nullable because extraction may fail to locate them -- the
    Validation Engine's presence rules are what turn a missing field into a
    rejection reason, not this model.
    """

    employee_name: str | None = None
    net_salary: Decimal | None = None
    payment_date: date | None = None
    raw_extraction: dict[str, Any] = Field(
        default_factory=dict,
        description="Full, unmodified OCR output -- retained for audit/debugging (docs/SDD.md section 10).",
    )
