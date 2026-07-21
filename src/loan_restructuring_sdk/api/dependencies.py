"""FastAPI dependency providers -- wires concrete implementations into the SDK facade.

This is the SDK's Dependency Injection composition root: every engine/rule
concrete class is instantiated exactly once, here, and handed to
`LoanRestructuringSDK`'s constructor. Nothing else in the codebase
hardcodes which concrete rule/strategy classes are in play, so swapping,
adding, or removing one is a one-line change in `get_sdk()`.
"""

from __future__ import annotations

from functools import lru_cache

import httpx
from fastapi import Depends

from loan_restructuring_sdk.config.settings import Settings, get_settings
from loan_restructuring_sdk.extraction.pdf_extraction_engine import PDFExtractionEngine
from loan_restructuring_sdk.financial_calculator.calculator import FinancialCalculator
from loan_restructuring_sdk.mapping.case_mapper import CaseMapper
from loan_restructuring_sdk.ocr.mistral_ocr_service import MistralOCRService
from loan_restructuring_sdk.priority.priority_engine import PriorityEngine
from loan_restructuring_sdk.priority.rules.keyword_rule import KeywordPriorityRule
from loan_restructuring_sdk.response.response_builder import ResponseBuilder
from loan_restructuring_sdk.response.stage1_response_builder import Stage1ResponseBuilder
from loan_restructuring_sdk.scenarios.scenario_engine import ScenarioEngine
from loan_restructuring_sdk.scenarios.strategies.balanced_scenario import BalancedScenario
from loan_restructuring_sdk.scenarios.strategies.max_affordability_scenario import MaxAffordabilityScenario
from loan_restructuring_sdk.scenarios.strategies.min_installment_scenario import MinInstallmentScenario
from loan_restructuring_sdk.sdk import LoanRestructuringSDK
from loan_restructuring_sdk.stage1_pipeline import Stage1Pipeline
from loan_restructuring_sdk.validation.rules.identity_rule import NameExactMatchRule
from loan_restructuring_sdk.validation.rules.presence_rules import (
    NameExistsRule,
    NetSalaryExistsRule,
    PaymentDateExistsRule,
)
from loan_restructuring_sdk.validation.rules.recency_rule import PaymentDateRecencyRule
from loan_restructuring_sdk.validation.validation_engine import ValidationEngine


@lru_cache
def get_http_client() -> httpx.AsyncClient:
    """Shared async HTTP client for outbound calls (e.g. to the Mistral OCR API)."""
    return httpx.AsyncClient()


def get_sdk(
    settings: Settings = Depends(get_settings),
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> LoanRestructuringSDK:
    """Build a fully-wired LoanRestructuringSDK instance for a single request.

    Pure object-graph construction -- no business logic lives here, every
    engine/rule it wires together is independently implemented and tested
    elsewhere; this function only decides *how the pieces are assembled*.
    """
    ocr_service = MistralOCRService(settings=settings, http_client=http_client)
    extraction_engine = PDFExtractionEngine(ocr_service=ocr_service)

    validation_engine = ValidationEngine(
        rules=[
            NameExistsRule(),
            NetSalaryExistsRule(),
            PaymentDateExistsRule(),
            NameExactMatchRule(),
            PaymentDateRecencyRule(),
        ]
    )

    stage1_pipeline = Stage1Pipeline(
        extraction_engine=extraction_engine,
        validation_engine=validation_engine,
        response_builder=Stage1ResponseBuilder(),
        settings=settings,
    )

    calculator = FinancialCalculator()
    scenario_engine = ScenarioEngine(
        strategies=[
            MaxAffordabilityScenario(),
            MinInstallmentScenario(),
            BalancedScenario(),
        ],
        calculator=calculator,
    )

    priority_engine = PriorityEngine(rules=[KeywordPriorityRule()])

    return LoanRestructuringSDK(
        case_mapper=CaseMapper(),
        stage1_pipeline=stage1_pipeline,
        scenario_engine=scenario_engine,
        priority_engine=priority_engine,
        response_builder=ResponseBuilder(),
        settings=settings,
    )
