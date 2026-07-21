"""Pydantic data contracts: DTOs, domain models, and result types, shared across the whole SDK.

Import direction is one-way: `case_dto` -> `mapping.case_mapper` -> `domain`.
Nothing outside `mapping/` should import `case_dto` (docs/SDD.md Design
Decision D10 / Goal G6).
"""
