"""Unit tests for `Stage1Pipeline` -- the full Stage 1 flow, minus the real Mistral OCR call.

Only the OCR/extraction step is faked (standing in for "Mistral is
mocked"); the Validation Engine, its 5 rules, and the Stage 1 Response
Builder are the real implementations, since they're fast, deterministic,
and exactly what this pipeline exists to wire together correctly.
"""

from datetime import date
from decimal import Decimal

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.extraction.base import PDFExtractionEngineInterface
from loan_restructuring_sdk.models.domain import CustomerProfile
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.models.validation import ReasonCode
from loan_restructuring_sdk.response.stage1_response_builder import Stage1ResponseBuilder
from loan_restructuring_sdk.stage1_pipeline import Stage1Pipeline
from loan_restructuring_sdk.validation.rules.identity_rule import NameExactMatchRule
from loan_restructuring_sdk.validation.rules.presence_rules import (
    NameExistsRule,
    NetSalaryExistsRule,
    PaymentDateExistsRule,
)
from loan_restructuring_sdk.validation.rules.recency_rule import PaymentDateRecencyRule
from loan_restructuring_sdk.validation.validation_engine import ValidationEngine

_TODAY = date(2026, 7, 21)
_CUSTOMER = CustomerProfile(name="Ahmed Ali", reported_net_salary=Decimal("4500"))


class _FakeExtractionEngine(PDFExtractionEngineInterface):
    """Stands in for the real Mistral-backed PDFExtractionEngine -- returns a preset SalaryStatement."""

    def __init__(self, statement: SalaryStatement) -> None:
        self._statement = statement

    async def extract(self, pdf_bytes: bytes) -> SalaryStatement:
        return self._statement


def _build_pipeline(statement: SalaryStatement) -> Stage1Pipeline:
    validation_engine = ValidationEngine(
        rules=[
            NameExistsRule(),
            NetSalaryExistsRule(),
            PaymentDateExistsRule(),
            NameExactMatchRule(),
            PaymentDateRecencyRule(reference_date=_TODAY),
        ]
    )
    return Stage1Pipeline(
        extraction_engine=_FakeExtractionEngine(statement),
        validation_engine=validation_engine,
        response_builder=Stage1ResponseBuilder(),
        settings=Settings(),
    )


async def test_success() -> None:
    statement = SalaryStatement(
        employee_name="Ahmed Ali", net_salary=Decimal("4500"), payment_date=_TODAY
    )
    pipeline = _build_pipeline(statement)

    result = await pipeline.run(pdf_bytes=b"pdf", customer=_CUSTOMER)

    assert result.validation.passed is True
    assert result.validation.issues == []
    assert result.statement == statement


async def test_missing_name() -> None:
    statement = SalaryStatement(employee_name=None, net_salary=Decimal("4500"), payment_date=_TODAY)
    pipeline = _build_pipeline(statement)

    result = await pipeline.run(pdf_bytes=b"pdf", customer=_CUSTOMER)

    assert result.validation.passed is False
    assert result.statement is None
    assert ReasonCode.NAME_MISSING in [issue.reason_code for issue in result.validation.issues]


async def test_missing_salary() -> None:
    statement = SalaryStatement(employee_name="Ahmed Ali", net_salary=None, payment_date=_TODAY)
    pipeline = _build_pipeline(statement)

    result = await pipeline.run(pdf_bytes=b"pdf", customer=_CUSTOMER)

    assert result.validation.passed is False
    assert result.statement is None
    assert ReasonCode.NET_SALARY_MISSING in [issue.reason_code for issue in result.validation.issues]


async def test_missing_payment_date() -> None:
    statement = SalaryStatement(employee_name="Ahmed Ali", net_salary=Decimal("4500"), payment_date=None)
    pipeline = _build_pipeline(statement)

    result = await pipeline.run(pdf_bytes=b"pdf", customer=_CUSTOMER)

    assert result.validation.passed is False
    assert result.statement is None
    assert ReasonCode.PAYMENT_DATE_MISSING in [issue.reason_code for issue in result.validation.issues]


async def test_name_mismatch() -> None:
    statement = SalaryStatement(
        employee_name="Someone Else", net_salary=Decimal("4500"), payment_date=_TODAY
    )
    pipeline = _build_pipeline(statement)

    result = await pipeline.run(pdf_bytes=b"pdf", customer=_CUSTOMER)

    assert result.validation.passed is False
    assert result.statement is None
    assert ReasonCode.NAME_MISMATCH in [issue.reason_code for issue in result.validation.issues]


async def test_statement_older_than_30_days() -> None:
    stale_date = date(2026, 6, 1)  # 50 days before _TODAY
    statement = SalaryStatement(
        employee_name="Ahmed Ali", net_salary=Decimal("4500"), payment_date=stale_date
    )
    pipeline = _build_pipeline(statement)

    result = await pipeline.run(pdf_bytes=b"pdf", customer=_CUSTOMER)

    assert result.validation.passed is False
    assert result.statement is None
    assert ReasonCode.STATEMENT_TOO_OLD in [issue.reason_code for issue in result.validation.issues]


async def test_collects_all_failures_at_once() -> None:
    """Explicit requirement: never stop at the first error."""
    statement = SalaryStatement(employee_name=None, net_salary=None, payment_date=None)
    pipeline = _build_pipeline(statement)

    result = await pipeline.run(pdf_bytes=b"pdf", customer=_CUSTOMER)

    reason_codes = {issue.reason_code for issue in result.validation.issues}
    assert reason_codes == {
        ReasonCode.NAME_MISSING,
        ReasonCode.NET_SALARY_MISSING,
        ReasonCode.PAYMENT_DATE_MISSING,
    }
