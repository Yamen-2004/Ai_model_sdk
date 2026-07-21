"""Turns the OCR Service's raw JSON output into a SalaryStatement.

Transformation only, per Stage 1 scope -- no validation happens here. A
field that is missing, `null`, or unparsable simply becomes `None` on the
resulting `SalaryStatement`; it's the Validation Engine's job to decide
whether a `None` is a rejection reason.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from loan_restructuring_sdk.models.salary_statement import SalaryStatement


class SalaryStatementBuilder:
    """Maps raw OCR output (a dict) to a `SalaryStatement`. Never raises -- unparsable fields become `None`."""

    def build(self, raw_extraction: dict[str, Any]) -> SalaryStatement:
        return SalaryStatement(
            employee_name=self._normalize_name(raw_extraction.get("employee_name")),
            net_salary=self._normalize_net_salary(raw_extraction.get("net_salary")),
            payment_date=self._normalize_payment_date(raw_extraction.get("payment_date")),
            raw_extraction=raw_extraction,
        )

    def _normalize_name(self, value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    def _normalize_net_salary(self, value: Any) -> Decimal | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None

    def _normalize_payment_date(self, value: Any) -> date | None:
        if not isinstance(value, str):
            return None
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            return None
