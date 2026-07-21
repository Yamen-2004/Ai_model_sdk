"""Stage 1 validation result types (docs/SDD.md section 5.3)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ReasonCode(str, Enum):
    NAME_MISSING = "NAME_MISSING"
    NET_SALARY_MISSING = "NET_SALARY_MISSING"
    PAYMENT_DATE_MISSING = "PAYMENT_DATE_MISSING"
    NAME_MISMATCH = "NAME_MISMATCH"
    STATEMENT_TOO_OLD = "STATEMENT_TOO_OLD"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"


class ValidationIssue(BaseModel):
    """A single failing rule's reason -- one of possibly several (docs/SDD.md Design Decision D2)."""

    rule_name: str
    reason_code: ReasonCode
    detail: str


class ValidationOutcome(BaseModel):
    """Aggregated result of running every configured ValidationRuleInterface."""

    passed: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
