"""Default implementation of PriorityEngineInterface.

v1 aggregation policy: take the highest `PriorityLevel` among all rules that
fired (explicit requirement -- "if multiple keywords detected, always
return the highest priority"). The aggregation step itself is intentionally
isolated in this class so a future weighted-scoring aggregator can replace
it without changing `PriorityRuleInterface` (docs/SDD.md Design Decision D7).
"""

from __future__ import annotations

from loan_restructuring_sdk.models.priority import PriorityContext, PriorityLevel, PriorityResult
from loan_restructuring_sdk.priority.base import PriorityEngineInterface, PriorityRuleInterface

# Highest-wins order, per the explicit requirement: "if multiple keywords detected,
# always return the highest priority." Also doubles as the "no rule fired" fallback,
# since LOW is last: "if no keyword matches, return LOW."
_LEVEL_PRIORITY_ORDER = (PriorityLevel.HIGH, PriorityLevel.MEDIUM, PriorityLevel.LOW)


class PriorityEngine(PriorityEngineInterface):
    """Runs a configured list of PriorityRuleInterface implementations and aggregates their votes."""

    def __init__(self, rules: list[PriorityRuleInterface]) -> None:
        self._rules = rules

    def evaluate(self, context: PriorityContext) -> PriorityResult:
        votes = [rule.evaluate(context) for rule in self._rules]
        fired_levels = {vote.level for vote in votes if vote.level is not None}

        level = PriorityLevel.LOW
        for candidate in _LEVEL_PRIORITY_ORDER:
            if candidate in fired_levels:
                level = candidate
                break

        return PriorityResult(level=level, votes=votes)
