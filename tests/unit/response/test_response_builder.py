"""Unit tests for `ResponseBuilder`."""

from datetime import date, datetime, timezone
from decimal import Decimal

from loan_restructuring_sdk.models.domain import CaseIdentity
from loan_restructuring_sdk.models.priority import PriorityLevel, PriorityResult
from loan_restructuring_sdk.models.response import CaseStatus
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.models.scenario import Scenario, ScenarioName
from loan_restructuring_sdk.models.validation import ReasonCode, ValidationIssue, ValidationOutcome
from loan_restructuring_sdk.response.response_builder import ResponseBuilder

_IDENTITY = CaseIdentity(case_id=1, application_number="APP-2026-0001")
_GENERATED_AT = datetime(2026, 7, 21, 12, 0, 0, tzinfo=timezone.utc)


def test_build_rejected_sets_status_rejected_and_no_stage2() -> None:
    validation = ValidationOutcome(
        passed=False,
        issues=[
            ValidationIssue(rule_name="NameExistsRule", reason_code=ReasonCode.NAME_MISSING, detail="missing")
        ],
    )

    response = ResponseBuilder().build_rejected(_IDENTITY, None, validation, _GENERATED_AT)

    assert response.status == CaseStatus.REJECTED
    assert response.case_id == 1
    assert response.application_number == "APP-2026-0001"
    assert response.stage1.statement is None
    assert response.stage1.validation.passed is False
    assert response.stage1.validation.issues == validation.issues
    assert response.stage2 is None
    assert response.generated_at == _GENERATED_AT


def test_build_rejected_preserves_every_validation_reason() -> None:
    validation = ValidationOutcome(
        passed=False,
        issues=[
            ValidationIssue(rule_name="RuleA", reason_code=ReasonCode.NAME_MISSING, detail="a"),
            ValidationIssue(rule_name="RuleB", reason_code=ReasonCode.NET_SALARY_MISSING, detail="b"),
        ],
    )

    response = ResponseBuilder().build_rejected(_IDENTITY, None, validation, _GENERATED_AT)

    assert len(response.stage1.validation.issues) == 2


def test_build_processed_sets_status_processed_with_stage2() -> None:
    statement = SalaryStatement(
        employee_name="Ahmed Ali", net_salary=Decimal("5000.00"), payment_date=date(2026, 7, 1)
    )
    validation = ValidationOutcome(passed=True, issues=[])
    scenario = Scenario(
        name=ScenarioName.SCENARIO_1_MAX_AFFORDABILITY,
        monthly_installment=Decimal("2750.00"),
        loan_duration_months=4,
        loan_end_date=date(2026, 11, 1),
        total_interest=Decimal("50.00"),
        total_payment=Decimal("10050.00"),
        feasible=True,
    )
    priority = PriorityResult(level=PriorityLevel.HIGH, votes=[])

    response = ResponseBuilder().build_processed(
        _IDENTITY, statement, validation, [scenario, scenario, scenario], priority, _GENERATED_AT
    )

    assert response.status == CaseStatus.PROCESSED
    assert response.stage1.statement == statement
    assert response.stage2 is not None
    assert response.stage2.scenarios == [scenario, scenario, scenario]
    assert response.stage2.priority == priority
    assert response.generated_at == _GENERATED_AT
