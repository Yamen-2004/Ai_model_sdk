"""Default implementation of ValidationEngineInterface."""

from __future__ import annotations

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.models.domain import CustomerProfile
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.models.validation import ValidationIssue, ValidationOutcome
from loan_restructuring_sdk.validation.base import ValidationEngineInterface, ValidationRuleInterface


class ValidationEngine(ValidationEngineInterface):
    """Runs a configured list of ValidationRuleInterface implementations and aggregates their issues."""

    def __init__(self, rules: list[ValidationRuleInterface]) -> None:
        self._rules = rules

    def run(
        self,
        statement: SalaryStatement,
        customer: CustomerProfile,
        settings: Settings,
    ) -> ValidationOutcome:
        issues: list[ValidationIssue] = []
        for rule in self._rules:
            issues.extend(rule.evaluate(statement, customer, settings))
        return ValidationOutcome(passed=not issues, issues=issues)
