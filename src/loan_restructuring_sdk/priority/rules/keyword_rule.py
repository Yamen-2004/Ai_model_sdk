"""MVP priority rule: Arabic keyword matching against the restructuring reason (docs/SDD.md D7/D8)."""

from __future__ import annotations

from loan_restructuring_sdk.models.priority import PriorityContext, PriorityLevel, PriorityVote
from loan_restructuring_sdk.priority.base import PriorityRuleInterface
from loan_restructuring_sdk.priority.keyword_loader import KeywordLoader

_RULE_NAME = "KeywordPriorityRule"
_LEVEL_PRIORITY_ORDER = (PriorityLevel.HIGH, PriorityLevel.MEDIUM, PriorityLevel.LOW)


class KeywordPriorityRule(PriorityRuleInterface):
    """Matches Arabic keywords (via `KeywordLoader`) against the restructuring reason text.

    Plain substring matching only -- no AI, no embeddings, no fuzzy matching
    (explicit MVP scope). Keywords are loaded once, at construction time, so
    a bad configuration file fails fast during startup/DI wiring rather than
    on the first request. When keywords from more than one level appear in
    the same reason, this rule reports only the highest one it found
    (HIGH -> MEDIUM -> LOW); `PriorityEngine` additionally applies this same
    highest-wins policy across *all* rules, not just this one.
    """

    def __init__(self, loader: KeywordLoader | None = None) -> None:
        self._keywords_by_level = (loader or KeywordLoader()).load()

    def evaluate(self, context: PriorityContext) -> PriorityVote:
        reason = context.restructuring_reason
        for level in _LEVEL_PRIORITY_ORDER:
            matched = [kw for kw in self._keywords_by_level[level.value] if kw and kw in reason]
            if matched:
                return PriorityVote(
                    rule_name=_RULE_NAME,
                    level=level,
                    matched=matched,
                    detail=f"Matched {level.value} keyword(s): {', '.join(matched)}",
                )

        return PriorityVote(
            rule_name=_RULE_NAME,
            level=None,
            matched=[],
            detail="No configured keyword matched the restructuring reason",
        )
