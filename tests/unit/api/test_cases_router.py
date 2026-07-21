"""Unit tests for `POST /cases/process`. The SDK itself is faked -- this only tests HTTP wiring."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from loan_restructuring_sdk.api.dependencies import get_sdk
from loan_restructuring_sdk.api.main import app
from loan_restructuring_sdk.models.response import CaseStatus, SDKResponse, Stage1Result
from loan_restructuring_sdk.models.validation import ReasonCode, ValidationIssue, ValidationOutcome
from loan_restructuring_sdk.sdk import LoanRestructuringSDK
from loan_restructuring_sdk.utils.exceptions import DocumentReadError, OCRServiceError
from mock_backend.mock_data import MOCK_CASES


def test_process_case_endpoint_returns_sdk_response() -> None:
    fake_response = SDKResponse(
        case_id=1,
        application_number="APP-2026-0001",
        status=CaseStatus.REJECTED,
        stage1=Stage1Result(
            statement=None,
            validation=ValidationOutcome(
                passed=False,
                issues=[
                    ValidationIssue(
                        rule_name="NetSalaryExistsRule", reason_code=ReasonCode.NET_SALARY_MISSING, detail="missing"
                    )
                ],
            ),
        ),
        stage2=None,
        generated_at=datetime(2026, 7, 21, 12, 0, 0, tzinfo=timezone.utc),
    )
    fake_sdk = AsyncMock(spec=LoanRestructuringSDK)
    fake_sdk.process_case.return_value = fake_response

    app.dependency_overrides[get_sdk] = lambda: fake_sdk
    try:
        client = TestClient(app)
        payload = MOCK_CASES[1].model_dump(mode="json", by_alias=True)
        response = client.post("/cases/process", json=payload)
    finally:
        app.dependency_overrides.pop(get_sdk, None)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert body["case_id"] == 1
    assert body["stage1"]["validation"]["passed"] is False
    assert body["stage2"] is None
    fake_sdk.process_case.assert_awaited_once()


def test_document_read_error_returns_structured_400() -> None:
    fake_sdk = AsyncMock(spec=LoanRestructuringSDK)
    fake_sdk.process_case.side_effect = DocumentReadError("Could not read salary statement document: nope.pdf")

    app.dependency_overrides[get_sdk] = lambda: fake_sdk
    try:
        client = TestClient(app)
        payload = MOCK_CASES[1].model_dump(mode="json", by_alias=True)
        response = client.post("/cases/process", json=payload)
    finally:
        app.dependency_overrides.pop(get_sdk, None)

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "DocumentReadError"
    assert "nope.pdf" in body["detail"]


def test_ocr_service_error_returns_structured_502() -> None:
    fake_sdk = AsyncMock(spec=LoanRestructuringSDK)
    fake_sdk.process_case.side_effect = OCRServiceError("Mistral request failed: boom")

    app.dependency_overrides[get_sdk] = lambda: fake_sdk
    try:
        client = TestClient(app)
        payload = MOCK_CASES[1].model_dump(mode="json", by_alias=True)
        response = client.post("/cases/process", json=payload)
    finally:
        app.dependency_overrides.pop(get_sdk, None)

    assert response.status_code == 502
    assert response.json()["error"] == "OCRServiceError"
