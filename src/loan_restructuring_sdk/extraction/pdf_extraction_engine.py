"""Default implementation of PDFExtractionEngineInterface."""

from __future__ import annotations

from loan_restructuring_sdk.extraction.base import PDFExtractionEngineInterface
from loan_restructuring_sdk.extraction.prompts import SALARY_STATEMENT_EXTRACTION_PROMPT
from loan_restructuring_sdk.extraction.salary_statement_builder import SalaryStatementBuilder
from loan_restructuring_sdk.models.salary_statement import SalaryStatement
from loan_restructuring_sdk.ocr.base import OCRServiceInterface


class PDFExtractionEngine(PDFExtractionEngineInterface):
    """Coordinates the OCR Service call and building a SalaryStatement from its result."""

    def __init__(
        self,
        ocr_service: OCRServiceInterface,
        statement_builder: SalaryStatementBuilder | None = None,
    ) -> None:
        self._ocr_service = ocr_service
        self._statement_builder = statement_builder or SalaryStatementBuilder()

    async def extract(self, pdf_bytes: bytes) -> SalaryStatement:
        raw_extraction = await self._ocr_service.extract(pdf_bytes, SALARY_STATEMENT_EXTRACTION_PROMPT)
        return self._statement_builder.build(raw_extraction)
