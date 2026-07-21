"""Unit tests for `CaseMapper`.

`CaseMapper` is the SDK's sole DTO/domain boundary (docs/SDD.md Design
Decision D12) -- every one of its methods below needs coverage, since
nothing downstream re-checks that the mapping was done correctly.
"""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from loan_restructuring_sdk.mapping.case_mapper import CaseMapper
from loan_restructuring_sdk.models.case_dto import (
    Case,
    Customer,
    DocumentRef,
    DocumentType,
    Loan,
    RestructuringRequest,
    RestructuringType,
)
from loan_restructuring_sdk.models.domain import CaseIdentity
from loan_restructuring_sdk.utils.exceptions import CaseMappingError


def _case(**overrides: object) -> Case:
    defaults: dict[str, object] = dict(
        id=42,
        application_number="APP-2026-0042",
        status="UNDER_REVIEW",
        priority=None,
        created_at=datetime(2026, 7, 1, 9, 0, 0),
        updated_at=datetime(2026, 7, 2, 9, 0, 0),
        customer=Customer(
            id=1,
            name="Ahmed Ali",
            national_id="1234567890",
            birth_date=date(1990, 1, 1),
            employer="Acme Corp",
            monthly_salary=Decimal("5000.00"),
            net_salary=Decimal("4500.00"),
            email="ahmed@example.com",
            phone="0790000000",
        ),
        loan=Loan(
            id=2,
            account_number="ACC-1",
            loan_type="PERSONAL",
            original_amount=Decimal("10000.00"),
            remaining_balance=Decimal("8000.00"),
            current_installment=Decimal("400.00"),
            interest_rate=Decimal("5.5"),
            term_months=36,
            loan_start_date=date(2025, 1, 1),
            loan_maturity_date=date(2028, 1, 1),
            loan_status="ACTIVE",
        ),
        restructuring_request=RestructuringRequest(
            reason="فقدان الوظيفة", type=RestructuringType.DECREASE
        ),
        documents=[
            DocumentRef(type=DocumentType.SALARY_STATEMENT, file="Salary_Statement/some_file.pdf")
        ],
    )
    defaults.update(overrides)
    return Case(**defaults)


def test_to_case_identity_maps_id_and_application_number() -> None:
    identity = CaseMapper().to_case_identity(_case(id=7, application_number="APP-2026-0007"))

    assert identity == CaseIdentity(case_id=7, application_number="APP-2026-0007")


def test_to_customer_profile_maps_expected_fields() -> None:
    customer = CaseMapper().to_customer_profile(_case())

    assert customer.name == "Ahmed Ali"
    assert customer.reported_net_salary == Decimal("4500.00")


def test_to_loan_profile_maps_expected_fields() -> None:
    loan = CaseMapper().to_loan_profile(_case())

    assert loan.remaining_balance == Decimal("8000.00")
    assert loan.interest_rate_annual == Decimal("5.5")
    assert loan.current_installment == Decimal("400.00")


def test_to_document_path_resolves_salary_statement_document() -> None:
    path = CaseMapper().to_document_path(
        _case(
            documents=[
                DocumentRef(type=DocumentType.SALARY_STATEMENT, file="Salary_Statement/foo.pdf"),
            ]
        )
    )

    assert Path(path).name == "foo.pdf"
    assert Path(path).is_absolute()


def test_to_document_path_raises_when_no_salary_statement_document_present() -> None:
    with pytest.raises(CaseMappingError):
        CaseMapper().to_document_path(_case(documents=[]))


def test_to_restructuring_reason_maps_reason_text() -> None:
    reason = CaseMapper().to_restructuring_reason(
        _case(restructuring_request=RestructuringRequest(reason="مرض", type=RestructuringType.DECREASE))
    )

    assert reason == "مرض"
