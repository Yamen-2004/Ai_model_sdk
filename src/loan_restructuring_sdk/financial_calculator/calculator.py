"""Default implementation of FinancialCalculatorInterface."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from loan_restructuring_sdk.financial_calculator import amortization_math
from loan_restructuring_sdk.financial_calculator.base import FinancialCalculatorInterface
from loan_restructuring_sdk.models.loan_calculation import LoanCalculation
from loan_restructuring_sdk.utils.datetime_utils import add_months
from loan_restructuring_sdk.utils.exceptions import (
    InfeasiblePaymentError,
    InvalidDurationError,
    InvalidInstallmentError,
    InvalidInterestRateError,
    InvalidPrincipalError,
)

_CENT = Decimal("0.01")


class FinancialCalculator(FinancialCalculatorInterface):
    """Standard fixed-payment amortized-loan calculator. Pure math -- no business rules."""

    def calculate(
        self,
        remaining_balance: Decimal,
        annual_interest_rate: Decimal,
        monthly_installment: Decimal,
        as_of_date: date,
    ) -> LoanCalculation:
        self._validate_principal(remaining_balance)
        self._validate_interest_rate(annual_interest_rate)
        if monthly_installment <= 0:
            raise InvalidInstallmentError(f"Monthly installment must be > 0, got {monthly_installment}.")

        monthly_rate = amortization_math.monthly_rate_from_annual(annual_interest_rate)
        if monthly_rate > 0:
            monthly_interest_only = remaining_balance * monthly_rate
            if monthly_installment <= monthly_interest_only:
                raise InfeasiblePaymentError(
                    f"Monthly installment {monthly_installment} does not cover the monthly interest "
                    f"({monthly_interest_only.quantize(_CENT, rounding=ROUND_HALF_UP)}) on a balance of "
                    f"{remaining_balance} at {annual_interest_rate}% annual interest; the loan would "
                    "never amortize."
                )

        duration_months = amortization_math.solve_duration_months(
            remaining_balance, monthly_rate, monthly_installment
        )
        balance_before_final = amortization_math.balance_before_final_payment(
            remaining_balance, monthly_rate, monthly_installment, duration_months
        )
        final_payment = balance_before_final * (Decimal(1) + monthly_rate)
        total_payment = monthly_installment * (duration_months - 1) + final_payment
        total_interest = total_payment - remaining_balance

        return LoanCalculation(
            monthly_installment=monthly_installment,
            loan_duration_months=duration_months,
            loan_end_date=add_months(as_of_date, duration_months),
            total_interest=self._quantize(total_interest),
            total_payment=self._quantize(total_payment),
        )

    def calculate_installment_for_duration(
        self,
        remaining_balance: Decimal,
        annual_interest_rate: Decimal,
        target_duration_months: int,
    ) -> Decimal:
        self._validate_principal(remaining_balance)
        self._validate_interest_rate(annual_interest_rate)
        if target_duration_months <= 0:
            raise InvalidDurationError(f"Target duration must be > 0, got {target_duration_months}.")

        monthly_rate = amortization_math.monthly_rate_from_annual(annual_interest_rate)
        installment = amortization_math.solve_installment_for_duration(
            remaining_balance, monthly_rate, target_duration_months
        )
        # Round UP, never to nearest: the exact installment gives precisely
        # target_duration_months months. Since duration is monotonically
        # decreasing in installment size, rounding up (never down) is what
        # guarantees the cents-quantized installment never yields a longer
        # actual duration than requested.
        return installment.quantize(_CENT, rounding=ROUND_CEILING)

    def _validate_principal(self, remaining_balance: Decimal) -> None:
        if remaining_balance <= 0:
            raise InvalidPrincipalError(f"Remaining balance must be > 0, got {remaining_balance}.")

    def _validate_interest_rate(self, annual_interest_rate: Decimal) -> None:
        if annual_interest_rate < 0:
            raise InvalidInterestRateError(f"Annual interest rate must be >= 0, got {annual_interest_rate}.")

    def _quantize(self, value: Decimal) -> Decimal:
        return value.quantize(_CENT, rounding=ROUND_HALF_UP)
