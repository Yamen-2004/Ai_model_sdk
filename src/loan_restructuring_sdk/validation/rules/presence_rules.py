"""Rules that check required fields were actually extracted (docs/SDD.md section 5.3, ReasonCode.*_MISSING)."""

from __future__ import annotations

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.models.domain import CustomerProfile
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.models.validation import ReasonCode, ValidationIssue
from loan_restructuring_sdk.validation.base import ValidationRuleInterface


class NameExistsRule(ValidationRuleInterface):
    """Fails with ReasonCode.NAME_MISSING if no employee name was extracted."""

    def evaluate(
        self,
        statement: SalaryStatement,
        customer: CustomerProfile,
        settings: Settings,
    ) -> list[ValidationIssue]:
        if statement.employee_name is not None:
            return []
        return [
            ValidationIssue(
                rule_name="NameExistsRule",
                reason_code=ReasonCode.NAME_MISSING,
                detail="Employee name could not be found on the salary statement.",
            )
        ]


class NetSalaryExistsRule(ValidationRuleInterface):
    """Fails with ReasonCode.NET_SALARY_MISSING if no net salary was extracted."""

    def evaluate(
        self,
        statement: SalaryStatement,
        customer: CustomerProfile,
        settings: Settings,
    ) -> list[ValidationIssue]:
        if statement.net_salary is not None:
            return []
        return [
            ValidationIssue(
                rule_name="NetSalaryExistsRule",
                reason_code=ReasonCode.NET_SALARY_MISSING,
                detail="Net salary could not be found on the salary statement.",
            )
        ]


class PaymentDateExistsRule(ValidationRuleInterface):
    """Fails with ReasonCode.PAYMENT_DATE_MISSING if no payment date was extracted."""

    def evaluate(
        self,
        statement: SalaryStatement,
        customer: CustomerProfile,
        settings: Settings,
    ) -> list[ValidationIssue]:
        if statement.payment_date is not None:
            return []
        return [
            ValidationIssue(
                rule_name="PaymentDateExistsRule",
                reason_code=ReasonCode.PAYMENT_DATE_MISSING,
                detail="Payment date could not be found on the salary statement.",
            )
        ]
