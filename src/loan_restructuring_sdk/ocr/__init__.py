"""OCR Service: talks to the multimodal OCR provider (Mistral OCR) to read document page images.

Deliberately has no knowledge of PDFs, SalaryStatement, or business rules --
it only knows how to send images + a prompt and get raw structured JSON
back. That orchestration lives in `extraction/` (docs/SDD.md section 4).
"""
