"""Default implementation of Stage1ResponseBuilderInterface."""

from __future__ import annotations

from loan_restructuring_sdk.models.response import Stage1Result
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.models.validation import ValidationOutcome
from loan_restructuring_sdk.response.stage1_base import Stage1ResponseBuilderInterface


class Stage1ResponseBuilder(Stage1ResponseBuilderInterface):
    """Assembles the Stage 1 result: extracted data only on acceptance, always the full validation outcome."""

    def build(
        self,
        statement: SalaryStatement,
        validation: ValidationOutcome,
    ) -> Stage1Result:
        return Stage1Result(
            statement=statement if validation.passed else None,
            validation=validation,
        )
