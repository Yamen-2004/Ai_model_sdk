"""Validation Engine: Stage 1 business rules applied to an extracted SalaryStatement.

Runs every configured rule and aggregates all failures -- never fails fast
on the first broken rule (docs/SDD.md Design Decision D2 / Goal G2).
"""
