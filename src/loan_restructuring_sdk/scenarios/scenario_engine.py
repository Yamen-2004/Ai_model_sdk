"""Default implementation of ScenarioEngineInterface."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.financial_calculator.base import FinancialCalculatorInterface
from loan_restructuring_sdk.models.domain import CustomerProfile, LoanProfile
from loan_restructuring_sdk.models.scenario import ScenarioCollection
from loan_restructuring_sdk.scenarios.base import ScenarioEngineInterface, ScenarioStrategyInterface


class ScenarioEngine(ScenarioEngineInterface):
    """Runs a fixed, ordered list of ScenarioStrategyInterface implementations.

    Contains no financial formulas itself -- every strategy delegates all
    amortization math to the injected `FinancialCalculatorInterface`.
    """

    def __init__(
        self,
        strategies: list[ScenarioStrategyInterface],
        calculator: FinancialCalculatorInterface,
    ) -> None:
        self._strategies = strategies
        self._calculator = calculator

    def generate(
        self,
        customer: CustomerProfile,
        loan: LoanProfile,
        verified_net_salary: Decimal,
        settings: Settings,
        as_of_date: date,
    ) -> ScenarioCollection:
        scenarios = [
            strategy.build(customer, loan, verified_net_salary, self._calculator, settings, as_of_date)
            for strategy in self._strategies
        ]
        return ScenarioCollection(scenarios=scenarios)
