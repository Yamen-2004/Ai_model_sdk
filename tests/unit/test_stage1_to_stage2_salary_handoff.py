"""Proves the Stage 1 -> Stage 2 salary handoff end to end (docs/SDD.md Design Decision D17).

There is no `Stage2Pipeline` yet (Priority Engine isn't built), so this
test wires `Stage1Pipeline` and `ScenarioEngine` together manually the way
a future `Stage2Pipeline`/`sdk.py` would: run Stage 1, and once it
succeeds, feed `Stage1Result.statement.net_salary` -- not
`CustomerProfile.reported_net_salary` -- into the Scenario Engine.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.extraction.base import PDFExtractionEngineInterface
from loan_restructuring_sdk.financial_calculator.calculator import FinancialCalculator
from loan_restructuring_sdk.models.domain import CustomerProfile, LoanProfile
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.response.stage1_response_builder import Stage1ResponseBuilder
from loan_restructuring_sdk.scenarios.scenario_engine import ScenarioEngine
from loan_restructuring_sdk.scenarios.strategies.balanced_scenario import BalancedScenario
from loan_restructuring_sdk.scenarios.strategies.max_affordability_scenario import MaxAffordabilityScenario
from loan_restructuring_sdk.scenarios.strategies.min_installment_scenario import MinInstallmentScenario
from loan_restructuring_sdk.stage1_pipeline import Stage1Pipeline
from loan_restructuring_sdk.validation.rules.identity_rule import NameExactMatchRule
from loan_restructuring_sdk.validation.rules.presence_rules import (
    NameExistsRule,
    NetSalaryExistsRule,
    PaymentDateExistsRule,
)
from loan_restructuring_sdk.validation.rules.recency_rule import PaymentDateRecencyRule
from loan_restructuring_sdk.validation.validation_engine import ValidationEngine

_TODAY = date(2026, 7, 21)
_SETTINGS = Settings()

# The backend reported one salary when the case was created; the salary statement Mistral
# extracted (and Stage 1 validated) shows a different, higher figure -- the realistic scenario
# this whole refactor exists for (a raise, a bonus, an out-of-date HR record, etc.).
_REPORTED_SALARY = Decimal("4000.00")
_VERIFIED_SALARY = Decimal("5000.00")


class _FakeExtractionEngine(PDFExtractionEngineInterface):
    def __init__(self, statement: SalaryStatement) -> None:
        self._statement = statement

    async def extract(self, pdf_bytes: bytes) -> SalaryStatement:
        return self._statement


def _stage1_pipeline(statement: SalaryStatement) -> Stage1Pipeline:
    validation_engine = ValidationEngine(
        rules=[
            NameExistsRule(),
            NetSalaryExistsRule(),
            PaymentDateExistsRule(),
            NameExactMatchRule(),
            PaymentDateRecencyRule(reference_date=_TODAY),
        ]
    )
    return Stage1Pipeline(
        extraction_engine=_FakeExtractionEngine(statement),
        validation_engine=validation_engine,
        response_builder=Stage1ResponseBuilder(),
        settings=_SETTINGS,
    )


async def test_scenario_engine_uses_stage1_verified_salary_not_backend_reported_salary() -> None:
    customer = CustomerProfile(name="Ahmed Ali", reported_net_salary=_REPORTED_SALARY)
    loan = LoanProfile(
        remaining_balance=Decimal("10000"),
        interest_rate_annual=Decimal("6"),
        current_installment=Decimal("0"),
    )
    statement = SalaryStatement(
        employee_name="Ahmed Ali", net_salary=_VERIFIED_SALARY, payment_date=_TODAY
    )

    stage1_result = await _stage1_pipeline(statement).run(pdf_bytes=b"pdf", customer=customer)
    assert stage1_result.validation.passed is True
    assert stage1_result.statement is not None

    scenario_engine = ScenarioEngine(
        strategies=[MaxAffordabilityScenario(), MinInstallmentScenario(), BalancedScenario()],
        calculator=FinancialCalculator(),
    )
    collection = scenario_engine.generate(
        customer, loan, stage1_result.statement.net_salary, _SETTINGS, _TODAY
    )

    scenario_1 = collection.scenarios[0]
    assert scenario_1.monthly_installment == (_VERIFIED_SALARY * _SETTINGS.max_installment_ratio).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    assert customer.reported_net_salary == _REPORTED_SALARY  # untouched, still available as metadata
    assert scenario_1.monthly_installment != (
        _REPORTED_SALARY * _SETTINGS.max_installment_ratio
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
