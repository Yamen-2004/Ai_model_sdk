"""Unit tests for `Stage1ResponseBuilder`."""

from datetime import date
from decimal import Decimal

from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.models.validation import ReasonCode, ValidationIssue, ValidationOutcome
from loan_restructuring_sdk.response.stage1_response_builder import Stage1ResponseBuilder

_STATEMENT = SalaryStatement(
    employee_name="Ahmed Ali", net_salary=Decimal("4500"), payment_date=date(2026, 7, 1)
)


def test_build_returns_extracted_data_when_validation_passed() -> None:
    validation = ValidationOutcome(passed=True, issues=[])
    builder = Stage1ResponseBuilder()

    result = builder.build(_STATEMENT, validation)

    assert result.statement == _STATEMENT
    assert result.validation.passed is True


def test_build_nulls_extracted_data_when_validation_failed() -> None:
    validation = ValidationOutcome(
        passed=False,
        issues=[ValidationIssue(rule_name="NameExistsRule", reason_code=ReasonCode.NAME_MISSING, detail="x")],
    )
    builder = Stage1ResponseBuilder()

    result = builder.build(_STATEMENT, validation)

    assert result.statement is None
    assert result.validation.passed is False
    assert len(result.validation.issues) == 1


def test_build_retains_all_rejection_reasons() -> None:
    validation = ValidationOutcome(
        passed=False,
        issues=[
            ValidationIssue(rule_name="NameExistsRule", reason_code=ReasonCode.NAME_MISSING, detail="x"),
            ValidationIssue(
                rule_name="PaymentDateRecencyRule", reason_code=ReasonCode.STATEMENT_TOO_OLD, detail="y"
            ),
        ],
    )
    builder = Stage1ResponseBuilder()

    result = builder.build(_STATEMENT, validation)

    assert [issue.reason_code for issue in result.validation.issues] == [
        ReasonCode.NAME_MISSING,
        ReasonCode.STATEMENT_TOO_OLD,
    ]
