"""Unit tests for `ScenarioEngine`. Mocks nothing -- uses the real `FinancialCalculator`."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.financial_calculator.calculator import FinancialCalculator
from loan_restructuring_sdk.models.domain import CustomerProfile, LoanProfile
from loan_restructuring_sdk.models.scenario import Scenario, ScenarioCollection, ScenarioName
from loan_restructuring_sdk.scenarios.scenario_engine import ScenarioEngine
from loan_restructuring_sdk.scenarios.strategies.balanced_scenario import BalancedScenario
from loan_restructuring_sdk.scenarios.strategies.max_affordability_scenario import MaxAffordabilityScenario
from loan_restructuring_sdk.scenarios.strategies.min_installment_scenario import MinInstallmentScenario

_AS_OF = date(2026, 1, 1)
_SETTINGS = Settings()

# Deliberately different from every test's verified_net_salary, to prove the engine/strategies
# never fall back to it (docs/SDD.md Design Decision D17).
_DECOY_REPORTED_SALARY = Decimal("999999.99")


def _engine() -> ScenarioEngine:
    calculator = FinancialCalculator()
    return ScenarioEngine(
        strategies=[MaxAffordabilityScenario(), MinInstallmentScenario(), BalancedScenario()],
        calculator=calculator,
    )


def _customer() -> CustomerProfile:
    return CustomerProfile(name="Ahmed Ali", reported_net_salary=_DECOY_REPORTED_SALARY)


def _loan(remaining_balance: str, interest_rate_annual: str) -> LoanProfile:
    return LoanProfile(
        remaining_balance=Decimal(remaining_balance),
        interest_rate_annual=Decimal(interest_rate_annual),
        current_installment=Decimal("0"),
    )


def test_generate_always_returns_exactly_three_scenarios() -> None:
    result = _engine().generate(_customer(), _loan("10000", "6"), Decimal("5000.00"), _SETTINGS, _AS_OF)

    assert isinstance(result, ScenarioCollection)
    assert len(result.scenarios) == 3


def test_generate_returns_scenarios_in_the_configured_order() -> None:
    result = _engine().generate(_customer(), _loan("10000", "6"), Decimal("5000.00"), _SETTINGS, _AS_OF)

    assert [s.name for s in result.scenarios] == [
        ScenarioName.SCENARIO_1_MAX_AFFORDABILITY,
        ScenarioName.SCENARIO_2_MIN_INSTALLMENT,
        ScenarioName.SCENARIO_3_BALANCED,
    ]


def test_generate_uses_verified_salary_not_reported_salary() -> None:
    result = _engine().generate(_customer(), _loan("10000", "6"), Decimal("5000.00"), _SETTINGS, _AS_OF)

    scenario_1 = result.scenarios[0]
    assert scenario_1.monthly_installment == Decimal("2750.00")  # 55% of verified 5000, not the decoy


def test_generate_high_salary() -> None:
    result = _engine().generate(_customer(), _loan("30000", "5"), Decimal("25000.00"), _SETTINGS, _AS_OF)

    assert all(s.feasible for s in result.scenarios)


def test_generate_low_salary() -> None:
    result = _engine().generate(_customer(), _loan("8000", "10"), Decimal("300.00"), _SETTINGS, _AS_OF)

    assert len(result.scenarios) == 3  # still exactly 3, even if some are infeasible or warn


def test_generate_small_remaining_balance() -> None:
    result = _engine().generate(_customer(), _loan("250", "7"), Decimal("4000.00"), _SETTINGS, _AS_OF)
    scenario_1, scenario_2, scenario_3 = result.scenarios

    assert len(result.scenarios) == 3
    assert all(s.feasible for s in result.scenarios)
    # Scenario 1 (55% of a comfortable salary) and Scenario 3 (its average with Scenario 2)
    # both use installments vastly larger than the tiny balance, so both pay off almost
    # immediately. Scenario 2 deliberately targets the full 96-month duration regardless of
    # how small the balance is -- it is not expected to be short.
    assert scenario_1.loan_duration_months <= 3
    assert scenario_3.loan_duration_months <= 3
    assert scenario_2.loan_duration_months <= _SETTINGS.max_loan_duration_months


def test_generate_zero_interest() -> None:
    result = _engine().generate(_customer(), _loan("6600", "0"), Decimal("2000.00"), _SETTINGS, _AS_OF)

    assert len(result.scenarios) == 3
    assert all(s.total_interest == Decimal("0.00") for s in result.scenarios)


def test_scenario_collection_rejects_fewer_than_three_scenarios() -> None:
    scenario = Scenario(
        name=ScenarioName.SCENARIO_1_MAX_AFFORDABILITY,
        monthly_installment=Decimal("100"),
        feasible=True,
    )
    with pytest.raises(ValidationError):
        ScenarioCollection(scenarios=[scenario, scenario])


def test_scenario_collection_rejects_more_than_three_scenarios() -> None:
    scenario = Scenario(
        name=ScenarioName.SCENARIO_1_MAX_AFFORDABILITY,
        monthly_installment=Decimal("100"),
        feasible=True,
    )
    with pytest.raises(ValidationError):
        ScenarioCollection(scenarios=[scenario, scenario, scenario, scenario])
