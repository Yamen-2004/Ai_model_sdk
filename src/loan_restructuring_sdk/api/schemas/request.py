"""API request schemas."""

from __future__ import annotations

from loan_restructuring_sdk.models.case_dto import Case


class ProcessCaseRequest(Case):
    """Request body for `POST /cases/process`. Identical to `Case` for now -- see module docstring in `api/schemas`."""
