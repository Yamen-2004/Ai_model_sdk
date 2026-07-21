"""Date/time helpers -- calendar-month arithmetic used by the Financial Calculator's `loan_end_date`."""

from __future__ import annotations

import calendar
from datetime import date


def add_months(base: date, months: int) -> date:
    """Return `base` advanced by `months` calendar months, clamping the day-of-month if needed.

    E.g. `add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)` -- January
    31st plus one month clamps to February's last day rather than
    overflowing into March.
    """
    if months < 0:
        raise ValueError(f"months must be >= 0, got {months}")
    total_month_index = base.month - 1 + months
    year = base.year + total_month_index // 12
    month = total_month_index % 12 + 1
    day = min(base.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)
