"""Unit tests for `KeywordPriorityRule`.

Each test writes its own small `priority_keywords.json` and constructs the
rule around it, rather than depending on the shipped config's exact content
-- this also directly proves the keyword configuration can be replaced
without touching `KeywordPriorityRule` or `PriorityEngine` at all.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

from loan_restructuring_sdk.models.domain import CustomerProfile, LoanProfile
from loan_restructuring_sdk.models.priority import PriorityContext, PriorityLevel
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.priority.keyword_loader import KeywordLoader
from loan_restructuring_sdk.priority.rules.keyword_rule import KeywordPriorityRule

_KEYWORDS_JSON = """
{
  "HIGH": ["فقدان الوظيفة", "مرض"],
  "MEDIUM": ["تخفيض الراتب", "مولود"],
  "LOW": ["شراء سيارة", "استثمار"]
}
"""

_LOAN = LoanProfile(
    remaining_balance=Decimal("10000"), interest_rate_annual=Decimal("6"), current_installment=Decimal("0")
)
_CUSTOMER = CustomerProfile(name="Ahmed Ali", reported_net_salary=Decimal("4000"))
_STATEMENT = SalaryStatement(employee_name="Ahmed Ali", net_salary=Decimal("4000"), payment_date=date(2026, 7, 1))


def _rule(tmp_path: Path) -> KeywordPriorityRule:
    path = tmp_path / "priority_keywords.json"
    path.write_text(_KEYWORDS_JSON, encoding="utf-8")
    return KeywordPriorityRule(loader=KeywordLoader(path))


def _context(reason: str) -> PriorityContext:
    return PriorityContext(restructuring_reason=reason, loan=_LOAN, customer=_CUSTOMER, statement=_STATEMENT)


def test_evaluate_returns_high_when_a_high_keyword_matches(tmp_path: Path) -> None:
    vote = _rule(tmp_path).evaluate(_context("تم فقدان الوظيفة الشهر الماضي"))

    assert vote.level == PriorityLevel.HIGH
    assert vote.matched == ["فقدان الوظيفة"]


def test_evaluate_returns_medium_when_a_medium_keyword_matches(tmp_path: Path) -> None:
    vote = _rule(tmp_path).evaluate(_context("بسبب تخفيض الراتب"))

    assert vote.level == PriorityLevel.MEDIUM
    assert vote.matched == ["تخفيض الراتب"]


def test_evaluate_returns_low_when_a_low_keyword_matches(tmp_path: Path) -> None:
    vote = _rule(tmp_path).evaluate(_context("بغرض استثمار"))

    assert vote.level == PriorityLevel.LOW
    assert vote.matched == ["استثمار"]


def test_evaluate_returns_highest_matched_level_when_multiple_keywords_match(tmp_path: Path) -> None:
    vote = _rule(tmp_path).evaluate(_context("مرض مزمن أدى إلى تخفيض الراتب ثم استثمار"))

    assert vote.level == PriorityLevel.HIGH
    assert vote.matched == ["مرض"]


def test_evaluate_returns_none_level_when_no_keyword_matches(tmp_path: Path) -> None:
    vote = _rule(tmp_path).evaluate(_context("سبب غير مذكور في القوائم"))

    assert vote.level is None
    assert vote.matched == []


def test_evaluate_returns_none_level_for_an_empty_reason(tmp_path: Path) -> None:
    vote = _rule(tmp_path).evaluate(_context(""))

    assert vote.level is None
    assert vote.matched == []


def test_evaluate_always_returns_a_vote_even_when_nothing_fires(tmp_path: Path) -> None:
    vote = _rule(tmp_path).evaluate(_context(""))

    assert vote.rule_name == "KeywordPriorityRule"
    assert vote.detail
