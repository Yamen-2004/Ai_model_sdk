"""Interfaces for Stage 1's Validation Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.models.domain import CustomerProfile
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.models.validation import ValidationIssue, ValidationOutcome


class ValidationRuleInterface(ABC):
    """A single validation rule. Must never raise for missing/invalid data -- return issues instead."""

    @abstractmethod
    def evaluate(
        self,
        statement: SalaryStatement,
        customer: CustomerProfile,
        settings: Settings,
    ) -> list[ValidationIssue]:
        """Return zero or more ValidationIssues. An empty list means this rule passed."""
        raise NotImplementedError


class ValidationEngineInterface(ABC):
    """Runs every configured rule and aggregates all issues (docs/SDD.md Design Decision D2 -- no fail-fast)."""

    @abstractmethod
    def run(
        self,
        statement: SalaryStatement,
        customer: CustomerProfile,
        settings: Settings,
    ) -> ValidationOutcome:
        """Run all configured rules against the statement and return the aggregated outcome."""
        raise NotImplementedError
