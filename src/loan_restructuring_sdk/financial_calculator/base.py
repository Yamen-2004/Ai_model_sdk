"""Interface for the Financial Calculator."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from loan_restructuring_sdk.models.loan_calculation import LoanCalculation


class FinancialCalculatorInterface(ABC):
    """Computes a full loan amortization outcome for a fixed monthly installment."""

    @abstractmethod
    def calculate(
        self,
        remaining_balance: Decimal,
        annual_interest_rate: Decimal,
        monthly_installment: Decimal,
        as_of_date: date,
    ) -> LoanCalculation:
        """Compute the amortization outcome of paying `monthly_installment` per month starting `as_of_date`.

        `as_of_date` has no default: a hidden `date.today()` would make the
        result depend on wall-clock time, which contradicts this module
        being fully deterministic.

        Raises a `LoanCalculationError` subclass (`utils.exceptions`) for
        invalid or mathematically infeasible inputs -- never returns a
        partial or approximate result.
        """
        raise NotImplementedError

    @abstractmethod
    def calculate_installment_for_duration(
        self,
        remaining_balance: Decimal,
        annual_interest_rate: Decimal,
        target_duration_months: int,
    ) -> Decimal:
        """Return the fixed monthly installment that fully amortizes `remaining_balance` over `target_duration_months`.

        Closed-form (the standard annuity-payment formula) -- no iterative
        or brute-force search. The result is rounded *up* to the nearest
        cent, never to nearest: rounding down could push the real
        (cents-quantized) amortization duration one month past
        `target_duration_months`, since duration is monotonically
        decreasing in installment size. Rounding up guarantees the actual
        duration never exceeds the target once `calculate()` is called
        with this installment.

        Raises a `LoanCalculationError` subclass for invalid inputs
        (`remaining_balance <= 0`, `annual_interest_rate < 0`,
        `target_duration_months <= 0`).
        """
        raise NotImplementedError
