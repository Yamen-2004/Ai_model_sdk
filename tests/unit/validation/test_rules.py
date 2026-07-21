"""Unit tests for the concrete ValidationRuleInterface implementations."""

from datetime import date, timedelta
from decimal import Decimal

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.models.domain import CustomerProfile
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.models.validation import ReasonCode
from loan_restructuring_sdk.validation.rules.identity_rule import NameExactMatchRule
from loan_restructuring_sdk.validation.rules.presence_rules import (
    NameExistsRule,
    NetSalaryExistsRule,
    PaymentDateExistsRule,
)
from loan_restructuring_sdk.validation.rules.recency_rule import PaymentDateRecencyRule

_SETTINGS = Settings()
_CUSTOMER = CustomerProfile(name="Ahmed Ali", reported_net_salary=Decimal("4500"))


def _statement(**overrides: object) -> SalaryStatement:
    defaults: dict[str, object] = {
        "employee_name": "Ahmed Ali",
        "net_salary": Decimal("4500"),
        "payment_date": date(2026, 7, 1),
    }
    defaults.update(overrides)
    return SalaryStatement(**defaults)


# --- Rule 1: Employee Name must exist ---


def test_name_exists_rule_passes_when_name_present() -> None:
    issues = NameExistsRule().evaluate(_statement(), _CUSTOMER, _SETTINGS)
    assert issues == []


def test_name_exists_rule_fails_when_name_missing() -> None:
    issues = NameExistsRule().evaluate(_statement(employee_name=None), _CUSTOMER, _SETTINGS)
    assert len(issues) == 1
    assert issues[0].reason_code == ReasonCode.NAME_MISSING


# --- Rule 2: Net Salary must exist ---


def test_net_salary_exists_rule_passes_when_present() -> None:
    issues = NetSalaryExistsRule().evaluate(_statement(), _CUSTOMER, _SETTINGS)
    assert issues == []


def test_net_salary_exists_rule_fails_when_missing() -> None:
    issues = NetSalaryExistsRule().evaluate(_statement(net_salary=None), _CUSTOMER, _SETTINGS)
    assert len(issues) == 1
    assert issues[0].reason_code == ReasonCode.NET_SALARY_MISSING


# --- Rule 3: Payment Date must exist ---


def test_payment_date_exists_rule_passes_when_present() -> None:
    issues = PaymentDateExistsRule().evaluate(_statement(), _CUSTOMER, _SETTINGS)
    assert issues == []


def test_payment_date_exists_rule_fails_when_missing() -> None:
    issues = PaymentDateExistsRule().evaluate(_statement(payment_date=None), _CUSTOMER, _SETTINGS)
    assert len(issues) == 1
    assert issues[0].reason_code == ReasonCode.PAYMENT_DATE_MISSING


# --- Rule 4: Employee Name must exactly match the customer's name ---


def test_name_exact_match_rule_passes_on_exact_match() -> None:
    issues = NameExactMatchRule().evaluate(_statement(employee_name="Ahmed Ali"), _CUSTOMER, _SETTINGS)
    assert issues == []


def test_name_exact_match_rule_fails_on_any_difference() -> None:
    issues = NameExactMatchRule().evaluate(_statement(employee_name="Ahmed Aly"), _CUSTOMER, _SETTINGS)
    assert len(issues) == 1
    assert issues[0].reason_code == ReasonCode.NAME_MISMATCH


def test_name_exact_match_rule_fails_on_case_difference() -> None:
    """No case-insensitive comparison, per explicit requirement."""
    issues = NameExactMatchRule().evaluate(_statement(employee_name="ahmed ali"), _CUSTOMER, _SETTINGS)
    assert len(issues) == 1
    assert issues[0].reason_code == ReasonCode.NAME_MISMATCH


def test_name_exact_match_rule_defers_to_presence_rule_when_name_missing() -> None:
    issues = NameExactMatchRule().evaluate(_statement(employee_name=None), _CUSTOMER, _SETTINGS)
    assert issues == []


# --- Rule 5: Payment Date must not be older than 30 days ---


def test_payment_date_recency_rule_passes_within_window() -> None:
    reference = date(2026, 7, 21)
    rule = PaymentDateRecencyRule(reference_date=reference)

    issues = rule.evaluate(_statement(payment_date=reference - timedelta(days=10)), _CUSTOMER, _SETTINGS)

    assert issues == []


def test_payment_date_recency_rule_passes_at_exactly_30_days() -> None:
    reference = date(2026, 7, 21)
    rule = PaymentDateRecencyRule(reference_date=reference)

    issues = rule.evaluate(_statement(payment_date=reference - timedelta(days=30)), _CUSTOMER, _SETTINGS)

    assert issues == []


def test_payment_date_recency_rule_fails_past_30_days() -> None:
    reference = date(2026, 7, 21)
    rule = PaymentDateRecencyRule(reference_date=reference)

    issues = rule.evaluate(_statement(payment_date=reference - timedelta(days=31)), _CUSTOMER, _SETTINGS)

    assert len(issues) == 1
    assert issues[0].reason_code == ReasonCode.STATEMENT_TOO_OLD


def test_payment_date_recency_rule_defers_to_presence_rule_when_date_missing() -> None:
    rule = PaymentDateRecencyRule(reference_date=date(2026, 7, 21))

    issues = rule.evaluate(_statement(payment_date=None), _CUSTOMER, _SETTINGS)

    assert issues == []
