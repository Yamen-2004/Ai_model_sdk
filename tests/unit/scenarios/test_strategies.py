"""Unit tests for the three ScenarioStrategyInterface implementations.

Mocks nothing -- uses the real `FinancialCalculator` throughout, and
cross-checks every strategy's output fields directly against independent
calls to the calculator, to verify the strategies truly delegate all
financial math rather than reimplementing it.

`_customer()` deliberately sets `reported_net_salary` to a decoy value
different from whatever `verified_net_salary` each test passes in --
docs/SDD.md Design Decision D17 requires the backend-reported figure to
never influence a scenario's math, and using two different values in every
test is what actually proves that, rather than merely asserting it.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.financial_calculator.calculator import FinancialCalculator
from loan_restructuring_sdk.models.domain import CustomerProfile, LoanProfile
from loan_restructuring_sdk.models.scenario import ScenarioName
from loan_restructuring_sdk.scenarios.strategies.balanced_scenario import BalancedScenario
from loan_restructuring_sdk.scenarios.strategies.max_affordability_scenario import MaxAffordabilityScenario
from loan_restructuring_sdk.scenarios.strategies.min_installment_scenario import MinInstallmentScenario

_CENT = Decimal("0.01")
_AS_OF = date(2026, 1, 1)
_SETTINGS = Settings()
_CALCULATOR = FinancialCalculator()

# A decoy backend-reported salary, deliberately different from every test's verified_net_salary
# below, so a test would fail loudly if a strategy ever accidentally read it.
_DECOY_REPORTED_SALARY = Decimal("999999.99")


def _customer() -> CustomerProfile:
    return CustomerProfile(name="Ahmed Ali", reported_net_salary=_DECOY_REPORTED_SALARY)


def _loan(remaining_balance: str, interest_rate_annual: str) -> LoanProfile:
    return LoanProfile(
        remaining_balance=Decimal(remaining_balance),
        interest_rate_annual=Decimal(interest_rate_annual),
        current_installment=Decimal("0"),
    )


# --- Scenario 1: MaxAffordabilityScenario ---


def test_max_affordability_installment_is_exactly_55_percent_of_verified_net_salary() -> None:
    verified_net_salary = Decimal("5000.00")
    loan = _loan("10000", "6")
    strategy = MaxAffordabilityScenario()

    scenario = strategy.build(_customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF)

    expected = (verified_net_salary * _SETTINGS.max_installment_ratio).quantize(_CENT, rounding=ROUND_HALF_UP)
    assert scenario.monthly_installment == expected
    assert scenario.name == ScenarioName.SCENARIO_1_MAX_AFFORDABILITY


def test_max_affordability_ignores_reported_net_salary() -> None:
    """The backend-reported salary must never influence the calculation (docs/SDD.md D17)."""
    verified_net_salary = Decimal("5000.00")
    loan = _loan("10000", "6")
    strategy = MaxAffordabilityScenario()

    scenario = strategy.build(_customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF)

    decoy_based = (_DECOY_REPORTED_SALARY * _SETTINGS.max_installment_ratio).quantize(
        _CENT, rounding=ROUND_HALF_UP
    )
    assert scenario.monthly_installment != decoy_based
    assert scenario.monthly_installment == Decimal("2750.00")  # 55% of the verified 5000, not the decoy


def test_max_affordability_delegates_full_calculation_to_financial_calculator() -> None:
    verified_net_salary = Decimal("5000.00")
    loan = _loan("10000", "6")
    strategy = MaxAffordabilityScenario()

    scenario = strategy.build(_customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF)
    expected = _CALCULATOR.calculate(
        loan.remaining_balance, loan.interest_rate_annual, scenario.monthly_installment, _AS_OF
    )

    assert scenario.loan_duration_months == expected.loan_duration_months
    assert scenario.loan_end_date == expected.loan_end_date
    assert scenario.total_interest == expected.total_interest
    assert scenario.total_payment == expected.total_payment
    assert scenario.feasible is True


def test_max_affordability_high_salary() -> None:
    verified_net_salary = Decimal("20000.00")
    loan = _loan("50000", "5")
    strategy = MaxAffordabilityScenario()

    scenario = strategy.build(_customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF)

    assert scenario.feasible is True
    assert scenario.monthly_installment == Decimal("11000.00")  # 55% of 20000


def test_max_affordability_low_salary_is_infeasible_when_installment_below_interest_only() -> None:
    # Verified net salary of 100 -> 55% = 55.00/month, which doesn't cover monthly interest
    # on a large balance at a high rate.
    verified_net_salary = Decimal("100.00")
    loan = _loan("100000", "24")
    strategy = MaxAffordabilityScenario()

    scenario = strategy.build(_customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF)

    assert scenario.feasible is False
    assert scenario.notes is not None
    assert scenario.loan_duration_months is None
    assert scenario.total_interest is None
    assert scenario.total_payment is None


def test_max_affordability_small_remaining_balance_pays_off_quickly() -> None:
    verified_net_salary = Decimal("5000.00")
    loan = _loan("500", "8")
    strategy = MaxAffordabilityScenario()

    scenario = strategy.build(_customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF)

    assert scenario.feasible is True
    assert scenario.loan_duration_months == 1  # 55% of 5000 = 2750, vastly more than the 500 balance


def test_max_affordability_zero_interest() -> None:
    verified_net_salary = Decimal("2000.00")
    loan = _loan("6600", "0")
    strategy = MaxAffordabilityScenario()

    scenario = strategy.build(_customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF)

    assert scenario.feasible is True
    assert scenario.total_interest == Decimal("0.00")


# --- Scenario 2: MinInstallmentScenario ---


def test_min_installment_targets_max_loan_duration_months() -> None:
    verified_net_salary = Decimal("5000.00")
    loan = _loan("10000", "6")
    strategy = MinInstallmentScenario()

    scenario = strategy.build(_customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF)

    assert scenario.feasible is True
    assert scenario.loan_duration_months <= _SETTINGS.max_loan_duration_months


def test_min_installment_uses_mathematically_correct_installment_unmodified() -> None:
    verified_net_salary = Decimal("5000.00")
    loan = _loan("10000", "6")
    strategy = MinInstallmentScenario()

    scenario = strategy.build(_customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF)
    expected_installment = _CALCULATOR.calculate_installment_for_duration(
        loan.remaining_balance, loan.interest_rate_annual, _SETTINGS.max_loan_duration_months
    )

    assert scenario.monthly_installment == expected_installment


def test_min_installment_warns_but_does_not_modify_installment_when_above_affordability_threshold() -> None:
    """Explicit required case: Scenario 2 requiring an installment above 55% of verified net salary."""
    verified_net_salary = Decimal("200.00")  # 55% = 110.00/month
    loan = _loan("50000", "10")  # requires a much higher installment to clear in 96 months
    strategy = MinInstallmentScenario()

    scenario = strategy.build(_customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF)
    expected_installment = _CALCULATOR.calculate_installment_for_duration(
        loan.remaining_balance, loan.interest_rate_annual, _SETTINGS.max_loan_duration_months
    )
    max_affordable = (verified_net_salary * _SETTINGS.max_installment_ratio).quantize(
        _CENT, rounding=ROUND_HALF_UP
    )

    assert expected_installment > max_affordable  # sanity check the test scenario is set up correctly
    assert scenario.feasible is True
    assert scenario.monthly_installment == expected_installment  # not clamped/modified
    assert scenario.notes is not None
    assert "exceeds the recommended affordability" in scenario.notes


def test_min_installment_ignores_reported_net_salary_for_the_warning_check() -> None:
    # 55% of the decoy reported salary (999999.99) would easily cover this installment,
    # so if the strategy mistakenly used it, no warning would fire. It must fire anyway,
    # because the verified salary of 200 is what should be used.
    verified_net_salary = Decimal("200.00")
    loan = _loan("50000", "10")
    strategy = MinInstallmentScenario()

    scenario = strategy.build(_customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF)

    assert scenario.notes is not None


def test_min_installment_no_warning_when_within_affordability_threshold() -> None:
    verified_net_salary = Decimal("20000.00")  # 55% = 11000.00/month, comfortably enough
    loan = _loan("10000", "6")
    strategy = MinInstallmentScenario()

    scenario = strategy.build(_customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF)

    assert scenario.notes is None


def test_min_installment_no_warning_at_exact_affordability_boundary() -> None:
    loan = _loan("10000", "6")
    required_installment = _CALCULATOR.calculate_installment_for_duration(
        loan.remaining_balance, loan.interest_rate_annual, _SETTINGS.max_loan_duration_months
    )
    # Construct a verified net salary whose 55% cap lands exactly on the required installment.
    verified_net_salary = required_installment / _SETTINGS.max_installment_ratio
    strategy = MinInstallmentScenario()

    scenario = strategy.build(_customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF)

    assert scenario.notes is None  # "exceeds" is a strict >, not >=


def test_min_installment_zero_interest() -> None:
    verified_net_salary = Decimal("5000.00")
    loan = _loan("9600", "0")
    strategy = MinInstallmentScenario()

    scenario = strategy.build(_customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF)

    assert scenario.feasible is True
    assert scenario.total_interest == Decimal("0.00")
    assert scenario.loan_duration_months <= _SETTINGS.max_loan_duration_months


# --- Scenario 3: BalancedScenario ---


def test_balanced_installment_is_average_of_scenario_1_and_2() -> None:
    verified_net_salary = Decimal("5000.00")
    loan = _loan("10000", "6")

    scenario_1 = MaxAffordabilityScenario().build(
        _customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF
    )
    scenario_2 = MinInstallmentScenario().build(
        _customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF
    )
    scenario_3 = BalancedScenario().build(
        _customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF
    )

    expected = ((scenario_1.monthly_installment + scenario_2.monthly_installment) / Decimal(2)).quantize(
        _CENT, rounding=ROUND_HALF_UP
    )
    assert scenario_3.monthly_installment == expected
    assert scenario_3.name == ScenarioName.SCENARIO_3_BALANCED


def test_balanced_delegates_full_calculation_to_financial_calculator() -> None:
    verified_net_salary = Decimal("5000.00")
    loan = _loan("10000", "6")
    strategy = BalancedScenario()

    scenario = strategy.build(_customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF)
    expected = _CALCULATOR.calculate(
        loan.remaining_balance, loan.interest_rate_annual, scenario.monthly_installment, _AS_OF
    )

    assert scenario.loan_duration_months == expected.loan_duration_months
    assert scenario.total_interest == expected.total_interest
    assert scenario.total_payment == expected.total_payment


def test_balanced_zero_interest() -> None:
    verified_net_salary = Decimal("2000.00")
    loan = _loan("6600", "0")
    strategy = BalancedScenario()

    scenario = strategy.build(_customer(), loan, verified_net_salary, _CALCULATOR, _SETTINGS, _AS_OF)

    assert scenario.feasible is True
    assert scenario.total_interest == Decimal("0.00")
