"""Unit tests for `PDFExtractionEngine`. The OCR Service is mocked -- no real Mistral calls."""

from unittest.mock import AsyncMock

from loan_restructuring_sdk.extraction.pdf_extraction_engine import PDFExtractionEngine
from loan_restructuring_sdk.extraction.prompts import SALARY_STATEMENT_EXTRACTION_PROMPT
from loan_restructuring_sdk.ocr.base import OCRServiceInterface


async def test_extract_passes_pdf_bytes_and_prompt_to_ocr_service() -> None:
    ocr_service = AsyncMock(spec=OCRServiceInterface)
    ocr_service.extract.return_value = {
        "employee_name": "Ahmed Ali",
        "net_salary": 4500,
        "payment_date": "2026-07-01",
    }
    engine = PDFExtractionEngine(ocr_service=ocr_service)

    await engine.extract(b"pdf-bytes")

    ocr_service.extract.assert_awaited_once_with(b"pdf-bytes", SALARY_STATEMENT_EXTRACTION_PROMPT)


async def test_extract_builds_salary_statement_from_ocr_output() -> None:
    ocr_service = AsyncMock(spec=OCRServiceInterface)
    ocr_service.extract.return_value = {
        "employee_name": "Ahmed Ali",
        "net_salary": 4500,
        "payment_date": "2026-07-01",
    }
    engine = PDFExtractionEngine(ocr_service=ocr_service)

    statement = await engine.extract(b"pdf-bytes")

    assert statement.employee_name == "Ahmed Ali"
    assert statement.net_salary == 4500
    assert statement.payment_date.isoformat() == "2026-07-01"


async def test_extract_passes_through_null_fields_from_ocr_service() -> None:
    ocr_service = AsyncMock(spec=OCRServiceInterface)
    ocr_service.extract.return_value = {"employee_name": None, "net_salary": None, "payment_date": None}
    engine = PDFExtractionEngine(ocr_service=ocr_service)

    statement = await engine.extract(b"pdf-bytes")

    assert statement.employee_name is None
    assert statement.net_salary is None
    assert statement.payment_date is None
