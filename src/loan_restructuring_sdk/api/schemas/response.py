"""API response schemas."""

from __future__ import annotations

from loan_restructuring_sdk.models.response import SDKResponse


class ProcessCaseResponse(SDKResponse):
    """Response body for `POST /cases/process`. Identical to `SDKResponse` for now."""
