"""Stage 1 pipeline: PDF Extraction Engine -> Validation Engine -> Stage 1 Response Builder.

Independently composable and testable without Stage 2, without the `Case`
DTO, and without a mapper: takes only the domain-level inputs Stage 1
needs -- raw PDF bytes and a `CustomerProfile` -- so it can be exercised in
isolation (docs/SDD.md Goal G1). `LoanRestructuringSDK.process_case()` will
compose this pipeline with a Stage 2 pipeline once the Scenario and
Priority Engines exist; until then, this is a complete, usable unit on its
own.
"""

from __future__ import annotations

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.extraction.base import PDFExtractionEngineInterface
from loan_restructuring_sdk.models.domain import CustomerProfile
from loan_restructuring_sdk.models.response import Stage1Result
from loan_restructuring_sdk.response.stage1_base import Stage1ResponseBuilderInterface
from loan_restructuring_sdk.validation.base import ValidationEngineInterface


class Stage1Pipeline:
    """Runs Stage 1 end to end for a single case: extract, validate, build the Stage 1 result."""

    def __init__(
        self,
        extraction_engine: PDFExtractionEngineInterface,
        validation_engine: ValidationEngineInterface,
        response_builder: Stage1ResponseBuilderInterface,
        settings: Settings,
    ) -> None:
        self._extraction_engine = extraction_engine
        self._validation_engine = validation_engine
        self._response_builder = response_builder
        self._settings = settings

    async def run(self, pdf_bytes: bytes, customer: CustomerProfile) -> Stage1Result:
        """Extract the salary statement, validate it against `customer`, and return the Stage 1 result.

        Raises `OCRServiceError` / `ExtractionError` for structural
        extraction failures (bad PDF, OCR provider call failure) -- those are
        not business-rule rejections. A document the OCR provider can read
        but can't confidently extract fields from comes back with `None`
        fields and fails the relevant presence rules instead, per Stage 1
        scope.
        """
        statement = await self._extraction_engine.extract(pdf_bytes)
        validation = self._validation_engine.run(statement, customer, self._settings)
        return self._response_builder.build(statement, validation)
