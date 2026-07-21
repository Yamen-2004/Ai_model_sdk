"""Loan Scenario Engine: the three restructuring scenario strategies.

All amortization math lives in the separate, independent
`financial_calculator` package (`financial_calculator.calculator.FinancialCalculator`);
strategies here only decide which payment to solve for and delegate the
math (docs/SDD.md Goal G3 / Design Decisions D6, D13).
"""
