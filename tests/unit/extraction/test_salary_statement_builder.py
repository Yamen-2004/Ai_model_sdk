"""Unit tests for `SalaryStatementBuilder` -- transformation only, never raises."""

from datetime import date
from decimal import Decimal

from loan_restructuring_sdk.extraction.salary_statement_builder import SalaryStatementBuilder


def test_build_normalizes_all_fields_when_present() -> None:
    builder = SalaryStatementBuilder()

    statement = builder.build(
        {"employee_name": "  Ahmed Ali  ", "net_salary": 4500, "payment_date": "2026-07-01"}
    )

    assert statement.employee_name == "Ahmed Ali"
    assert statement.net_salary == Decimal("4500")
    assert statement.payment_date == date(2026, 7, 1)


def test_build_returns_none_for_missing_employee_name() -> None:
    builder = SalaryStatementBuilder()

    statement = builder.build({"employee_name": None, "net_salary": 4500, "payment_date": "2026-07-01"})

    assert statement.employee_name is None


def test_build_returns_none_for_blank_employee_name() -> None:
    builder = SalaryStatementBuilder()

    statement = builder.build({"employee_name": "   ", "net_salary": 4500, "payment_date": "2026-07-01"})

    assert statement.employee_name is None


def test_build_returns_none_for_missing_net_salary() -> None:
    builder = SalaryStatementBuilder()

    statement = builder.build({"employee_name": "Ahmed Ali", "net_salary": None, "payment_date": "2026-07-01"})

    assert statement.net_salary is None


def test_build_returns_none_for_unparsable_net_salary() -> None:
    builder = SalaryStatementBuilder()

    statement = builder.build(
        {"employee_name": "Ahmed Ali", "net_salary": "not-a-number", "payment_date": "2026-07-01"}
    )

    assert statement.net_salary is None


def test_build_returns_none_for_missing_payment_date() -> None:
    builder = SalaryStatementBuilder()

    statement = builder.build({"employee_name": "Ahmed Ali", "net_salary": 4500, "payment_date": None})

    assert statement.payment_date is None


def test_build_returns_none_for_unparsable_payment_date() -> None:
    builder = SalaryStatementBuilder()

    statement = builder.build(
        {"employee_name": "Ahmed Ali", "net_salary": 4500, "payment_date": "30th of July"}
    )

    assert statement.payment_date is None


def test_build_retains_raw_extraction() -> None:
    builder = SalaryStatementBuilder()
    raw = {"employee_name": "Ahmed Ali", "net_salary": 4500, "payment_date": "2026-07-01"}

    statement = builder.build(raw)

    assert statement.raw_extraction == raw
