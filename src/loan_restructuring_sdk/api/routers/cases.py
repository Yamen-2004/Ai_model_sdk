"""HTTP routes for submitting loan-restructuring cases to the SDK."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from loan_restructuring_sdk.api.dependencies import get_sdk
from loan_restructuring_sdk.api.schemas.request import ProcessCaseRequest
from loan_restructuring_sdk.api.schemas.response import ProcessCaseResponse
from loan_restructuring_sdk.sdk import LoanRestructuringSDK

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("/process", response_model=ProcessCaseResponse)
async def process_case(
    request: ProcessCaseRequest,
    sdk: LoanRestructuringSDK = Depends(get_sdk),
) -> ProcessCaseResponse:
    """Run a Case through the SDK's two-stage pipeline and return the resulting SDKResponse."""
    result = await sdk.process_case(request)
    return ProcessCaseResponse.model_validate(result, from_attributes=True)
