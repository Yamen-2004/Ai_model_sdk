"""Interface for mapping backend DTOs into internal domain models (docs/SDD.md Design Decisions D10 / D12).

This is deliberately the *only* interface in the SDK allowed to accept a
`Case` (or any of its nested DTOs) as a parameter. Every field of `Case`
that any downstream module needs has a dedicated mapper method here -- so
`sdk.py` can receive the raw `Case` at its boundary and immediately hand
every field access off to this mapper, without any engine, rule, strategy,
or the Response Builder ever importing `models.case_dto` themselves.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from loan_restructuring_sdk.models.case_dto import Case
from loan_restructuring_sdk.models.domain import CaseIdentity, CustomerProfile, LoanProfile


class CaseMapperInterface(ABC):
    """Converts a `Case` DTO into the domain models/primitives the rest of the SDK operates on."""

    @abstractmethod
    def to_case_identity(self, case: Case) -> CaseIdentity:
        """Map `case.id` / `case.application_number` to a `CaseIdentity` (all the Response Builder needs)."""
        raise NotImplementedError

    @abstractmethod
    def to_customer_profile(self, case: Case) -> CustomerProfile:
        """Map `case.customer` to a `CustomerProfile`."""
        raise NotImplementedError

    @abstractmethod
    def to_loan_profile(self, case: Case) -> LoanProfile:
        """Map `case.loan` to a `LoanProfile`."""
        raise NotImplementedError

    @abstractmethod
    def to_document_path(self, case: Case) -> str:
        """Resolve the salary-statement document reference (`case.documents`) to a readable path/URI."""
        raise NotImplementedError

    @abstractmethod
    def to_restructuring_reason(self, case: Case) -> str:
        """Map `case.restructuring_request.reason` -- the Priority Engine's raw text input."""
        raise NotImplementedError
