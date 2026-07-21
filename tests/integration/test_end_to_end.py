"""End-to-end tests: `process_case()` against the fully-wired production stack.

Only the external Mistral OCR API call is mocked (at the `httpx.AsyncClient`
transport boundary, exactly like `tests/unit/ocr/test_mistral_ocr_service.py`
already does) -- every other component is the real, `api.dependencies.get_sdk()`
composition: `CaseMapper`, `Stage1Pipeline` (real `ValidationEngine` rules),
`ScenarioEngine` (real `FinancialCalculator`), `PriorityEngine` (real
`priority_keywords.json`), and `ResponseBuilder`. Document reading is real
too -- every fixture `Case` points at one of the real sample PDFs in
`Salary_Statement/`; since Mistral itself is mocked, the PDF's actual content
doesn't matter, only that a real file exists at the path `CaseMapper`
resolves.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock

import httpx

from loan_restructuring_sdk.api.dependencies import get_sdk
from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.models.case_dto import (
    Case,
    Customer,
    DocumentRef,
    DocumentType,
    Loan,
    RestructuringRequest,
    RestructuringType,
)
from loan_restructuring_sdk.models.priority import PriorityLevel
from loan_restructuring_sdk.models.response import CaseStatus, SDKResponse
from loan_restructuring_sdk.models.scenario import ScenarioName
from loan_restructuring_sdk.models.validation import ReasonCode

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SAMPLE_PDF = _REPO_ROOT / "Salary_Statement" / "mock_data_test_case_1_pass.pdf"

# Deliberately different from every test's Mistral-extracted net_salary, so a test would fail
# loudly if the pipeline ever wired the backend-reported figure into the Scenario Engine
# instead of Stage 1's verified salary (docs/SDD.md D17/D18).
_DECOY_REPORTED_SALARY = Decimal("999999.99")


def _case(
    *,
    customer_name: str = "Ahmed Ali",
    remaining_balance: str = "8000",
    interest_rate: str = "5",
    reason: str = "فقدان الوظيفة",
) -> Case:
    return Case(
        id=1,
        application_number="APP-2026-0001",
        status="UNDER_REVIEW",
        priority=None,
        created_at=datetime(2026, 7, 1, 9, 0, 0),
        updated_at=datetime(2026, 7, 1, 9, 0, 0),
        customer=Customer(
            id=1,
            name=customer_name,
            national_id="1234567890",
            birth_date=date(1990, 1, 1),
            employer="Acme Corp",
            monthly_salary=Decimal("5750.00"),
            net_salary=_DECOY_REPORTED_SALARY,
            email="ahmed@example.com",
            phone="0790000000",
        ),
        loan=Loan(
            id=1,
            account_number="ACC-1",
            loan_type="PERSONAL",
            original_amount=Decimal("10000.00"),
            remaining_balance=Decimal(remaining_balance),
            current_installment=Decimal("400.00"),
            interest_rate=Decimal(interest_rate),
            term_months=36,
            loan_start_date=date(2025, 1, 1),
            loan_maturity_date=date(2028, 1, 1),
            loan_status="ACTIVE",
        ),
        restructuring_request=RestructuringRequest(reason=reason, type=RestructuringType.DECREASE),
        documents=[DocumentRef(type=DocumentType.SALARY_STATEMENT, file=str(_SAMPLE_PDF))],
    )


def _mistral_response(employee_name: str | None, net_salary: Decimal | None, payment_date: date | None) -> httpx.Response:
    payload = {
        "employee_name": employee_name,
        "net_salary": float(net_salary) if net_salary is not None else None,
        "payment_date": payment_date.isoformat() if payment_date is not None else None,
    }
    return httpx.Response(
        status_code=200,
        json={
            "pages": [],
            "model": "mistral-ocr-latest",
            "document_annotation": json.dumps(payload),
            "usage_info": {"pages_processed": 1, "doc_size_bytes": None},
        },
        request=httpx.Request("POST", "https://example.invalid/v1/ocr"),
    )


async def _run(
    case: Case,
    employee_name: str | None,
    net_salary: Decimal | None,
    payment_date: date | None,
) -> SDKResponse:
    """Run `case` through the real, fully-wired SDK, with only the Mistral OCR HTTP call faked."""
    http_client = AsyncMock(spec=httpx.AsyncClient)
    http_client.post.return_value = _mistral_response(employee_name, net_salary, payment_date)
    sdk = get_sdk(settings=Settings(), http_client=http_client)
    return await sdk.process_case(case, as_of_date=date.today())


async def test_successful_processing() -> None:
    result = await _run(_case(), "Ahmed Ali", Decimal("5000.00"), date.today())

    assert result.status == CaseStatus.PROCESSED
    assert result.stage1.validation.passed is True
    assert result.stage1.statement is not None
    assert result.stage1.statement.net_salary == Decimal("5000.00")
    assert result.stage2 is not None
    assert len(result.stage2.scenarios) == 3
    # 55% of the verified salary (5000), never the decoy backend-reported figure (docs/SDD.md D17).
    scenario_1 = result.stage2.scenarios[0]
    assert scenario_1.monthly_installment == Decimal("2750.00")


async def test_name_mismatch_is_rejected() -> None:
    result = await _run(_case(customer_name="Ahmed Ali"), "Someone Else", Decimal("5000.00"), date.today())

    assert result.status == CaseStatus.REJECTED
    assert result.stage2 is None
    codes = {issue.reason_code for issue in result.stage1.validation.issues}
    assert ReasonCode.NAME_MISMATCH in codes


async def test_missing_salary_is_rejected() -> None:
    result = await _run(_case(), "Ahmed Ali", None, date.today())

    assert result.status == CaseStatus.REJECTED
    assert result.stage2 is None
    codes = {issue.reason_code for issue in result.stage1.validation.issues}
    assert ReasonCode.NET_SALARY_MISSING in codes


async def test_missing_payment_date_is_rejected() -> None:
    result = await _run(_case(), "Ahmed Ali", Decimal("5000.00"), None)

    assert result.status == CaseStatus.REJECTED
    assert result.stage2 is None
    codes = {issue.reason_code for issue in result.stage1.validation.issues}
    assert ReasonCode.PAYMENT_DATE_MISSING in codes


async def test_salary_statement_older_than_30_days_is_rejected() -> None:
    result = await _run(_case(), "Ahmed Ali", Decimal("5000.00"), date(2020, 1, 1))

    assert result.status == CaseStatus.REJECTED
    assert result.stage2 is None
    codes = {issue.reason_code for issue in result.stage1.validation.issues}
    assert ReasonCode.STATEMENT_TOO_OLD in codes


async def test_high_priority_reason() -> None:
    result = await _run(_case(reason="فقدان الوظيفة"), "Ahmed Ali", Decimal("5000.00"), date.today())

    assert result.status == CaseStatus.PROCESSED
    assert result.stage2 is not None
    assert result.stage2.priority.level == PriorityLevel.HIGH


async def test_medium_priority_reason() -> None:
    result = await _run(_case(reason="تخفيض الراتب"), "Ahmed Ali", Decimal("5000.00"), date.today())

    assert result.status == CaseStatus.PROCESSED
    assert result.stage2 is not None
    assert result.stage2.priority.level == PriorityLevel.MEDIUM


async def test_low_priority_reason() -> None:
    result = await _run(_case(reason="شراء سيارة"), "Ahmed Ali", Decimal("5000.00"), date.today())

    assert result.status == CaseStatus.PROCESSED
    assert result.stage2 is not None
    assert result.stage2.priority.level == PriorityLevel.LOW


async def test_multiple_priority_keywords_returns_the_highest() -> None:
    result = await _run(
        _case(reason="تخفيض الراتب بسبب فقدان الوظيفة"), "Ahmed Ali", Decimal("5000.00"), date.today()
    )

    assert result.status == CaseStatus.PROCESSED
    assert result.stage2 is not None
    assert result.stage2.priority.level == PriorityLevel.HIGH


async def test_scenario_2_affordability_warning() -> None:
    case = _case(remaining_balance="50000", interest_rate="10")

    result = await _run(case, "Ahmed Ali", Decimal("200.00"), date.today())

    assert result.status == CaseStatus.PROCESSED
    assert result.stage2 is not None
    scenario_2 = result.stage2.scenarios[1]
    assert scenario_2.name == ScenarioName.SCENARIO_2_MIN_INSTALLMENT
    assert scenario_2.feasible is True
    assert scenario_2.notes is not None
    assert "exceeds the recommended affordability" in scenario_2.notes
