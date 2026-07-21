"""Unit tests for `PriorityEngine` -- aggregation behavior (docs/SDD.md Design Decision D7).

Uses fake `PriorityRuleInterface` implementations (never the real keyword
rule) so the aggregation policy is tested in isolation from keyword matching.
"""

from datetime import date
from decimal import Decimal

from loan_restructuring_sdk.models.domain import CustomerProfile, LoanProfile
from loan_restructuring_sdk.models.priority import PriorityContext, PriorityLevel, PriorityVote
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.priority.base import PriorityRuleInterface
from loan_restructuring_sdk.priority.priority_engine import PriorityEngine

_CONTEXT = PriorityContext(
    restructuring_reason="any reason",
    loan=LoanProfile(
        remaining_balance=Decimal("10000"), interest_rate_annual=Decimal("6"), current_installment=Decimal("0")
    ),
    customer=CustomerProfile(name="Ahmed Ali", reported_net_salary=Decimal("4000")),
    statement=SalaryStatement(employee_name="Ahmed Ali", net_salary=Decimal("4000"), payment_date=date(2026, 7, 1)),
)


class _FixedVoteRule(PriorityRuleInterface):
    def __init__(self, rule_name: str, level: PriorityLevel | None) -> None:
        self._rule_name = rule_name
        self._level = level

    def evaluate(self, context: PriorityContext) -> PriorityVote:
        return PriorityVote(rule_name=self._rule_name, level=self._level, matched=[], detail="fixed vote")


def test_evaluate_returns_highest_level_among_rules_that_fired() -> None:
    engine = PriorityEngine(
        rules=[
            _FixedVoteRule("RuleA", PriorityLevel.LOW),
            _FixedVoteRule("RuleB", PriorityLevel.HIGH),
            _FixedVoteRule("RuleC", PriorityLevel.MEDIUM),
        ]
    )

    result = engine.evaluate(_CONTEXT)

    assert result.level == PriorityLevel.HIGH


def test_evaluate_defaults_to_low_when_no_rule_fires() -> None:
    engine = PriorityEngine(
        rules=[
            _FixedVoteRule("RuleA", None),
            _FixedVoteRule("RuleB", None),
        ]
    )

    result = engine.evaluate(_CONTEXT)

    assert result.level == PriorityLevel.LOW


def test_evaluate_defaults_to_low_when_there_are_no_rules_at_all() -> None:
    engine = PriorityEngine(rules=[])

    result = engine.evaluate(_CONTEXT)

    assert result.level == PriorityLevel.LOW
    assert result.votes == []


def test_evaluate_retains_every_rule_vote_for_auditability() -> None:
    engine = PriorityEngine(
        rules=[
            _FixedVoteRule("RuleA", None),
            _FixedVoteRule("RuleB", PriorityLevel.MEDIUM),
        ]
    )

    result = engine.evaluate(_CONTEXT)

    assert [vote.rule_name for vote in result.votes] == ["RuleA", "RuleB"]
    assert result.votes[0].level is None
    assert result.votes[1].level == PriorityLevel.MEDIUM


def test_evaluate_ignores_non_firing_votes_when_picking_the_winner() -> None:
    engine = PriorityEngine(
        rules=[
            _FixedVoteRule("RuleA", None),
            _FixedVoteRule("RuleB", PriorityLevel.LOW),
        ]
    )

    result = engine.evaluate(_CONTEXT)

    assert result.level == PriorityLevel.LOW
