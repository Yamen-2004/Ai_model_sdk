"""SDK-wide exception hierarchy.

Business-rule rejections (a case failing Stage 1 validation) are never
exceptions -- they are normal `ValidationOutcome` / `SDKResponse` values
(see docs/SDD.md section 5.6). These exceptions are reserved for structural
failures the caller must fix before retrying (bad input, unreachable
service, missing configuration).
"""

from __future__ import annotations


class SDKError(Exception):
    """Base class for every exception raised by the Loan Restructuring SDK."""


class CaseMappingError(SDKError):
    """Raised when an incoming Case payload cannot be mapped to internal domain models."""


class DocumentReadError(SDKError):
    """Raised when a referenced document file cannot be read or is not a valid PDF."""


class OCRServiceError(SDKError):
    """Raised when the OCR service (Mistral OCR) call fails or returns an unusable response."""


class ExtractionError(SDKError):
    """Raised when OCR output cannot be parsed into a well-formed SalaryStatement."""


class ConfigurationError(SDKError):
    """Raised when required configuration (e.g. an API key) is missing or invalid."""


class LoanCalculationError(SDKError):
    """Base class for invalid or mathematically infeasible Financial Calculator inputs."""


class InvalidPrincipalError(LoanCalculationError):
    """Raised when remaining balance is <= 0."""


class InvalidInstallmentError(LoanCalculationError):
    """Raised when monthly installment is <= 0."""


class InvalidInterestRateError(LoanCalculationError):
    """Raised when annual interest rate is < 0."""


class InfeasiblePaymentError(LoanCalculationError):
    """Raised when the monthly installment does not cover monthly interest, so the loan would never amortize."""


class InvalidDurationError(LoanCalculationError):
    """Raised when a target loan duration is <= 0."""


class PriorityEngineError(SDKError):
    """Base class for Priority Engine configuration/structural failures."""


class KeywordConfigurationError(PriorityEngineError):
    """Raised when `priority_keywords.json` is missing, unreadable, or not well-formed."""
