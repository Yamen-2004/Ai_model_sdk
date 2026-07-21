"""Unit tests for `MistralOCRService`. All Mistral calls are mocked -- no real network access."""

import json
from unittest.mock import AsyncMock

import httpx
import pytest

from loan_restructuring_sdk.config.settings import Settings
from loan_restructuring_sdk.ocr.mistral_ocr_service import MistralOCRService
from loan_restructuring_sdk.utils.exceptions import OCRServiceError


def _settings() -> Settings:
    return Settings(mistral_api_key="test-key", mistral_model="mistral-ocr-latest")


def _mistral_response(payload: dict) -> httpx.Response:
    """Build a fake Mistral `/v1/ocr` response wrapping `payload` as `document_annotation`."""
    return httpx.Response(
        status_code=200,
        json={
            "pages": [],
            "model": "mistral-ocr-latest",
            "document_annotation": json.dumps(payload),
            "usage_info": {"pages_processed": 1, "doc_size_bytes": None},
        },
        request=httpx.Request("POST", "https://example.invalid/v1/ocr"),
    )


async def test_extract_returns_parsed_json_from_mistral_response() -> None:
    expected = {"employee_name": "Ahmed Ali", "net_salary": 4500.0, "payment_date": "2026-07-01"}
    http_client = AsyncMock(spec=httpx.AsyncClient)
    http_client.post.return_value = _mistral_response(expected)

    service = MistralOCRService(settings=_settings(), http_client=http_client)
    result = await service.extract(b"%PDF-1.4 fake pdf bytes", "extract please")

    assert result == expected


async def test_extract_sends_pdf_as_document_url_and_requests_json_schema() -> None:
    http_client = AsyncMock(spec=httpx.AsyncClient)
    http_client.post.return_value = _mistral_response(
        {"employee_name": None, "net_salary": None, "payment_date": None}
    )

    service = MistralOCRService(settings=_settings(), http_client=http_client)
    await service.extract(b"raw-pdf-bytes", "my prompt")

    assert http_client.post.await_count == 1
    _, kwargs = http_client.post.await_args
    payload = kwargs["json"]
    assert payload["model"] == "mistral-ocr-latest"
    assert payload["document"]["type"] == "document_url"
    assert payload["document"]["document_url"].startswith("data:application/pdf;base64,")
    assert payload["document_annotation_format"]["type"] == "json_schema"
    assert payload["document_annotation_prompt"] == "my prompt"
    assert kwargs["headers"] == {"Authorization": "Bearer test-key"}


async def test_extract_raises_ocr_service_error_on_http_error() -> None:
    http_client = AsyncMock(spec=httpx.AsyncClient)
    http_client.post.side_effect = httpx.ConnectError("boom")

    service = MistralOCRService(settings=_settings(), http_client=http_client)

    with pytest.raises(OCRServiceError):
        await service.extract(b"pdf-bytes", "prompt")


async def test_extract_raises_ocr_service_error_on_malformed_response_shape() -> None:
    http_client = AsyncMock(spec=httpx.AsyncClient)
    http_client.post.return_value = httpx.Response(
        status_code=200,
        json={"unexpected": "shape"},
        request=httpx.Request("POST", "https://example.invalid/v1/ocr"),
    )

    service = MistralOCRService(settings=_settings(), http_client=http_client)

    with pytest.raises(OCRServiceError):
        await service.extract(b"pdf-bytes", "prompt")


async def test_extract_raises_ocr_service_error_on_null_document_annotation() -> None:
    http_client = AsyncMock(spec=httpx.AsyncClient)
    http_client.post.return_value = httpx.Response(
        status_code=200,
        json={
            "pages": [],
            "model": "mistral-ocr-latest",
            "document_annotation": None,
            "usage_info": {"pages_processed": 1, "doc_size_bytes": None},
        },
        request=httpx.Request("POST", "https://example.invalid/v1/ocr"),
    )

    service = MistralOCRService(settings=_settings(), http_client=http_client)

    with pytest.raises(OCRServiceError):
        await service.extract(b"pdf-bytes", "prompt")


async def test_extract_raises_ocr_service_error_on_invalid_json_text() -> None:
    http_client = AsyncMock(spec=httpx.AsyncClient)
    http_client.post.return_value = httpx.Response(
        status_code=200,
        json={
            "pages": [],
            "model": "mistral-ocr-latest",
            "document_annotation": "not json",
            "usage_info": {"pages_processed": 1, "doc_size_bytes": None},
        },
        request=httpx.Request("POST", "https://example.invalid/v1/ocr"),
    )

    service = MistralOCRService(settings=_settings(), http_client=http_client)

    with pytest.raises(OCRServiceError):
        await service.extract(b"pdf-bytes", "prompt")
