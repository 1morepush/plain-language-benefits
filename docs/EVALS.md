# Evals — what we measure and why

"It worked when I tried it once" is not enough for a tool that affects people's food,
health coverage, and housing. The eval harness (`evals/run_evals.py`) checks every change
against a fixed set of **golden cases** in `evals/dataset.jsonl`, so we can catch problems
before a real person ever sees them — and prove the tool works to a non-technical
stakeholder.

## The six things we score

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

### 3. Forbidden facts — hallucination guard (no API needed)
Each case also lists `forbidden_facts`: a few values that look plausible but are **wrong**
(e.g. a transposed dollar amount `$1,840` when the real rent is `$1,480`, or a `30`-day
appeal window when the notice says `20`). If any of these appears in the output, the tool
invented something — the case fails. This catches the most dangerous kind of error directly.

### 4. Citation grounding (no API needed)
The tool returns short source quotes to back up its claims. This check verifies every quote
is **really present in the source** (whitespace/quote-normalized, ellipsis-aware). It is what
makes "every claim is auditable" true rather than just a promise.

### 5. Escalation correctness (no API needed)
Each case has an `expected_escalate` label. Notices whose main purpose is an **adverse
action** (a proposed termination, denial, reduction, or overpayment) should be flagged for
a human; routine renewals should not. This judge checks the tool's `escalate` flag against
the golden label. It measures the tool's *judgment*, not just its writing.

### 6. Faithfulness (LLM-as-judge)
A separate, independent model reads the source and the rewrite and scores 1–5 on whether
the rewrite invented or changed any fact. We require **≥ 4/5**. Using a different model to
grade is deliberate: the model being tested should never grade its own work.

## Why five of six checks use no API

Reading grade, fact coverage, forbidden facts, citation grounding, and escalation are all
computed locally in plain Python — so most regressions are caught instantly and for free;
only faithfulness costs a few cents per run. The five local checks also run as fast offline
unit tests (`tests/test_judges.py`) in CI on every push, with no API key.

## Regression tracking

Every report records the `prompt_version` from `src/prompts.py`. When you change the
prompt, bump that version and re-run. Comparing two reports tells you whether a wording
change helped or quietly broke something — the core discipline behind a "production LLM
deployment."

## Extending the dataset

To add a case, append one line to `evals/dataset.jsonl` with: a new `id`, the `doc` path,
the `must_include_facts`, `forbidden_facts`, and the `expected_escalate` label. The more
varied (and tricky) the notices, the more trustworthy the tool.

The set already includes **adversarial** cases: a benefit reduction with two contradicting
effective dates (must escalate), an outreach notice that tempts an eligibility claim (must
*not* assert "you qualify"), and a claim "under review" with no deadline (must escalate and
must not invent one). An offline integrity test (`tests/test_dataset.py`) checks that every
`must_include_fact` really appears in its source and every `forbidden_fact` is genuinely
absent — so a malformed case is caught immediately. Good further additions: a notice with a
typo'd date, or a bilingual notice.
