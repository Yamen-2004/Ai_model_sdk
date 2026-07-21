"""Data Transfer Objects mirroring the backend API's Case payload, 1:1 (docs/SDD.md section 5.1).

These are intentionally "dumb" -- no business logic, no computed fields, no
validation beyond basic typing. `mapping.case_mapper.CaseMapper` is the only
module allowed to convert these into the internal domain models in
`models.domain` (docs/SDD.md Design Decision D10).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class RestructuringType(str, Enum):
    INCREASE = "INCREASE"
    DECREASE = "DECREASE"


class DocumentType(str, Enum):
    SALARY_STATEMENT = "SALARY_STATEMENT"


class CamelCaseModel(BaseModel):
    """Base model that accepts the backend's camelCase JSON while exposing snake_case attributes."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Customer(CamelCaseModel):
    id: int
    name: str
    national_id: str
    birth_date: date
    employer: str
    monthly_salary: Decimal
    net_salary: Decimal
    email: str
    phone: str


class Loan(CamelCaseModel):
    id: int
    account_number: str
    loan_type: str
    original_amount: Decimal
    remaining_balance: Decimal
    current_installment: Decimal
    interest_rate: Decimal
    term_months: int
    loan_start_date: date
    loan_maturity_date: date
    loan_status: str


class RestructuringRequest(CamelCaseModel):
    reason: str
    type: RestructuringType


class DocumentRef(CamelCaseModel):
    type: DocumentType
    file: str


class Case(CamelCaseModel):
    id: int
    application_number: str
    status: str
    priority: str | None = None
    created_at: datetime
    updated_at: datetime
    customer: Customer
    loan: Loan
    restructuring_request: RestructuringRequest
    documents: list[DocumentRef]
