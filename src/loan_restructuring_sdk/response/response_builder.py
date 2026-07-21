"""Default implementation of ResponseBuilderInterface."""

from __future__ import annotations

from datetime import datetime

from loan_restructuring_sdk.models.domain import CaseIdentity
from loan_restructuring_sdk.models.priority import PriorityResult
from loan_restructuring_sdk.models.response import CaseStatus, SDKResponse, Stage1Result, Stage2Result
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.models.scenario import Scenario
from loan_restructuring_sdk.models.validation import ValidationOutcome
from loan_restructuring_sdk.response.base import ResponseBuilderInterface


class ResponseBuilder(ResponseBuilderInterface):
    """Assembles SDKResponse objects from Stage 1 / Stage 2 outputs -- pure domain models in, SDKResponse out."""

    def build_rejected(
        self,
        case_identity: CaseIdentity,
        statement: SalaryStatement | None,
        validation: ValidationOutcome,
        generated_at: datetime,
    ) -> SDKResponse:
        return SDKResponse(
            case_id=case_identity.case_id,
            application_number=case_identity.application_number,
            status=CaseStatus.REJECTED,
            stage1=Stage1Result(statement=statement, validation=validation),
            stage2=None,
            generated_at=generated_at,
        )

    def build_processed(
        self,
        case_identity: CaseIdentity,
        statement: SalaryStatement,
        validation: ValidationOutcome,
        scenarios: list[Scenario],
        priority: PriorityResult,
        generated_at: datetime,
    ) -> SDKResponse:
        return SDKResponse(
            case_id=case_identity.case_id,
            application_number=case_identity.application_number,
            status=CaseStatus.PROCESSED,
            stage1=Stage1Result(statement=statement, validation=validation),
            stage2=Stage2Result(scenarios=scenarios, priority=priority),
            generated_at=generated_at,
        )
