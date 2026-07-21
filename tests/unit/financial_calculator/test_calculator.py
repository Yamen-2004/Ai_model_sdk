"""Comprehensive unit tests for `FinancialCalculator`. Mocks nothing -- fully deterministic pure math.

`_reference_amortize` is an intentionally naive month-by-month simulation,
written independently of `amortization_math`'s closed-form implementation,
used here purely as a cross-check oracle. It is test-only: the production
code never iterates/searches for its answer (per the explicit
no-brute-force requirement) -- this loop exists only to verify the
closed-form result is correct, not to compute it for the SDK.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

import pytest

from loan_restructuring_sdk.financial_calculator.calculator import FinancialCalculator
from loan_restructuring_sdk.utils.exceptions import (
    InfeasiblePaymentError,
    InvalidDurationError,
    InvalidInstallmentError,
    InvalidInterestRateError,
    InvalidPrincipalError,
)

_CENT = Decimal("0.01")
_AS_OF = date(2026, 1, 1)


def _reference_amortize(principal: Decimal, monthly_rate: Decimal, installment: Decimal) -> tuple[int, Decimal, Decimal]:
    """Naive, independent month-by-month simulation -- an oracle for tests only, not production logic."""
    balance = principal
    months = 0
    total_paid = Decimal("0")
    while True:
        months += 1
        if months > 100_000:
            raise AssertionError("reference amortization did not terminate -- test inputs are unrealistic")
        interest = balance * monthly_rate
        owed = balance + interest
        payment = owed if owed <= installment else installment
        total_paid += payment
        balance = owed - payment
        if balance <= 0:
            break
    total_interest = total_paid - principal
    return months, total_interest.quantize(_CENT, rounding=ROUND_HALF_UP), total_paid.quantize(_CENT, rounding=ROUND_HALF_UP)


@pytest.mark.parametrize(
    ("balance", "rate", "installment"),
    [
        (Decimal("5000"), Decimal("12"), Decimal("450")),
        (Decimal("15000"), Decimal("7.5"), Decimal("500")),
        (Decimal("2000"), Decimal("18"), Decimal("150")),
        (Decimal("8200"), Decimal("4.75"), Decimal("410")),
    ],
)
def test_normal_loan_matches_independent_reference_simulation(
    balance: Decimal, rate: Decimal, installment: Decimal
) -> None:
    calculator = FinancialCalculator()
    monthly_rate = rate / Decimal(100) / Decimal(12)

    result = calculator.calculate(balance, rate, installment, _AS_OF)
    expected_months, expected_interest, expected_payment = _reference_amortize(balance, monthly_rate, installment)

    assert result.loan_duration_months == expected_months
    assert result.total_interest == expected_interest
    assert result.total_payment == expected_payment
    assert result.monthly_installment == installment


def test_zero_interest_exact_division() -> None:
    calculator = FinancialCalculator()

    result = calculator.calculate(Decimal("1200"), Decimal("0"), Decimal("100"), _AS_OF)

    assert result.loan_duration_months == 12
    assert result.total_interest == Decimal("0.00")
    assert result.total_payment == Decimal("1200.00")
    assert result.loan_end_date == date(2027, 1, 1)


def test_zero_interest_non_exact_division_has_smaller_final_payment() -> None:
    calculator = FinancialCalculator()

    result = calculator.calculate(Decimal("1000"), Decimal("0"), Decimal("300"), _AS_OF)

    assert result.loan_duration_months == 4  # 3 full payments of 300 + a smaller final payment of 100
    assert result.total_interest == Decimal("0.00")
    assert result.total_payment == Decimal("1000.00")


def test_high_installment_pays_off_in_a_single_month() -> None:
    calculator = FinancialCalculator()

    result = calculator.calculate(Decimal("1000"), Decimal("12"), Decimal("2000"), _AS_OF)

    assert result.loan_duration_months == 1
    assert result.total_payment == Decimal("1010.00")  # 1000 + one month's interest at 1%
    assert result.total_interest == Decimal("10.00")
    assert result.loan_end_date == date(2026, 2, 1)


def test_very_low_installment_just_above_interest_only_yields_long_duration() -> None:
    # P=10000, 12%/yr => monthly rate 1%, interest-only payment = 100. Installment of 105
    # barely covers interest, so the loan should take a very long time to amortize.
    calculator = FinancialCalculator()

    result = calculator.calculate(Decimal("10000"), Decimal("12"), Decimal("105"), _AS_OF)

    assert result.loan_duration_months > 100
    assert result.total_interest > 0


def test_deterministic_same_inputs_produce_identical_results() -> None:
    calculator = FinancialCalculator()

    first = calculator.calculate(Decimal("5000"), Decimal("6"), Decimal("450"), _AS_OF)
    second = calculator.calculate(Decimal("5000"), Decimal("6"), Decimal("450"), _AS_OF)

    assert first == second


def test_loan_end_date_clamps_day_of_month() -> None:
    calculator = FinancialCalculator()

    result = calculator.calculate(Decimal("1000"), Decimal("12"), Decimal("2000"), date(2026, 1, 31))

    assert result.loan_end_date == date(2026, 2, 28)  # 1-month loan starting Jan 31 -> Feb 28 (not a leap year)


# --- Invalid inputs ---


def test_invalid_balance_zero_raises() -> None:
    calculator = FinancialCalculator()
    with pytest.raises(InvalidPrincipalError):
        calculator.calculate(Decimal("0"), Decimal("5"), Decimal("100"), _AS_OF)


def test_invalid_balance_negative_raises() -> None:
    calculator = FinancialCalculator()
    with pytest.raises(InvalidPrincipalError):
        calculator.calculate(Decimal("-500"), Decimal("5"), Decimal("100"), _AS_OF)


def test_invalid_installment_zero_raises() -> None:
    calculator = FinancialCalculator()
    with pytest.raises(InvalidInstallmentError):
        calculator.calculate(Decimal("1000"), Decimal("5"), Decimal("0"), _AS_OF)


def test_invalid_installment_negative_raises() -> None:
    calculator = FinancialCalculator()
    with pytest.raises(InvalidInstallmentError):
        calculator.calculate(Decimal("1000"), Decimal("5"), Decimal("-50"), _AS_OF)


def test_invalid_interest_rate_negative_raises() -> None:
    calculator = FinancialCalculator()
    with pytest.raises(InvalidInterestRateError):
        calculator.calculate(Decimal("1000"), Decimal("-1"), Decimal("100"), _AS_OF)


def test_zero_interest_rate_is_valid_not_an_error() -> None:
    calculator = FinancialCalculator()
    # Should not raise.
    calculator.calculate(Decimal("1000"), Decimal("0"), Decimal("100"), _AS_OF)


# --- Boundary cases ---


def test_installment_exactly_equal_to_interest_only_is_infeasible() -> None:
    # P=10000, 12%/yr => monthly interest-only payment is exactly 100.00.
    calculator = FinancialCalculator()
    with pytest.raises(InfeasiblePaymentError):
        calculator.calculate(Decimal("10000"), Decimal("12"), Decimal("100"), _AS_OF)


def test_installment_below_interest_only_is_infeasible() -> None:
    calculator = FinancialCalculator()
    with pytest.raises(InfeasiblePaymentError):
        calculator.calculate(Decimal("10000"), Decimal("12"), Decimal("50"), _AS_OF)


def test_installment_one_cent_above_interest_only_is_feasible() -> None:
    calculator = FinancialCalculator()
    # Should not raise, even though the resulting duration is extremely long.
    result = calculator.calculate(Decimal("10000"), Decimal("12"), Decimal("100.01"), _AS_OF)
    assert result.loan_duration_months > 0


# --- calculate_installment_for_duration ---


def test_calculate_installment_for_duration_zero_interest() -> None:
    calculator = FinancialCalculator()

    installment = calculator.calculate_installment_for_duration(Decimal("1200"), Decimal("0"), 12)

    assert installment == Decimal("100.00")


def test_calculate_installment_for_duration_matches_standard_annuity_formula() -> None:
    calculator = FinancialCalculator()
    principal, rate, n = Decimal("10000"), Decimal("12"), 96

    installment = calculator.calculate_installment_for_duration(principal, rate, n)

    monthly_rate = rate / Decimal(100) / Decimal(12)
    growth = (Decimal(1) + monthly_rate) ** n
    expected = (principal * monthly_rate * growth / (growth - Decimal(1))).quantize(
        _CENT, rounding=ROUND_HALF_UP
    )
    # Allow for the deliberate round-UP (ROUND_CEILING) vs this test's ROUND_HALF_UP reference --
    # they can only differ by at most one cent.
    assert abs(installment - expected) <= _CENT


def test_calculate_installment_for_duration_feeds_back_into_calculate_at_or_under_target() -> None:
    """The installment returned must never let the actual (cents-quantized) duration exceed the target."""
    calculator = FinancialCalculator()
    principal, rate, target = Decimal("10000"), Decimal("12"), 96

    installment = calculator.calculate_installment_for_duration(principal, rate, target)
    result = calculator.calculate(principal, rate, installment, _AS_OF)

    assert result.loan_duration_months <= target


@pytest.mark.parametrize(
    ("balance", "rate", "months"),
    [
        (Decimal("10000"), Decimal("12"), 96),
        (Decimal("5000"), Decimal("6"), 24),
        (Decimal("50000"), Decimal("4.5"), 60),
        (Decimal("1500"), Decimal("18"), 12),
    ],
)
def test_calculate_installment_for_duration_round_trips_through_solve_duration(
    balance: Decimal, rate: Decimal, months: int
) -> None:
    calculator = FinancialCalculator()

    installment = calculator.calculate_installment_for_duration(balance, rate, months)
    result = calculator.calculate(balance, rate, installment, _AS_OF)

    assert result.loan_duration_months <= months


def test_calculate_installment_for_duration_zero_interest_is_valid() -> None:
    calculator = FinancialCalculator()
    # Should not raise.
    calculator.calculate_installment_for_duration(Decimal("1000"), Decimal("0"), 10)


def test_calculate_installment_for_duration_invalid_balance_raises() -> None:
    calculator = FinancialCalculator()
    with pytest.raises(InvalidPrincipalError):
        calculator.calculate_installment_for_duration(Decimal("0"), Decimal("5"), 12)


def test_calculate_installment_for_duration_invalid_interest_rate_raises() -> None:
    calculator = FinancialCalculator()
    with pytest.raises(InvalidInterestRateError):
        calculator.calculate_installment_for_duration(Decimal("1000"), Decimal("-1"), 12)


def test_calculate_installment_for_duration_zero_duration_raises() -> None:
    calculator = FinancialCalculator()
    with pytest.raises(InvalidDurationError):
        calculator.calculate_installment_for_duration(Decimal("1000"), Decimal("5"), 0)


def test_calculate_installment_for_duration_negative_duration_raises() -> None:
    calculator = FinancialCalculator()
    with pytest.raises(InvalidDurationError):
        calculator.calculate_installment_for_duration(Decimal("1000"), Decimal("5"), -12)


def test_calculate_installment_for_duration_single_month() -> None:
    # Over exactly 1 month, the required installment is simply principal + one month's interest.
    calculator = FinancialCalculator()

    installment = calculator.calculate_installment_for_duration(Decimal("1000"), Decimal("12"), 1)

    assert installment == Decimal("1010.00")  # 1000 * 1.01
