"""Interfaces for the Priority Engine (docs/SDD.md Design Decisions D7-D9)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from loan_restructuring_sdk.models.priority import PriorityContext, PriorityResult, PriorityVote


class PriorityRuleInterface(ABC):
    """A single priority-scoring signal. Must always return a vote, even a non-firing one (`level=None`)."""

    @abstractmethod
    def evaluate(self, context: PriorityContext) -> PriorityVote:
        """Score the given context and return this rule's vote."""
        raise NotImplementedError


class PriorityEngineInterface(ABC):
    """Runs every configured rule and aggregates votes into a single PriorityResult."""

    @abstractmethod
    def evaluate(self, context: PriorityContext) -> PriorityResult:
        """Run all rules and aggregate their votes (v1 aggregation: highest level among rules that fired)."""
        raise NotImplementedError
