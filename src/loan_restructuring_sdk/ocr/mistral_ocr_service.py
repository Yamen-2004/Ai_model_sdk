"""Mistral OCR implementation of the OCR Service.

Sends the salary-statement PDF to Mistral's `/v1/ocr` endpoint as a base64
data URL -- no local text extraction, OCR library, or page-image rendering
(docs/SDD.md Design Decision D5). Uses `document_annotation_format` to force
strictly-typed JSON output for exactly the three fields Stage 1 needs, so
"Mistral cannot confidently extract a field" maps directly to a JSON `null`
rather than a guess -- Mistral makes no business decisions, only extracts.
"""

from __future__ import annotations

import base64
import json
from typing import Any

import httpx

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.ocr.base import OCRServiceInterface
from loan_restructuring_sdk.utils.exceptions import OCRServiceError
from loan_restructuring_sdk.utils.logger import get_logger

logger = get_logger(__name__)

_REQUEST_TIMEOUT_SECONDS = 60.0

# Standard JSON Schema (Mistral's `document_annotation_format`, unlike Gemini's
# OpenAPI-subset Schema, takes a regular JSON Schema) -- forces the model to
# return exactly these three fields, each independently nullable.
_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "employee_name": {"type": ["string", "null"]},
        "net_salary": {"type": ["number", "null"]},
        "payment_date": {"type": ["string", "null"]},
    },
    "required": ["employee_name", "net_salary", "payment_date"],
    "additionalProperties": False,
}


class MistralOCRService(OCRServiceInterface):
    """Calls the Mistral OCR API to extract structured fields from a salary-statement PDF."""

    def __init__(self, settings: Settings, http_client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._http_client = http_client

    async def extract(self, document_bytes: bytes, prompt: str) -> dict[str, Any]:
        url = f"{self._settings.mistral_api_base_url}/v1/ocr"
        document_data_url = f"data:application/pdf;base64,{base64.b64encode(document_bytes).decode('ascii')}"
        payload = {
            "model": self._settings.mistral_model,
            "document": {
                "type": "document_url",
                "document_url": document_data_url,
            },
            "document_annotation_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "salary_statement",
                    "schema": _RESPONSE_SCHEMA,
                    "strict": True,
                },
            },
            "document_annotation_prompt": prompt,
        }

        try:
            response = await self._http_client.post(
                url,
                headers={"Authorization": f"Bearer {self._settings.mistral_api_key}"},
                json=payload,
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OCRServiceError(f"Mistral request failed: {exc}") from exc

        body = response.json()
        try:
            text = body["document_annotation"]
        except KeyError as exc:
            raise OCRServiceError(f"Unexpected Mistral response shape: {body!r}") from exc
        if text is None:
            raise OCRServiceError(f"Unexpected Mistral response shape: {body!r}")

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise OCRServiceError(f"Mistral did not return valid JSON: {text!r}") from exc
