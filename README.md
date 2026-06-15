# Plain Language — A Benefits Notice Translator

> A safety-first AI tool that rewrites confusing government benefits notices into clear,
> plain language — built end-to-end with evaluations, a staff workshop, and a handoff
> runbook.

Official benefits notices — SNAP, Medicaid, housing vouchers, unemployment — are often
written at a college reading level and packed with jargon. People miss deadlines they
didn't understand and lose food, health coverage, or housing they actually qualified for.

**Plain Language** rewrites those notices into clear, 6th-grade language a stressed reader
can act on — while refusing to invent facts and flagging high-stakes notices for a human
to review.

It is built across the four things a real public-interest AI project needs:
**Build → Evaluate → Teach → Hand off.**

---

## Table of contents
- [What it does](#what-it-does)
- [See it in action (real output)](#see-it-in-action-real-output)
- [How it works](#how-it-works)
- [Proven with evaluations](#proven-with-evaluations)
- [Safety-first by design](#safety-first-by-design)
- [How to run it](#how-to-run-it)
- [Project layout](#project-layout)
- [How this maps to the Claude Corps Fellow role](#how-this-maps-to-the-claude-corps-fellow-role)
- [Limitations & next steps](#limitations--next-steps)
- [A note on data & privacy](#a-note-on-data--privacy)

---

## What it does

Give it the text of a benefits notice, and it returns a structured result:

- **A plain-language rewrite** at roughly a 6th-grade reading level, leading with what the
  reader must do and by when.
- **A clear action list** — every step and deadline pulled out so nothing gets skimmed past.
- **Source citations** — short quotes from the original notice backing every key fact, so
  the output is auditable.
- **A confidence level** and an **escalation flag** — when a notice is high-stakes or
  ambiguous, the tool says "a person should help with this" instead of guessing.

It is powered by the Claude API and is intentionally small (~250 lines of heavily commented
Python) so that a non-technical person can run it and a successor can maintain it.

---

## See it in action (real output)

These are **actual outputs** from the command-line tool and the eval run (not mock-ups).

### Example 1 — a routine SNAP recertification (no escalation)

**Before** (`sample_docs/snap_recertification.txt`, excerpt):

> Your household's certification period for SNAP benefits will end on 06/30/2026… If the
> Division does not receive your completed recertification and required verifications by
> 06/20/2026, your SNAP benefits will stop on 06/30/2026 and you will need to file a new
> application to receive benefits again.

**After** — what the tool produced:

```
=== WHAT YOU NEED TO DO ===
  • Submit completed Form FA-100 (Application/Recertification) on or before 06/20/2026
  • Complete your phone interview on 06/16/2026 between 9:00 AM and 11:00 AM
  • If you miss the interview, call (555) 014-2200 to reschedule before 06/20/2026
  • Provide proof of current household income from the last 30 days by 06/20/2026
  • If you disagree with any action on your case, request a fair hearing within 90
    days of 06/02/2026

=== WHERE THIS COMES FROM (source quotes) ===
  "If the Division does not receive your completed recertification and required
   verifications by 06/20/2026, your SNAP benefits will stop on 06/30/2026…"

=== CONFIDENCE & SAFETY ===
  Confidence: high
  No escalation flagged.
```

### Example 2 — an unemployment overpayment (escalation triggered)

For an overpayment-and-appeal notice, the tool keeps the dollar amounts and the strict
20-day appeal deadline, and **flags it for a human** — here is the real escalation message
it generated:

```
=== CONFIDENCE & SAFETY ===
  Confidence: high
  ⚠ ESCALATE: A person should review this notice with you.
    Reason: The main purpose of this notice is an overpayment demand — an adverse
    action requiring repayment of $1,304.00 — so the reader should contact their
    caseworker or a local legal aid organization to understand their options before
    the 20-day appeal deadline passes.
```

That difference — staying quiet on a routine renewal but raising a hand on an adverse
action — is the core judgment built into the tool.

---

## How it works

```
benefits notice (text)
        │
        ▼
  src/translate.py  ──uses──▶  src/prompts.py   (the versioned, safety-first instructions)
        │                        Claude API
        ▼
  structured result:  plain_text · action_items · citations · confidence · escalate
        │
        ├──▶  src/cli.py        prints it for a human to read
        └──▶  evals/run_evals.py  scores it against golden test cases
```

The instructions that govern the model live in one place (`src/prompts.py`) and are
**versioned**, so a non-technical successor can tune the wording without touching code, and
every eval report records which prompt version produced it.

---

## Proven with evaluations

"It worked once when I tried it" is not good enough for a tool that affects people's food
and housing. The harness (`evals/run_evals.py`) scores every change against fixed
[golden cases](evals/dataset.jsonl) on four dimensions:

| Metric | What it checks | Needs API? |
|--------|----------------|------------|
| **Reading grade** | Flesch-Kincaid grade of the rewrite (target ≤ 8) | No (local) |
| **Fact coverage** | Did every required deadline / amount / form survive? | No (local) |
| **Escalation** | Did it flag a human on adverse actions, and stay quiet on routine ones? | No (local) |
| **Faithfulness** | An independent LLM judge checks for invented or changed facts | Yes |

**Latest run (real, committed at [`evals/results/sample-report.md`](evals/results/sample-report.md)):**

| Case | Pass | Reading grade | Facts kept | Escalation | Faithfulness |
|------|------|---------------|------------|------------|--------------|
| snap_recert | ✅ | 5.0 | 5/5 | exp False / got False | 4/5 |
| medicaid_renewal | ✅ | 4.9 | 4/4 | exp False / got False | 5/5 |
| housing_termination | ✅ | 6.4 | 4/4 | exp True / got True | 5/5 |
| unemployment_overpayment | ✅ | 5.7 | 4/4 | exp True / got True | 4/5 |

**The eval loop in action:** the first version of the prompt produced text at a grade 8–10
reading level — too hard, and inconsistent run to run. The harness caught it. Tightening the
prompt (capping sentence length, targeting grade 6) pulled every notice down to grade 5–6
with all checks passing. *Measure → find the weak spot → fix it → prove the fix* is the whole
discipline behind a trustworthy LLM tool. See [`docs/EVALS.md`](docs/EVALS.md).

---

## Safety-first by design

In benefits work, a confident wrong answer is worse than none. The tool therefore:
1. **Never invents facts** — every date/amount/number must trace to the source.
2. **Never gives advice** — it explains the notice; it doesn't predict eligibility.
3. **Keeps every deadline and action item.**
4. **Escalates** terminations, overpayments, denials, and ambiguous notices to a human.

See [`docs/DESIGN.md`](docs/DESIGN.md) for the reasoning behind these trade-offs.

---

## How to run it

### Option A — read the results without installing anything
Open [`evals/results/sample-report.md`](evals/results/sample-report.md) for a real eval run,
and the [output examples above](#see-it-in-action-real-output). No setup or API key needed.

### Option B — run it live
Requires Python 3.10+ and an Anthropic API key (each notice costs a fraction of a cent).

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your API key (creates a private file that is git-ignored)
cp .env.example .env          # then paste your key after ANTHROPIC_API_KEY=

# 3. Translate one notice
python -m src.cli sample_docs/snap_recertification.txt
#   → prints the plain-language rewrite, action list, source quotes,
#     and the confidence / escalation status

# 4. Run the quality checks
python evals/run_evals.py
#   → scores all four golden cases and writes a timestamped report
#     into evals/results/
```

> **Never put your API key in a tracked file.** It belongs only in the git-ignored `.env`.
> Full setup, costs, troubleshooting, and how to safely edit the prompt are in
> [`docs/RUNBOOK.md`](docs/RUNBOOK.md).

---

## Project layout

```
src/         translator (prompts.py · translate.py · cli.py)
sample_docs/ four synthetic (fake-PII) benefits notices
evals/       golden dataset, judges, runner, and a committed sample report
docs/        RUNBOOK (handoff) · EVALS · DESIGN · PORTFOLIO
workshop/    facilitator guide · slide outline · hands-on exercise
```

---

## How this maps to the Claude Corps Fellow role

The fellowship embeds you in a public-interest org to *build AI solutions, teach colleagues,
and ensure the work is maintainable after you leave.* This project is a deliberate miniature
of that engagement, mapped to the role's own responsibilities:

| Fellowship responsibility | In this project |
|---------------------------|-----------------|
| **Discovery & scoping** | Identified a concrete, high-impact problem (unreadable benefits notices) and scoped a tool with measurable outcomes (reading grade, facts kept). |
| **Development** | Built a working Claude-powered tool with structured output and an eval harness — "agents, automations, internal tools, evaluation harnesses." |
| **Training & enablement** | A 60-minute workshop ([`workshop/`](workshop/)) for mixed technical / non-technical staff, with a hands-on exercise. |
| **Handoff & documentation** | A runbook ([`docs/RUNBOOK.md`](docs/RUNBOOK.md)) a successor can operate cold, plus design and eval docs. |
| **Strategic judgment** | Deliberate safety calls: no invented facts, no legal advice, human escalation on high-stakes notices, and synthetic-only data to protect PII. |

---

## Limitations & next steps

This is a **working prototype on synthetic data**, not a deployed system serving real people.
Honest next steps:
- **Document upload + OCR** so staff can drop in a PDF or photo instead of pasting text.
- **Multi-language output** (Spanish, Vietnamese, Haitian Creole, and more).
- **A caseworker feedback loop** that grows the eval set with real, expert-flagged examples.
- **A "this is a plain-language summary, not legal advice" disclaimer** on every output.

Details in [`docs/DESIGN.md`](docs/DESIGN.md).

---

## A note on data & privacy

Every sample notice here is **fabricated** — realistic in structure and jargon, but with
invented names, case numbers, and amounts. Benefits notices contain sensitive personal
information; this project never uses real recipient data, and the runbook reminds operators
not to paste real personal data without their organization's approval.

---

## License

Released under the [MIT License](LICENSE).
