"""Unit tests for `ValidationEngine` -- aggregation behavior (docs/SDD.md Design Decision D2)."""

from datetime import date
from decimal import Decimal

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.models.domain import CustomerProfile
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.models.validation import ReasonCode, ValidationIssue
from loan_restructuring_sdk.validation.base import ValidationRuleInterface
from loan_restructuring_sdk.validation.validation_engine import ValidationEngine

_SETTINGS = Settings()
_CUSTOMER = CustomerProfile(name="Ahmed Ali", reported_net_salary=Decimal("4500"))
_STATEMENT = SalaryStatement(
    employee_name="Ahmed Ali", net_salary=Decimal("4500"), payment_date=date(2026, 7, 1)
)


class _AlwaysPassRule(ValidationRuleInterface):
    def evaluate(self, statement, customer, settings) -> list[ValidationIssue]:
        return []


class _AlwaysFailRule(ValidationRuleInterface):
    def __init__(self, rule_name: str, reason_code: ReasonCode) -> None:
        self._rule_name = rule_name
        self._reason_code = reason_code

    def evaluate(self, statement, customer, settings) -> list[ValidationIssue]:
        return [ValidationIssue(rule_name=self._rule_name, reason_code=self._reason_code, detail="failed")]


def test_run_returns_passed_true_when_no_rule_fails() -> None:
    engine = ValidationEngine(rules=[_AlwaysPassRule(), _AlwaysPassRule()])

    outcome = engine.run(_STATEMENT, _CUSTOMER, _SETTINGS)

    assert outcome.passed is True
    assert outcome.issues == []


def test_run_aggregates_issues_from_every_failing_rule() -> None:
    engine = ValidationEngine(
        rules=[
            _AlwaysFailRule("RuleA", ReasonCode.NAME_MISSING),
            _AlwaysPassRule(),
            _AlwaysFailRule("RuleB", ReasonCode.NET_SALARY_MISSING),
        ]
    )

    outcome = engine.run(_STATEMENT, _CUSTOMER, _SETTINGS)

    assert outcome.passed is False
    assert [issue.rule_name for issue in outcome.issues] == ["RuleA", "RuleB"]


def test_run_does_not_stop_at_first_failure() -> None:
    """Explicit requirement: never stop at the first error."""
    engine = ValidationEngine(
        rules=[
            _AlwaysFailRule("RuleA", ReasonCode.NAME_MISSING),
            _AlwaysFailRule("RuleB", ReasonCode.NET_SALARY_MISSING),
            _AlwaysFailRule("RuleC", ReasonCode.PAYMENT_DATE_MISSING),
        ]
    )

    outcome = engine.run(_STATEMENT, _CUSTOMER, _SETTINGS)

    assert len(outcome.issues) == 3
