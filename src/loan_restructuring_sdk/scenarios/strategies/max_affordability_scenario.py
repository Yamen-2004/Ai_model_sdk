"""Scenario 1 -- monthly installment fixed at `settings.max_installment_ratio` of verified net salary."""

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


class MaxAffordabilityScenario(ScenarioStrategyInterface):
    """Scenario 1: installment = `settings.max_installment_ratio` * verified net salary (docs/SDD.md 6.1/D17).

    Uses `verified_net_salary` (Stage 1's extracted, validated figure), not
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
        installment = (verified_net_salary * settings.max_installment_ratio).quantize(
            _CENT, rounding=ROUND_HALF_UP
        )

        try:
            calculation = calculator.calculate(
                loan.remaining_balance, loan.interest_rate_annual, installment, as_of_date
            )
        except InfeasiblePaymentError as exc:
            return Scenario(
                name=ScenarioName.SCENARIO_1_MAX_AFFORDABILITY,
                monthly_installment=installment,
                feasible=False,
                notes=str(exc),
            )

        return Scenario(
            name=ScenarioName.SCENARIO_1_MAX_AFFORDABILITY,
            monthly_installment=calculation.monthly_installment,
            loan_duration_months=calculation.loan_duration_months,
            loan_end_date=calculation.loan_end_date,
            total_interest=calculation.total_interest,
            total_payment=calculation.total_payment,
            feasible=True,
        )
