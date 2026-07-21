"""The final response contract returned by `LoanRestructuringSDK.process_case()` (docs/SDD.md section 5.5)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from loan_restructuring_sdk.models.priority import PriorityResult
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.models.scenario import Scenario
from loan_restructuring_sdk.models.validation import ValidationOutcome


class CaseStatus(str, Enum):
    REJECTED = "REJECTED"
    PROCESSED = "PROCESSED"


class Stage1Result(BaseModel):
    """Output of Stage 1 -- Extraction & Validation."""

    statement: SalaryStatement | None
    validation: ValidationOutcome


class Stage2Result(BaseModel):
    """Output of Stage 2 -- Calculation, Scenarios & Priority. Only produced if Stage 1 passes."""

    scenarios: list[Scenario]
    priority: PriorityResult


class SDKResponse(BaseModel):
    """The single return type of `process_case()`, covering both the REJECTED and PROCESSED paths."""

    case_id: int
    application_number: str
    status: CaseStatus
    stage1: Stage1Result
    stage2: Stage2Result | None = None
    generated_at: datetime
