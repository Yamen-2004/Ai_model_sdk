"""Unit tests for `LoanRestructuringSDK.process_case`.

Every collaborator is a fake, so this test verifies pure orchestration --
which stages run, in what order, with what data -- not the business logic
inside any one engine (each engine has its own dedicated unit tests;
`tests/integration/test_end_to_end.py` covers the real, fully-wired stack).
"""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.extraction.base import PDFExtractionEngineInterface
from loan_restructuring_sdk.mapping.base import CaseMapperInterface
from loan_restructuring_sdk.models.case_dto import (
    Case,
    Customer,
    DocumentRef,
    DocumentType,
    Loan,
    RestructuringRequest,
    RestructuringType,
)
from loan_restructuring_sdk.models.domain import CaseIdentity, CustomerProfile, LoanProfile
from loan_restructuring_sdk.models.priority import PriorityContext, PriorityLevel, PriorityResult
from loan_restructuring_sdk.models.response import CaseStatus, SDKResponse, Stage1Result, Stage2Result
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.models.scenario import Scenario, ScenarioCollection, ScenarioName
from loan_restructuring_sdk.models.validation import ReasonCode, ValidationIssue, ValidationOutcome
from loan_restructuring_sdk.priority.base import PriorityEngineInterface
from loan_restructuring_sdk.response.base import ResponseBuilderInterface
from loan_restructuring_sdk.response.stage1_response_builder import Stage1ResponseBuilder
from loan_restructuring_sdk.scenarios.base import ScenarioEngineInterface
from loan_restructuring_sdk.sdk import LoanRestructuringSDK
from loan_restructuring_sdk.stage1_pipeline import Stage1Pipeline
from loan_restructuring_sdk.validation.base import ValidationEngineInterface

_SETTINGS = Settings()
_AS_OF = date(2026, 7, 21)
_REAL_PDF = Path(__file__).resolve().parents[2] / "Salary_Statement" / "mock_data_test_case_1_pass.pdf"

# Deliberately different from every test's SalaryStatement.net_salary, so a test would fail
# loudly if process_case() ever wired the wrong salary into the Scenario Engine (docs/SDD.md D17/D18).
_DECOY_REPORTED_SALARY = Decimal("999999.99")


def _case() -> Case:
    return Case(
        id=1,
        application_number="APP-2026-0001",
        status="UNDER_REVIEW",
        priority=None,
        created_at=datetime(2026, 7, 1, 9, 0, 0),
        updated_at=datetime(2026, 7, 1, 9, 0, 0),
        customer=Customer(
            id=1,
            name="Ahmed Ali",
            national_id="1",
            birth_date=date(1990, 1, 1),
            employer="Acme",
            monthly_salary=Decimal("5000"),
            net_salary=_DECOY_REPORTED_SALARY,
            email="a@a.com",
            phone="0",
        ),
        loan=Loan(
            id=1,
            account_number="A",
            loan_type="PERSONAL",
            original_amount=Decimal("10000"),
            remaining_balance=Decimal("8000"),
            current_installment=Decimal("400"),
            interest_rate=Decimal("5"),
            term_months=36,
            loan_start_date=date(2025, 1, 1),
            loan_maturity_date=date(2028, 1, 1),
            loan_status="ACTIVE",
        ),
        restructuring_request=RestructuringRequest(reason="فقدان الوظيفة", type=RestructuringType.DECREASE),
        documents=[DocumentRef(type=DocumentType.SALARY_STATEMENT, file=str(_REAL_PDF))],
    )


class _FakeCaseMapper(CaseMapperInterface):
    def to_case_identity(self, case: Case) -> CaseIdentity:
        return CaseIdentity(case_id=case.id, application_number=case.application_number)

    def to_customer_profile(self, case: Case) -> CustomerProfile:
        return CustomerProfile(name=case.customer.name, reported_net_salary=case.customer.net_salary)

    def to_loan_profile(self, case: Case) -> LoanProfile:
        return LoanProfile(
            remaining_balance=case.loan.remaining_balance,
            interest_rate_annual=case.loan.interest_rate,
            current_installment=case.loan.current_installment,
        )

    def to_document_path(self, case: Case) -> str:
        return case.documents[0].file

    def to_restructuring_reason(self, case: Case) -> str:
        return case.restructuring_request.reason


class _FakeExtractionEngine(PDFExtractionEngineInterface):
    def __init__(self, statement: SalaryStatement) -> None:
        self._statement = statement

    async def extract(self, pdf_bytes: bytes) -> SalaryStatement:
        return self._statement


class _FakeValidationEngine(ValidationEngineInterface):
    def __init__(self, outcome: ValidationOutcome) -> None:
        self._outcome = outcome

    def run(self, statement, customer, settings) -> ValidationOutcome:
        return self._outcome


class _SpyScenarioEngine(ScenarioEngineInterface):
    def __init__(self, collection: ScenarioCollection) -> None:
        self._collection = collection
        self.calls: list[tuple] = []

    def generate(self, customer, loan, verified_net_salary, settings, as_of_date) -> ScenarioCollection:
        self.calls.append((customer, loan, verified_net_salary, settings, as_of_date))
        return self._collection


class _SpyPriorityEngine(PriorityEngineInterface):
    def __init__(self, result: PriorityResult) -> None:
        self._result = result
        self.calls: list[PriorityContext] = []

    def evaluate(self, context: PriorityContext) -> PriorityResult:
        self.calls.append(context)
        return self._result


class _SpyResponseBuilder(ResponseBuilderInterface):
    def __init__(self) -> None:
        self.rejected_calls: list[tuple] = []
        self.processed_calls: list[tuple] = []

    def build_rejected(self, case_identity, statement, validation, generated_at) -> SDKResponse:
        self.rejected_calls.append((case_identity, statement, validation, generated_at))
        return SDKResponse(
            case_id=case_identity.case_id,
            application_number=case_identity.application_number,
            status=CaseStatus.REJECTED,
            stage1=Stage1Result(statement=statement, validation=validation),
            stage2=None,
            generated_at=generated_at,
        )

    def build_processed(self, case_identity, statement, validation, scenarios, priority, generated_at) -> SDKResponse:
        self.processed_calls.append((case_identity, statement, validation, scenarios, priority, generated_at))
        return SDKResponse(
            case_id=case_identity.case_id,
            application_number=case_identity.application_number,
            status=CaseStatus.PROCESSED,
            stage1=Stage1Result(statement=statement, validation=validation),
            stage2=Stage2Result(scenarios=scenarios, priority=priority),
            generated_at=generated_at,
        )


def _sdk(
    statement: SalaryStatement,
    validation_outcome: ValidationOutcome,
    scenario_engine: _SpyScenarioEngine,
    priority_engine: _SpyPriorityEngine,
    response_builder: _SpyResponseBuilder,
) -> LoanRestructuringSDK:
    stage1_pipeline = Stage1Pipeline(
        extraction_engine=_FakeExtractionEngine(statement),
        validation_engine=_FakeValidationEngine(validation_outcome),
        response_builder=Stage1ResponseBuilder(),
        settings=_SETTINGS,
    )
    return LoanRestructuringSDK(
        case_mapper=_FakeCaseMapper(),
        stage1_pipeline=stage1_pipeline,
        scenario_engine=scenario_engine,
        priority_engine=priority_engine,
        response_builder=response_builder,
        settings=_SETTINGS,
    )


async def test_process_case_stops_after_stage1_when_validation_fails() -> None:
    statement = SalaryStatement(employee_name="Someone Else", net_salary=None, payment_date=None)
    validation_outcome = ValidationOutcome(
        passed=False,
        issues=[
            ValidationIssue(rule_name="NetSalaryExistsRule", reason_code=ReasonCode.NET_SALARY_MISSING, detail="x")
        ],
    )
    scenario_engine = _SpyScenarioEngine(ScenarioCollection(scenarios=[_scenario()] * 3))
    priority_engine = _SpyPriorityEngine(PriorityResult(level=PriorityLevel.LOW, votes=[]))
    response_builder = _SpyResponseBuilder()
    sdk = _sdk(statement, validation_outcome, scenario_engine, priority_engine, response_builder)

    result = await sdk.process_case(_case(), as_of_date=_AS_OF)

    assert result.status == CaseStatus.REJECTED
    assert scenario_engine.calls == []
    assert priority_engine.calls == []
    assert response_builder.processed_calls == []
    assert len(response_builder.rejected_calls) == 1


async def test_process_case_runs_stage2_when_validation_passes() -> None:
    verified_salary = Decimal("5000.00")
    statement = SalaryStatement(employee_name="Ahmed Ali", net_salary=verified_salary, payment_date=_AS_OF)
    validation_outcome = ValidationOutcome(passed=True, issues=[])
    scenario_collection = ScenarioCollection(scenarios=[_scenario()] * 3)
    scenario_engine = _SpyScenarioEngine(scenario_collection)
    priority_result = PriorityResult(level=PriorityLevel.HIGH, votes=[])
    priority_engine = _SpyPriorityEngine(priority_result)
    response_builder = _SpyResponseBuilder()
    sdk = _sdk(statement, validation_outcome, scenario_engine, priority_engine, response_builder)

    result = await sdk.process_case(_case(), as_of_date=_AS_OF)

    assert result.status == CaseStatus.PROCESSED
    assert len(scenario_engine.calls) == 1
    _customer, _loan, called_salary, called_settings, called_as_of = scenario_engine.calls[0]
    assert called_salary == verified_salary  # the verified salary, never customer.reported_net_salary
    assert called_salary != _DECOY_REPORTED_SALARY
    assert called_settings is _SETTINGS
    assert called_as_of == _AS_OF

    assert len(priority_engine.calls) == 1
    assert priority_engine.calls[0].restructuring_reason == "فقدان الوظيفة"

    assert len(response_builder.processed_calls) == 1
    assert response_builder.rejected_calls == []
    assert result.stage2 is not None
    assert result.stage2.priority == priority_result


def _scenario() -> Scenario:
    return Scenario(
        name=ScenarioName.SCENARIO_1_MAX_AFFORDABILITY,
        monthly_installment=Decimal("100.00"),
        feasible=True,
    )
