"""Internal domain models -- what Stage 1 and Stage 2 actually operate on.

Derived from `models.case_dto` by `mapping.case_mapper.CaseMapper`. Nothing
downstream of the mapping boundary should import `case_dto` directly --
including the Response Builder, which only ever sees `CaseIdentity`, never
the full `Case` (docs/SDD.md Design Decisions D10 / D12, Goal G6).
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class CaseIdentity(BaseModel):
    """The minimal case-identifying information business logic and the Response Builder need.

    Deliberately holds nothing beyond these two identifiers -- everything
    else about a case (customer, loan, document, reason) has its own
    dedicated domain model. This is what keeps `ResponseBuilder` decoupled
    from the `Case` DTO shape (docs/SDD.md Design Decision D12).
    """

    case_id: int
    application_number: str


class CustomerProfile(BaseModel):
    """The subset of customer data the SDK's business logic needs.

    `name` drives Stage 1's exact-match identity check (D4). `reported_net_salary`
    is the backend's own figure -- reference metadata only, carried for
    display/audit purposes. It is deliberately never read by the Scenario
    Engine or any other calculation: after Stage 1 succeeds, the *verified*
    net salary extracted from the salary statement (`SalaryStatement.net_salary`)
    is the sole source of truth for salary-driven restructuring math, passed
    into the Scenario Engine as its own explicit parameter rather than
    pulled off this model (docs/SDD.md Design Decision D17).
    """

    name: str
    reported_net_salary: Decimal


class LoanProfile(BaseModel):
    """The subset of loan data the Financial Calculator and Scenario Engine need."""

    remaining_balance: Decimal
    interest_rate_annual: Decimal
    current_installment: Decimal
