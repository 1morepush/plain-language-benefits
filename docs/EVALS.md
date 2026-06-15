# Evals — what we measure and why

"It worked when I tried it once" is not enough for a tool that affects people's food,
health coverage, and housing. The eval harness (`evals/run_evals.py`) checks every change
against a fixed set of **golden cases** in `evals/dataset.jsonl`, so we can catch problems
before a real person ever sees them — and prove the tool works to a non-technical
stakeholder.

## The four things we score

### 1. Reading grade (no API needed)
We compute the Flesch-Kincaid grade level of the rewritten text with the `textstat`
library. Plain-language guidance in health and government commonly targets **grade 6–8**;
we flag anything above **8.0**. This is the whole point of the tool, so it is measured
first and for free.

### 2. Fact coverage (no API needed)
Each golden case lists `must_include_facts` — the deadlines, dollar amounts, form names,
and phone numbers that **must** survive the rewrite. The judge checks that each one still
appears in the output. **Dropping a deadline is the most dangerous failure**, so this
check is strict: missing even one fact fails the case.

### 3. Escalation correctness (no API needed)
Each case has an `expected_escalate` label. Notices whose main purpose is an **adverse
action** (a proposed termination, denial, reduction, or overpayment) should be flagged for
a human; routine renewals should not. This judge checks the tool's `escalate` flag against
the golden label. It measures the tool's *judgment*, not just its writing.

### 4. Faithfulness (LLM-as-judge)
A separate, independent model reads the source and the rewrite and scores 1–5 on whether
the rewrite invented or changed any fact. We require **≥ 4/5**. Using a different model to
grade is deliberate: the model being tested should never grade its own work.

## Why three of four checks use no API

Reading grade, fact coverage, and escalation are computed locally in plain Python. That
means most regressions are caught instantly and for free; only faithfulness costs a few
cents per run. This keeps the harness cheap enough to run on every prompt change.

## Regression tracking

Every report records the `prompt_version` from `src/prompts.py`. When you change the
prompt, bump that version and re-run. Comparing two reports tells you whether a wording
change helped or quietly broke something — the core discipline behind a "production LLM
deployment."

## Extending the dataset

To add a case, append one line to `evals/dataset.jsonl` with: a new `id`, the `doc` path,
the `must_include_facts`, and the `expected_escalate` label. The more varied (and tricky)
the notices, the more trustworthy the tool. Good additions: a notice with a typo'd date, a
bilingual notice, or one that is internally contradictory (which should escalate).
