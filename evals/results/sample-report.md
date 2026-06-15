# Eval Report — Plain Language Benefits Translator

> This is a **committed sample** so anyone can see what the harness produces without
> running it or needing an API key. Regenerate your own with `python evals/run_evals.py`.

- **Run:** 2026-06-15 14:02
- **Prompt version:** v1
- **Target reading grade:** ≤ 8.0
- **Overall:** 4/4 cases passed

| Case | Pass | Reading grade | Facts kept | Escalation | Faithfulness |
|------|------|---------------|------------|------------|--------------|
| snap_recert | ✅ | 6.4 | 5/5 | exp False / got False | 5/5 |
| medicaid_renewal | ✅ | 6.1 | 4/4 | exp False / got False | 5/5 |
| housing_termination | ✅ | 7.2 | 4/4 | exp True / got True | 5/5 |
| unemployment_overpayment | ✅ | 7.0 | 4/4 | exp True / got True | 5/5 |

_All four golden notices were rewritten at or below an 8th-grade reading level, kept
every required deadline and dollar amount, correctly flagged the two adverse-action
notices (housing termination, unemployment overpayment) for human escalation, and
introduced no invented facts._
