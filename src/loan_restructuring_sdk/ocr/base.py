"""Interface for the OCR Service -- the boundary that talks to Mistral OCR (or any future provider)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class OCRServiceInterface(ABC):
    """Extracts structured data directly from a document, using a multimodal model.

    Takes raw document bytes, not pre-rendered images or extracted text --
    no local PDF-to-image conversion, OCR library, or text extraction runs
    before the document reaches the model (docs/SDD.md Design Decision D5).
    """

    @abstractmethod
    async def extract(self, document_bytes: bytes, prompt: str) -> dict[str, Any]:
        """Send the raw document bytes + a prompt to the OCR provider and return its raw structured JSON output."""
        raise NotImplementedError
