"""PDF Extraction Engine: PDF bytes -> OCR Service -> a validated SalaryStatement.

Orchestrates the OCR Service call (the PDF is sent as-is, no local
page-image rendering -- docs/SDD.md Design Decision D5) and produces the
`SalaryStatement` the Validation Engine then checks.
"""
