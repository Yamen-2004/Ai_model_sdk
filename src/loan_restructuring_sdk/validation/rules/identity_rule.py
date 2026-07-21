"""Exact-match identity check (docs/SDD.md Design Decision D4 -- no fuzzy matching)."""

from __future__ import annotations

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.models.domain import CustomerProfile
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.models.validation import ReasonCode, ValidationIssue
from loan_restructuring_sdk.validation.base import ValidationRuleInterface


class NameExactMatchRule(ValidationRuleInterface):
    """Fails with ReasonCode.NAME_MISMATCH unless the extracted name exactly matches the customer's name.

    Exact string equality only -- no case-folding, no whitespace
    normalization beyond what `SalaryStatementBuilder` already applies, no
    fuzzy/similarity matching (docs/SDD.md Design Decision D4).
    """

    def evaluate(
        self,
        statement: SalaryStatement,
        customer: CustomerProfile,
        settings: Settings,
    ) -> list[ValidationIssue]:
        if statement.employee_name is None:
            # NameExistsRule already reports the missing-name case.
            return []
        if statement.employee_name == customer.name:
            return []
        return [
            ValidationIssue(
                rule_name="NameExactMatchRule",
                reason_code=ReasonCode.NAME_MISMATCH,
                detail=(
                    f"Extracted employee name '{statement.employee_name}' does not exactly match "
                    f"the customer's name '{customer.name}'."
                ),
            )
        ]
