# Loan Restructuring SDK

AI-powered Loan Restructuring SDK for banks. Given a full loan-restructuring case from a backend
system, it extracts and validates a salary-statement PDF (via Mistral OCR, multimodal), then —
only if validation passes — computes three amortized restructuring scenarios and a case priority
level.

See [docs/SDD.md](docs/SDD.md) for the full design rationale and decision log.

## Architecture

```
Stage 1: OCR Provider -> Extraction -> Validation
Stage 2: Financial Calculator -> Scenario Engine -> Priority Engine
```

A `Case` payload comes in, gets mapped to internal domain models, and Stage 1 extracts +
validates the applicant's salary statement. If validation fails, the case is rejected and Stage 2
never runs. If it passes, Stage 2 computes three restructuring scenarios (max affordability, min
installment, balanced) and scores the case's priority, and both stages' results come back in one
response.

## Requirements

- Python 3.12+
- A [Mistral API key](https://console.mistral.ai/api-keys) (used for OCR extraction)

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -e ".[dev]"

cp .env.example .env          # then fill in MISTRAL_API_KEY
```

## Running

```bash
uvicorn loan_restructuring_sdk.api.main:app --reload --port 8000
```

Interactive API docs: http://localhost:8000/docs

A mock backend (simulating the real bank system that would send `Case` payloads) is included for
local end-to-end testing, on a separate port:

```bash
uvicorn mock_backend.main:app --reload --port 8001
```

## API

### `POST /cases/process`

Request body: a `Case` (camelCase JSON — customer, loan, restructuring request, and a
`documents[]` entry pointing at a salary-statement PDF path).

Response body: an `SDKResponse` — `status` (`PROCESSED` or `REJECTED`), Stage 1's extracted
statement + validation outcome, and (if processed) Stage 2's three scenarios and priority level.

Structural failures (bad payload, unreadable document, OCR call failure, missing config) come
back as `{"error": "<ExceptionType>", "detail": "..."}` with an appropriate 4xx/5xx status —
business-rule rejections are never errors, just a normal `REJECTED` response.

See the `/docs` Swagger UI for the full request/response schema.

## Configuration

All settings are environment-driven (see `.env.example`):

| Variable | Purpose |
|---|---|
| `MISTRAL_API_KEY` | Mistral API key used for OCR extraction |
| `MISTRAL_MODEL` | OCR model (default `mistral-ocr-latest`) |
| `MISTRAL_API_BASE_URL` | Mistral API base URL |
| `MAX_INSTALLMENT_RATIO` | Affordability threshold for scenario feasibility |
| `MAX_LOAN_DURATION_MONTHS` | Cap on restructured loan duration |
| `MAX_STATEMENT_AGE_DAYS` | How old a salary statement can be before rejection |
| `LOG_LEVEL` | Logging verbosity |
| `API_HOST` / `API_PORT` | Bind address for `uvicorn` |

## Testing

```bash
pytest
```

Unit tests mock all external calls (no real network access); `tests/integration/` runs the full
wired-up SDK against the sample PDFs in `Salary_Statement/`, with only the Mistral OCR HTTP call
faked.

## Project structure

```
src/loan_restructuring_sdk/
  api/            FastAPI app, routes, DI composition root
  config/         Settings (env-driven)
  mapping/        Backend Case DTO -> internal domain models
  ocr/            OCR provider integration (Mistral)
  extraction/     OCR output -> SalaryStatement
  validation/     Stage 1 validation rules
  financial_calculator/  Amortization math
  scenarios/      Stage 2 restructuring scenario strategies
  priority/       Case priority scoring
  response/       Final response assembly
  models/         Shared DTOs / domain models
src/mock_backend/ Standalone mock of the real backend, for local end-to-end testing
tests/            Unit + integration tests
Salary_Statement/ Sample salary-statement PDFs used by tests/mock backend
docs/SDD.md       Full software design document
```
