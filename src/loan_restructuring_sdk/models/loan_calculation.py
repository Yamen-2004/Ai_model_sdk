"""Output of the Financial Calculator: the full amortization outcome for a fixed monthly installment."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class LoanCalculation(BaseModel):
    """A fully-determined loan amortization result. Pure data -- no behavior, no business meaning attached."""

    monthly_installment: Decimal
    loan_duration_months: int
    loan_end_date: date
    total_interest: Decimal
    total_payment: Decimal
