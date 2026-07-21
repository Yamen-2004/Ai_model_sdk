"""Statement-recency check: payment date must not be older than `settings.max_statement_age_days`."""

from __future__ import annotations

from datetime import date

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.models.domain import CustomerProfile
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.models.validation import ReasonCode, ValidationIssue
from loan_restructuring_sdk.validation.base import ValidationRuleInterface


class PaymentDateRecencyRule(ValidationRuleInterface):
    """Fails with ReasonCode.STATEMENT_TOO_OLD if the payment date is older than
    `settings.max_statement_age_days`.
    """

    def __init__(self, reference_date: date | None = None) -> None:
        self._reference_date = reference_date

    def evaluate(
        self,
        statement: SalaryStatement,
        customer: CustomerProfile,
        settings: Settings,
    ) -> list[ValidationIssue]:

        print("\n" + "=" * 60)
        print("PaymentDateRecencyRule")
        print("=" * 60)

        if statement.payment_date is None:
            print("Payment Date: None")
            print("-> PaymentDateExistsRule should handle this case.")
            return []

        reference_date = self._reference_date or date.today()

        print(f"Reference Date : {reference_date}")
        print(f"Payment Date   : {statement.payment_date}")
        print(f"Max Age (days) : {settings.max_statement_age_days}")

        age_days = (reference_date - statement.payment_date).days

        print(f"Computed Age   : {age_days} days")

        if age_days <= settings.max_statement_age_days:
            print("Validation Result: PASS")
            print("=" * 60 + "\n")
            return []

        print("Validation Result: FAIL")
        print(
            f"Reason: Statement is {age_days} days old "
            f"(limit: {settings.max_statement_age_days})"
        )
        print("=" * 60 + "\n")

        return [
            ValidationIssue(
                rule_name="PaymentDateRecencyRule",
                reason_code=ReasonCode.STATEMENT_TOO_OLD,
                detail=(
                    f"Salary statement payment date "
                    f"{statement.payment_date.isoformat()} is "
                    f"{age_days} days old, exceeding the "
                    f"{settings.max_statement_age_days}-day limit."
                ),
            )
        ]