"""Interface for the PDF Extraction Engine -- Stage 1's document-handling layer."""

from __future__ import annotations

from abc import ABC, abstractmethod

from loan_restructuring_sdk.models.salary_statement import SalaryStatement


class PDFExtractionEngineInterface(ABC):
    """Orchestrates PDF bytes -> OCR Service -> a validated SalaryStatement.

    No local PDF-to-image rendering step: the PDF is sent to the OCR
    Service as-is (docs/SDD.md Design Decision D5).
    """

    @abstractmethod
    async def extract(self, pdf_bytes: bytes) -> SalaryStatement:
        """Extract a SalaryStatement from raw PDF bytes."""
        raise NotImplementedError
