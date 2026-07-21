"""Interface for the Response Builder -- assembles the final SDKResponse for both outcomes.

Takes a `CaseIdentity`, never a `Case` DTO: the Response Builder is the
last step in the pipeline (docs/SDD.md section 3) and has no business
reason to know anything about the backend's API shape -- it only needs the
two identifiers that go into `SDKResponse` (docs/SDD.md Design Decision D12).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from loan_restructuring_sdk.models.domain import CaseIdentity
from loan_restructuring_sdk.models.priority import PriorityResult
from loan_restructuring_sdk.models.response import SDKResponse
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.models.scenario import Scenario
from loan_restructuring_sdk.models.validation import ValidationOutcome


class ResponseBuilderInterface(ABC):
    """Builds the final SDKResponse returned by `sdk.process_case()` (docs/SDD.md section 5.5)."""

    @abstractmethod
    def build_rejected(
        self,
        case_identity: CaseIdentity,
        statement: SalaryStatement | None,
        validation: ValidationOutcome,
        generated_at: datetime,
    ) -> SDKResponse:
        """Build a REJECTED response -- returned immediately when Stage 1 validation fails.

        `generated_at` has no default, for the same reason `as_of_date`
        doesn't on the Financial Calculator / Scenario Engine (docs/SDD.md
        Design Decision D16): the caller supplies the wall-clock time once,
        at the `process_case()` boundary, rather than the builder reading
        it itself -- keeping this class a pure function of its inputs.
        """
        raise NotImplementedError

    @abstractmethod
    def build_processed(
        self,
        case_identity: CaseIdentity,
        statement: SalaryStatement,
        validation: ValidationOutcome,
        scenarios: list[Scenario],
        priority: PriorityResult,
        generated_at: datetime,
    ) -> SDKResponse:
        """Build a PROCESSED response -- returned when both Stage 1 and Stage 2 complete successfully."""
        raise NotImplementedError
