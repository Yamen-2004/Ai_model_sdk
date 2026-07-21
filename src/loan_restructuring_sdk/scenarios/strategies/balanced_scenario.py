"""Scenario 3 -- the average monthly installment between Scenario 1 and Scenario 2."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.financial_calculator.base import FinancialCalculatorInterface
from loan_restructuring_sdk.models.domain import CustomerProfile, LoanProfile
from loan_restructuring_sdk.models.scenario import Scenario, ScenarioName
from loan_restructuring_sdk.scenarios.base import ScenarioStrategyInterface
from loan_restructuring_sdk.scenarios.strategies.max_affordability_scenario import MaxAffordabilityScenario
from loan_restructuring_sdk.scenarios.strategies.min_installment_scenario import MinInstallmentScenario
from loan_restructuring_sdk.utils.exceptions import InfeasiblePaymentError

_CENT = Decimal("0.01")


class BalancedScenario(ScenarioStrategyInterface):
    """Scenario 3: installment = average(Scenario 1 installment, Scenario 2 installment).

    Recomputes Scenario 1 and Scenario 2 via their own strategies rather
    than accepting pre-computed values, so this strategy stays
    self-contained and independently testable/constructible -- the
    recomputation is cheap, closed-form arithmetic, not a performance
    concern.
    """

    def __init__(
        self,
        max_affordability: MaxAffordabilityScenario | None = None,
        min_installment: MinInstallmentScenario | None = None,
    ) -> None:
        self._max_affordability = max_affordability or MaxAffordabilityScenario()
        self._min_installment = min_installment or MinInstallmentScenario()

    def build(
        self,
        customer: CustomerProfile,
        loan: LoanProfile,
        verified_net_salary: Decimal,
        calculator: FinancialCalculatorInterface,
        settings: Settings,
        as_of_date: date,
    ) -> Scenario:
        scenario_1 = self._max_affordability.build(
            customer, loan, verified_net_salary, calculator, settings, as_of_date
        )
        scenario_2 = self._min_installment.build(
            customer, loan, verified_net_salary, calculator, settings, as_of_date
        )

        installment = (
            (scenario_1.monthly_installment + scenario_2.monthly_installment) / Decimal(2)
        ).quantize(_CENT, rounding=ROUND_HALF_UP)

        try:
            calculation = calculator.calculate(
                loan.remaining_balance, loan.interest_rate_annual, installment, as_of_date
            )
        except InfeasiblePaymentError as exc:
            return Scenario(
                name=ScenarioName.SCENARIO_3_BALANCED,
                monthly_installment=installment,
                feasible=False,
                notes=str(exc),
            )

        return Scenario(
            name=ScenarioName.SCENARIO_3_BALANCED,
            monthly_installment=calculation.monthly_installment,
            loan_duration_months=calculation.loan_duration_months,
            loan_end_date=calculation.loan_end_date,
            total_interest=calculation.total_interest,
            total_payment=calculation.total_payment,
            feasible=True,
        )
