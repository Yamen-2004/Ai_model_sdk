"""Stage 2 priority-scoring types (docs/SDD.md Design Decisions D7-D9)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from loan_restructuring_sdk.models.domain import CustomerProfile, LoanProfile
from loan_restructuring_sdk.models.salary_statement import SalaryStatement


class PriorityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PriorityContext(BaseModel):
    """Everything a PriorityRuleInterface implementation might need -- current and future.

    Only `restructuring_reason` is read by the v1 keyword rule. `loan`,
    `customer`, and `statement` are carried so future rules (loan amount,
    remaining balance, salary, delayed installments, credit score) are
    additive -- a new rule reads a field already present here instead of
    requiring a breaking signature change (docs/SDD.md Design Decision D9).
    """

    restructuring_reason: str
    loan: LoanProfile
    customer: CustomerProfile
    statement: SalaryStatement


class PriorityVote(BaseModel):
    """A single rule's contribution to the final priority decision.

    Always emitted, even when the rule doesn't fire (`level=None`), so the
    final PriorityResult is fully auditable -- no rule's non-vote is silently
    dropped.
    """

    rule_name: str
    level: PriorityLevel | None = None
    matched: list[str] = Field(default_factory=list)
    detail: str


class PriorityResult(BaseModel):
    """Aggregated result of running every configured PriorityRuleInterface."""

    level: PriorityLevel
    votes: list[PriorityVote] = Field(default_factory=list)
