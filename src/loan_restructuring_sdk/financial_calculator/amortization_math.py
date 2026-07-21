"""Pure amortization math: closed-form only, no approximation, no iterative/brute-force search.

No exceptions, no model construction, no I/O. Callers (`calculator.py`)
validate inputs before calling these functions, which assume `principal >
0`, `installment > 0`, `monthly_rate >= 0`, and -- when `monthly_rate > 0`
-- `installment > principal * monthly_rate` already hold.

All computation happens in `Decimal` (never `float`), so results are exact
to the configured precision and reproducible -- the same inputs always
produce the same outputs.
"""

from __future__ import annotations

import math
from decimal import Decimal, localcontext

# Elevated precision for the intermediate ln()/power operations below, scoped to a
# local context so it never affects the caller's global decimal precision/rounding.
_CALCULATION_PRECISION = 50


def monthly_rate_from_annual(annual_rate_percent: Decimal) -> Decimal:
    """Convert an annual percentage rate (e.g. `Decimal("4.5")` for 4.5%) to a monthly decimal rate."""
    return annual_rate_percent / Decimal(100) / Decimal(12)


def solve_duration_months(principal: Decimal, monthly_rate: Decimal, installment: Decimal) -> int:
    """Return the smallest whole number of months that fully amortizes `principal`.

    Closed-form: for r > 0, n = -ln(1 - r*P/A) / ln(1+r); for r == 0,
    n = P/A. The exact (possibly fractional) result is rounded up to the
    next whole month -- the final month's payment is then smaller than
    `installment` unless the exact value happens to land on an integer.
    """
    if monthly_rate == 0:
        exact_months = principal / installment
    else:
        with localcontext() as ctx:
            ctx.prec = _CALCULATION_PRECISION
            exact_months = -(Decimal(1) - monthly_rate * principal / installment).ln() / (
                Decimal(1) + monthly_rate
            ).ln()
    return math.ceil(exact_months)


def balance_before_final_payment(
    principal: Decimal,
    monthly_rate: Decimal,
    installment: Decimal,
    duration_months: int,
) -> Decimal:
    """Return the outstanding balance immediately before the final (`duration_months`-th) payment.

    Closed-form balance after `k` fixed payments:
    `B_k = P*(1+r)^k - A*((1+r)^k - 1)/r` for r > 0, or `P - A*k` for r == 0.
    """
    months_of_full_payments = duration_months - 1
    if monthly_rate == 0:
        return principal - installment * months_of_full_payments
    with localcontext() as ctx:
        ctx.prec = _CALCULATION_PRECISION
        growth = (Decimal(1) + monthly_rate) ** months_of_full_payments
        return principal * growth - installment * (growth - Decimal(1)) / monthly_rate


def solve_installment_for_duration(
    principal: Decimal,
    monthly_rate: Decimal,
    duration_months: int,
) -> Decimal:
    """Return the fixed monthly installment that fully amortizes `principal` over exactly `duration_months`.

    Closed-form (the standard annuity-payment formula, algebraic inverse of
    `solve_duration_months`): for r > 0, `A = P*r*(1+r)^n / ((1+r)^n - 1)`;
    for r == 0, `A = P/n`. Exact -- no search, no approximation.
    """
    if monthly_rate == 0:
        return principal / Decimal(duration_months)
    with localcontext() as ctx:
        ctx.prec = _CALCULATION_PRECISION
        growth = (Decimal(1) + monthly_rate) ** duration_months
        return principal * monthly_rate * growth / (growth - Decimal(1))
