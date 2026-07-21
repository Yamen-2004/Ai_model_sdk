"""Interfaces for the Loan Scenario Engine (docs/SDD.md section 6).

`FinancialCalculatorInterface` lives in `financial_calculator.base` (its
own, fully independent package -- docs/SDD.md D13/D14) and is only
imported here for typing `ScenarioStrategyInterface.build()`. This
package must depend only on the Financial Calculator, `CustomerProfile`,
and `LoanProfile` -- never on API DTOs, the Validation Engine, the
Priority Engine, or the Response Builder.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.financial_calculator.base import FinancialCalculatorInterface
from loan_restructuring_sdk.models.domain import CustomerProfile, LoanProfile
from loan_restructuring_sdk.models.scenario import Scenario, ScenarioCollection


class ScenarioStrategyInterface(ABC):
    """A single restructuring scenario: decides which installment to use, then delegates the math."""

    @abstractmethod
    def build(
        self,
        customer: CustomerProfile,
        loan: LoanProfile,
        verified_net_salary: Decimal,
        calculator: FinancialCalculatorInterface,
        settings: Settings,
        as_of_date: date,
    ) -> Scenario:
        """Compute this scenario's Scenario.

        `verified_net_salary` -- not `customer.reported_net_salary` -- is
        the source of truth for every salary-driven calculation (Scenario
        1's affordability cap, Scenario 2's affordability warning). It is
        the net salary Stage 1 extracted from the salary statement and
        validated, passed in explicitly by the caller once Stage 1 has
        succeeded; `customer.reported_net_salary` (the backend's own
        figure) is reference metadata only and must never be read here
        (docs/SDD.md Design Decision D17).

        `as_of_date` has no default, for the same reason
        `FinancialCalculatorInterface.calculate()`'s doesn't: a hidden
        `date.today()` would make the result depend on wall-clock time.
        """
        raise NotImplementedError


class ScenarioEngineInterface(ABC):
    """Runs all configured scenario strategies in a fixed order (docs/SDD.md NG2 -- always exactly 3)."""

    @abstractmethod
    def generate(
        self,
        customer: CustomerProfile,
        loan: LoanProfile,
        verified_net_salary: Decimal,
        settings: Settings,
        as_of_date: date,
    ) -> ScenarioCollection:
        """Return the full ScenarioCollection, one Scenario per configured strategy.

        `verified_net_salary` must be Stage 1's verified salary, not
        `customer.reported_net_salary` -- see `ScenarioStrategyInterface.build()`.
        """
        raise NotImplementedError
