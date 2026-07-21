"""Mock backend API.

Simulates the real banking backend that sends `Case` payloads to the Loan
Restructuring SDK, so the SDK's API layer can be developed and tested
end-to-end before a real backend integration exists. No OCR or business
logic here -- only the endpoint and the models it returns (data lives in
`mock_data.py`).

Run with: `uvicorn mock_backend.main:app --reload --port 8001`
(a different port than the SDK's own API, so both can run side by side).
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from loan_restructuring_sdk.models.case_dto import Case
from mock_backend.mock_data import get_case

app = FastAPI(
    title="Mock Backend API",
    description="Simulates the backend system that sends Case payloads to the Loan Restructuring SDK.",
    version="0.1.0",
)


@app.get("/cases/{case_id}", response_model=Case)
def read_case(case_id: int) -> Case:
    """Return a single mock Case by id, or 404 if no mock case with that id exists."""
    case = get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return case
