# Eval Report — Plain Language Benefits Translator

> This is a **committed sample from a real run** so anyone can see what the harness
> produces without running it or needing an API key. Regenerate your own with
> `python evals/run_evals.py`.

- **Run:** 2026-06-15 22:33
- **Prompt version:** v2
- **Target reading grade:** ≤ 8.0
- **Overall:** 4/4 cases passed

| Case | Pass | Reading grade | Facts kept | Escalation | Faithfulness |
|------|------|---------------|------------|------------|--------------|
| snap_recert | ✅ | 5.0 | 5/5 | exp False / got False | 4/5 |
| medicaid_renewal | ✅ | 4.9 | 4/4 | exp False / got False | 5/5 |
| housing_termination | ✅ | 6.4 | 4/4 | exp True / got True | 5/5 |
| unemployment_overpayment | ✅ | 5.7 | 4/4 | exp True / got True | 4/5 |

_All four notices were rewritten at roughly a 5th–6th-grade reading level, kept every
required deadline and dollar amount, correctly flagged the two adverse-action notices
(housing termination, unemployment overpayment) for human escalation, and stayed faithful
to the source._

## What this run taught us (the eval loop in action)

An earlier `v1` run surfaced two real issues that the eval caught:
1. A golden test checked for the exact phrase "telephone interview" — but the model wrote
   "phone interview" while keeping the interview **date**. The fix was to test the
   safety-critical fact (the date `06/16/2026`), not the wording.
2. Reading grades were too high and varied run-to-run (some notices landed at grade 8–10).
   Tightening the prompt to cap sentence length and target grade 6 (`v2`) pulled every
   notice down to the 5–6 range.

This is the point of evals: measure, find the weak spot, fix it, and prove the fix.
