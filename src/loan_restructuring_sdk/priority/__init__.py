"""Priority Engine: scores a case's urgency.

v1 is a single Arabic-keyword rule reading `priority_keywords.json`; the
`PriorityRuleInterface` + `PriorityContext` are shaped so future signals
(loan amount, remaining balance, salary, delayed installments, credit
score) can be added as new rule classes without touching this engine
(docs/SDD.md Design Decisions D7-D9).
"""
