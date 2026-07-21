"""Public facade for the Loan Restructuring SDK: the single entry point, `process_case()`.

Orchestrates Stage 1 (`Stage1Pipeline`: PDF Extraction Engine -> Validation
Engine) and, only if validation passes, Stage 2 (Loan Scenario Engine ->
Priority Engine), then hands off to the Response Builder. Everything else
in this package is internal; this class + `models/` are the only stable,
versioned surface (docs/SDD.md sections 3, 5.6, and 7).

`Case` (the backend API DTO) exists only at this facade's boundary: the
implementation of `process_case()` passes `case` straight to
`self._case_mapper` and nowhere else -- every field access happens inside
`CaseMapperInterface` methods. No engine, rule, strategy, or the Response
Builder ever sees a `Case`; they only ever receive `CaseIdentity`,
`CustomerProfile`, `LoanProfile`, and plain primitives (docs/SDD.md Design
Decisions D10 / D12). This is what lets the backend's API evolve without
touching business logic.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.mapping.base import CaseMapperInterface
from loan_restructuring_sdk.models.case_dto import Case
from loan_restructuring_sdk.models.priority import PriorityContext
from loan_restructuring_sdk.models.response import SDKResponse
from loan_restructuring_sdk.priority.base import PriorityEngineInterface
from loan_restructuring_sdk.response.base import ResponseBuilderInterface
from loan_restructuring_sdk.scenarios.base import ScenarioEngineInterface
from loan_restructuring_sdk.stage1_pipeline import Stage1Pipeline
from loan_restructuring_sdk.utils.exceptions import DocumentReadError


class LoanRestructuringSDK:
    """Composes every engine/service via constructor injection and exposes `process_case()`."""

    def __init__(
        self,
        case_mapper: CaseMapperInterface,
        stage1_pipeline: Stage1Pipeline,
        scenario_engine: ScenarioEngineInterface,
        priority_engine: PriorityEngineInterface,
        response_builder: ResponseBuilderInterface,
        settings: Settings,
    ) -> None:
        self._case_mapper = case_mapper
        self._stage1_pipeline = stage1_pipeline
        self._scenario_engine = scenario_engine
        self._priority_engine = priority_engine
        self._response_builder = response_builder
        self._settings = settings

    async def process_case(self, case: Case, as_of_date: date | None = None) -> SDKResponse:
        """Run Stage 1, then (if it passes) Stage 2, and return the final SDKResponse.

        `as_of_date` defaults to today but is injectable for deterministic
        tests -- the same pattern `PaymentDateRecencyRule` already uses,
        rather than letting a hidden `date.today()` live inside an engine
        (docs/SDD.md Design Decisions D16, D20-adjacent).

        Raises only for structural failures the caller must fix before
        retrying (e.g. an unreadable document, a malformed Case) -- a
        business-rule rejection is always a normal SDKResponse, never an
        exception (docs/SDD.md section 5.6).
        """
        case_identity = self._case_mapper.to_case_identity(case)
        customer = self._case_mapper.to_customer_profile(case)
        loan = self._case_mapper.to_loan_profile(case)
        document_path = self._case_mapper.to_document_path(case)
        restructuring_reason = self._case_mapper.to_restructuring_reason(case)

        pdf_bytes = self._read_document(document_path)
        stage1_result = await self._stage1_pipeline.run(pdf_bytes, customer)
        generated_at = datetime.now(timezone.utc)

        if not stage1_result.validation.passed:
            return self._response_builder.build_rejected(
                case_identity, stage1_result.statement, stage1_result.validation, generated_at
            )

        # Guaranteed non-None: Stage1ResponseBuilder only nulls `statement` when
        # `validation.passed` is False (already handled above).
        statement = stage1_result.statement
        assert statement is not None
        assert statement.net_salary is not None  # guaranteed by NetSalaryExistsRule passing

        scenarios = self._scenario_engine.generate(
            customer, loan, statement.net_salary, self._settings, as_of_date or date.today()
        )
        priority = self._priority_engine.evaluate(
            PriorityContext(
                restructuring_reason=restructuring_reason,
                loan=loan,
                customer=customer,
                statement=statement,
            )
        )

        return self._response_builder.build_processed(
            case_identity,
            statement,
            stage1_result.validation,
            scenarios.scenarios,
            priority,
            generated_at,
        )

    @staticmethod
    def _read_document(path: str) -> bytes:
        try:
            return Path(path).read_bytes()
        except OSError as exc:
            raise DocumentReadError(f"Could not read salary statement document: {path}") from exc
