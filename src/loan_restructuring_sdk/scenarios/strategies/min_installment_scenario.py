"""Scenario 2 -- the required monthly installment for a fixed `settings.max_loan_duration_months` term."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.financial_calculator.base import FinancialCalculatorInterface
from loan_restructuring_sdk.models.domain import CustomerProfile, LoanProfile
from loan_restructuring_sdk.models.scenario import Scenario, ScenarioName
from loan_restructuring_sdk.scenarios.base import ScenarioStrategyInterface
from loan_restructuring_sdk.utils.exceptions import InfeasiblePaymentError

_CENT = Decimal("0.01")


class MinInstallmentScenario(ScenarioStrategyInterface):
    """Scenario 2: installment = `calculate_installment_for_duration(remaining_balance, rate, settings.max_loan_duration_months)`.

    Never silently caps or modifies the installment if it exceeds the 55%
    affordability guideline -- the mathematically correct installment is
    always what's used to compute the scenario; a warning is attached to
    `notes` instead (docs/SDD.md Design Decision D15). The affordability
    comparison itself uses `verified_net_salary`, not
    `customer.reported_net_salary` (docs/SDD.md Design Decision D17).
    """

    def build(
        self,
        customer: CustomerProfile,
        loan: LoanProfile,
        verified_net_salary: Decimal,
        calculator: FinancialCalculatorInterface,
        settings: Settings,
        as_of_date: date,
    ) -> Scenario:
        installment = calculator.calculate_installment_for_duration(
            loan.remaining_balance, loan.interest_rate_annual, settings.max_loan_duration_months
        )

        max_affordable = (verified_net_salary * settings.max_installment_ratio).quantize(
            _CENT, rounding=ROUND_HALF_UP
        )
        notes = None
        if installment > max_affordable:
            notes = (
                f"Required installment {installment} to amortize within "
                f"{settings.max_loan_duration_months} months exceeds the recommended affordability "
                f"threshold of {max_affordable} ({settings.max_installment_ratio * 100} percent of net "
                "salary)."
            )

        try:
            calculation = calculator.calculate(
                loan.remaining_balance, loan.interest_rate_annual, installment, as_of_date
            )
        except InfeasiblePaymentError as exc:
            return Scenario(
                name=ScenarioName.SCENARIO_2_MIN_INSTALLMENT,
                monthly_installment=installment,
                feasible=False,
                notes=str(exc),
            )

        return Scenario(
            name=ScenarioName.SCENARIO_2_MIN_INSTALLMENT,
            monthly_installment=calculation.monthly_installment,
            loan_duration_months=calculation.loan_duration_months,
            loan_end_date=calculation.loan_end_date,
            total_interest=calculation.total_interest,
            total_payment=calculation.total_payment,
            feasible=True,
            notes=notes,
        )
