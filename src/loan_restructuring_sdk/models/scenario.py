"""Stage 2 scenario result types (docs/SDD.md section 5.4 / 6 / Design Decisions D6, D15).

`Scenario`'s amortization fields (`monthly_installment`, `loan_duration_months`,
`loan_end_date`, `total_interest`, `total_payment`) come straight from the
Financial Calculator's `LoanCalculation` output when `feasible=True`; the
Scenario Engine adds `name`, `feasible`, and `notes` on top. They're
nullable because when `feasible=False` (the calculator raised
`InfeasiblePaymentError`), there is no amortization outcome to report --
only the installment that was attempted and why it failed.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class ScenarioName(str, Enum):
    SCENARIO_1_MAX_AFFORDABILITY = "SCENARIO_1_MAX_AFFORDABILITY"
    SCENARIO_2_MIN_INSTALLMENT = "SCENARIO_2_MIN_INSTALLMENT"
    SCENARIO_3_BALANCED = "SCENARIO_3_BALANCED"


class Scenario(BaseModel):
    """One restructuring option.

    `feasible=False` when the Financial Calculator raised
    `InfeasiblePaymentError` for this scenario's installment (docs/SDD.md
    Design Decision D6, revised v2.3) -- the Scenario Engine catches that
    exception and reports it as data instead of letting the whole case
    processing crash. `notes` is also used for non-fatal warnings on an
    otherwise feasible scenario (e.g. Scenario 2 exceeding the 55%
    affordability guideline, docs/SDD.md Design Decision D15) -- `feasible`
    and `notes` are independent: a scenario can be feasible *and* carry a
    warning.
    """

    name: ScenarioName
    monthly_installment: Decimal
    loan_duration_months: int | None = None
    loan_end_date: date | None = None
    total_interest: Decimal | None = None
    total_payment: Decimal | None = None
    feasible: bool
    notes: str | None = None


class ScenarioCollection(BaseModel):
    """The Scenario Engine's output: always exactly three scenarios, enforced at construction time."""

    scenarios: list[Scenario] = Field(min_length=3, max_length=3)
