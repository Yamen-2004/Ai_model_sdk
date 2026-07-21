"""Financial Calculator: pure, reusable amortized-loan math.

No business rules live in this package -- no affordability caps, no
duration limits, no scenario-selection logic. Given a remaining balance,
an annual interest rate, and a monthly installment, it deterministically
computes what happens: the resulting duration, end date, total interest,
and total payment. Every restructuring scenario (a later stage) decides
*which* installment to pass in; this package only ever answers "what
happens if the customer pays exactly this much per month."

Must not depend on API DTOs, the Scenario Engine, the Priority Engine, the
Validation Engine, or the Response Builder -- verified by this package
never importing from `mapping`, `scenarios`, `priority`, `validation`, or
`response`.
"""
