"""FastAPI application entrypoint. Run with: `uvicorn loan_restructuring_sdk.api.main:app --reload`."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from loan_restructuring_sdk.api.routers import cases
from loan_restructuring_sdk.config.logging_config import configure_logging
from loan_restructuring_sdk.utils.exceptions import (
    CaseMappingError,
    ConfigurationError,
    DocumentReadError,
    ExtractionError,
    OCRServiceError,
    SDKError,
)

# Every SDKError is a structural failure the caller must fix before retrying (docs/SDD.md section
# 5.6) -- never a business-rule rejection, which is always a normal SDKResponse instead. This maps
# each kind to the HTTP status that best describes whose fault it is; anything not listed here
# (e.g. a LoanCalculationError, which should be impossible given validated input) falls back to 500.
_STATUS_CODE_BY_EXCEPTION: dict[type[SDKError], int] = {
    CaseMappingError: 400,  # malformed Case payload
    DocumentReadError: 400,  # Case references a document that can't be read
    OCRServiceError: 502,  # upstream OCR provider call failed
    ExtractionError: 502,  # OCR provider responded, but not usably
    ConfigurationError: 500,  # server misconfigured (e.g. missing API key)
}


def _status_code_for(exc: SDKError) -> int:
    for exc_type, status_code in _STATUS_CODE_BY_EXCEPTION.items():
        if isinstance(exc, exc_type):
            return status_code
    return 500


def create_app() -> FastAPI:
    """Application factory: builds and returns a configured FastAPI instance."""
    configure_logging()
    app = FastAPI(
        title="Loan Restructuring SDK API",
        version="0.1.0",
    )
    app.include_router(cases.router)

    @app.exception_handler(SDKError)
    async def handle_sdk_error(request: Request, exc: SDKError) -> JSONResponse:
        """Translate an SDKError into a structured JSON error response instead of a bare 500."""
        return JSONResponse(
            status_code=_status_code_for(exc),
            content={"error": type(exc).__name__, "detail": str(exc)},
        )

    return app


app = create_app()
