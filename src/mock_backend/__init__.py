"""Mock backend: simulates the real banking backend that sends Case payloads to the SDK.

Exists purely for local development/testing of `loan_restructuring_sdk`'s
API layer against realistic data before a real backend integration exists.
Contains no OCR or business logic -- static mock data and simple lookups
only.
"""
