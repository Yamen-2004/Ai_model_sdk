"""Interface for the Stage 1 Response Builder.

Deliberately separate from `ResponseBuilderInterface` (the final,
post-Stage-2 `SDKResponse` builder): that interface's `build_processed`
requires `Scenario`s and a `PriorityResult`; the Priority Engine isn't
implemented yet (the Scenario Engine now is). This interface produces the
Stage-1-only shape the SDK can return today: extracted data + validation
result when accepted, or just the validation result with every rejection
reason when rejected -- no scenarios.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from loan_restructuring_sdk.models.response import Stage1Result
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.models.validation import ValidationOutcome


class Stage1ResponseBuilderInterface(ABC):
    """Builds the Stage-1-only response returned by `Stage1Pipeline.run()`."""

    @abstractmethod
    def build(
        self,
        statement: SalaryStatement,
        validation: ValidationOutcome,
    ) -> Stage1Result:
        """Build the Stage 1 result.

        When `validation.passed` is True: the returned `Stage1Result.statement`
        is the extracted data. When False: `statement` is `None` -- a
        rejected case returns the validation outcome (and all its
        `ValidationIssue`s) but not the extracted data.
        """
        raise NotImplementedError
