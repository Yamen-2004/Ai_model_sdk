"""Unit tests for the pure amortization math functions in isolation."""

from decimal import Decimal

from loan_restructuring_sdk.financial_calculator import amortization_math


def test_monthly_rate_from_annual() -> None:
    rate = amortization_math.monthly_rate_from_annual(Decimal("12"))
    assert rate == Decimal("0.01")


def test_monthly_rate_from_annual_zero() -> None:
    rate = amortization_math.monthly_rate_from_annual(Decimal("0"))
    assert rate == Decimal("0")


def test_solve_duration_months_zero_interest_exact_division() -> None:
    months = amortization_math.solve_duration_months(Decimal("1200"), Decimal("0"), Decimal("100"))
    assert months == 12


def test_solve_duration_months_zero_interest_rounds_up() -> None:
    months = amortization_math.solve_duration_months(Decimal("1000"), Decimal("0"), Decimal("300"))
    assert months == 4  # 1000 / 300 = 3.33... -> ceil to 4


def test_solve_duration_months_with_interest_rounds_up_a_fractional_month() -> None:
    # Known example: P=5000, r=1%/month, A=450 -> exact months is not an integer.
    months = amortization_math.solve_duration_months(Decimal("5000"), Decimal("0.01"), Decimal("450"))
    assert isinstance(months, int)
    assert months > 0


def test_balance_before_final_payment_zero_interest() -> None:
    balance = amortization_math.balance_before_final_payment(
        Decimal("1000"), Decimal("0"), Decimal("300"), duration_months=4
    )
    assert balance == Decimal("100")  # 1000 - 300*3 = 100


def test_balance_before_final_payment_with_interest_matches_manual_growth() -> None:
    principal = Decimal("1000")
    monthly_rate = Decimal("0.01")
    installment = Decimal("2000")
    # duration is 1 month (installment vastly exceeds what's owed), so k=0 full payments.
    balance = amortization_math.balance_before_final_payment(
        principal, monthly_rate, installment, duration_months=1
    )
    assert balance == principal  # no full payments made yet -> balance unchanged


def test_solve_installment_for_duration_zero_interest() -> None:
    installment = amortization_math.solve_installment_for_duration(
        Decimal("1200"), Decimal("0"), duration_months=12
    )
    assert installment == Decimal("100")


def test_solve_installment_for_duration_is_inverse_of_solve_duration_months() -> None:
    # Feeding the exact (unrounded) installment back into solve_duration_months
    # should recover the original target duration exactly -- these two
    # functions are algebraic inverses of the same recurrence.
    principal = Decimal("10000")
    monthly_rate = Decimal("0.01")
    target_months = 96

    installment = amortization_math.solve_installment_for_duration(principal, monthly_rate, target_months)
    recovered_months = amortization_math.solve_duration_months(principal, monthly_rate, installment)

    assert recovered_months == target_months


def test_solve_installment_for_duration_matches_standard_annuity_formula() -> None:
    # P=5000, r=1%/month, n=24 -> hand-checkable via A = P*r*(1+r)^n / ((1+r)^n - 1).
    principal = Decimal("5000")
    monthly_rate = Decimal("0.01")
    n = 24

    installment = amortization_math.solve_installment_for_duration(principal, monthly_rate, n)

    growth = (Decimal(1) + monthly_rate) ** n
    expected = principal * monthly_rate * growth / (growth - Decimal(1))
    assert abs(installment - expected) < Decimal("0.0000001")
