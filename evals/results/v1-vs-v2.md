# Regression evidence — prompt v1 → v2

This is the eval loop doing its job, captured from real runs. The point of an eval harness
is exactly this: change something, measure, and *see* whether it helped — without guessing.

## What the harness caught at v1

The first prompt (`v1`) produced rewrites that were often **too hard to read** and varied
from run to run. Two consecutive `v1` runs:

| Case | v1 run A — reading grade | v1 run B — reading grade |
|------|--------------------------|--------------------------|
| snap_recert | 7.3 | 10.7 ❌ |
| medicaid_renewal | 6.5 | 7.7 |
| housing_termination | 7.5 | 8.4 ❌ |
| unemployment_overpayment | 7.0 | 6.1 |

Run B pushed two notices **above the grade-8 target** — a real, user-facing problem the
harness flagged automatically. (Run A also surfaced a brittle golden test that matched the
exact phrase "telephone interview" instead of the safety-critical interview date; that test
was corrected to check the date.)

## The fix (v2)

Tightened the prompt's STYLE rules to **cap sentence length (~15 words) and explicitly target
a 6th-grade level**. Bumped `PROMPT_VERSION` to `v2` so reports are comparable.

## Result at v2

| Case | Pass | Reading grade | Facts kept | Escalation | Faithfulness |
|------|------|---------------|------------|------------|--------------|
| snap_recert | ✅ | 5.0 | 5/5 | exp False / got False | 4/5 |
| medicaid_renewal | ✅ | 4.9 | 4/4 | exp False / got False | 5/5 |
| housing_termination | ✅ | 6.4 | 4/4 | exp True / got True | 5/5 |
| unemployment_overpayment | ✅ | 5.7 | 4/4 | exp True / got True | 4/5 |

Every notice dropped from the **grade 7–10** range to **grade 5–6**, with all checks passing.

## Takeaway

*Measure → find the weak spot → fix it → prove the fix.* The reading-level regression was
caught by a metric, not by luck, and the improvement is visible in the numbers. That loop is
what makes an LLM tool trustworthy enough to put in front of people who can't afford a wrong
answer.
