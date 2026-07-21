"""Default implementation of CaseMapperInterface."""

from __future__ import annotations

from pathlib import Path

from loan_restructuring_sdk.mapping.base import CaseMapperInterface
from loan_restructuring_sdk.models.case_dto import Case, DocumentType
from loan_restructuring_sdk.models.domain import CaseIdentity, CustomerProfile, LoanProfile
from loan_restructuring_sdk.utils.exceptions import CaseMappingError

# `Case.documents[].file` is a path relative to the repo root (see
# `mock_backend/mock_data.py`'s module docstring, e.g. "Salary_Statement/case_1.pdf").
# Resolved here, once, so `to_document_path`'s caller gets a path it can read
# directly without knowing anything about how the DTO expresses file references.
_REPO_ROOT = Path(__file__).resolve().parents[3]


class CaseMapper(CaseMapperInterface):
    """Maps a `Case` DTO (backend API shape) to internal domain models/primitives (docs/SDD.md section 5.2)."""

    def to_case_identity(self, case: Case) -> CaseIdentity:
        return CaseIdentity(case_id=case.id, application_number=case.application_number)

    def to_customer_profile(self, case: Case) -> CustomerProfile:
        return CustomerProfile(name=case.customer.name, reported_net_salary=case.customer.net_salary)

    def to_loan_profile(self, case: Case) -> LoanProfile:
        return LoanProfile(
            remaining_balance=case.loan.remaining_balance,
            interest_rate_annual=case.loan.interest_rate,
            current_installment=case.loan.current_installment,
        )

    def to_document_path(self, case: Case) -> str:
        for document in case.documents:
            if document.type == DocumentType.SALARY_STATEMENT:
                return str(_REPO_ROOT / document.file)
        raise CaseMappingError(f"Case {case.id} has no SALARY_STATEMENT document to extract")

    def to_restructuring_reason(self, case: Case) -> str:
        return case.restructuring_request.reason
