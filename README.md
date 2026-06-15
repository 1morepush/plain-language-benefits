# Plain Language — A Benefits Notice Translator

Official benefits notices — SNAP, Medicaid, housing vouchers, unemployment — are often
written at a college reading level and packed with jargon. People miss deadlines they
didn't understand and lose food, health coverage, or housing they qualified for.

**Plain Language** is a small, safety-first AI tool that rewrites those notices into clear,
6th–8th-grade language a stressed reader can act on — while refusing to invent facts and
flagging high-stakes notices for a human to review.

It is built end-to-end across the four things a real public-interest AI project needs:
**Build → Evaluate → Teach → Hand off.**

---

## See it in action (no setup needed)

**Before** — an excerpt from a real-style SNAP notice (`sample_docs/snap_recertification.txt`):

> Your household's certification period for SNAP benefits will end on 06/30/2026. To
> continue receiving benefits without interruption, you must complete the recertification
> process described below… If the Division does not receive your completed recertification
> and required verifications by 06/20/2026, your SNAP benefits will stop on 06/30/2026…

**After** — what the tool produces (illustrative):

> **You need to keep your food assistance (SNAP). Here's how.**
> Your SNAP benefits end on **June 30, 2026**. To keep them, do these things by
> **June 20, 2026**:
> - Send in **Form FA-100** (the recertification form).
> - Do your **phone interview** on June 16, 2026 (9–11 AM). Missed it? Call (555) 014-2200
>   to reschedule before June 20.
> - Send recent **proof of income** (pay stubs, unemployment statements) from the last 30 days.
>
> If they don't get everything by June 20, 2026, your benefits stop June 30 and you'll
> have to apply again.
>
> *Source quotes, confidence, and a "see a person" flag are included with every result.*

> The committed eval report at [`evals/results/sample-report.md`](evals/results/sample-report.md)
> shows the tool passing 4/4 golden cases — you can read it without an API key.

---

## The four pillars

| Pillar | Where it lives | What it shows |
|--------|----------------|---------------|
| **Build** | `src/` | A focused Claude-powered tool: structured output with plain text, action items, source citations, a confidence level, and a human-escalation flag. |
| **Evaluate** | `evals/` | A real eval harness — reading grade, fact coverage, escalation correctness, and an independent LLM-as-judge faithfulness check — with prompt-version regression tracking. |
| **Teach** | `workshop/` | A 60-minute workshop for non-technical staff: facilitator guide, slide outline, and a hands-on "catch the mistake" exercise. |
| **Hand off** | `docs/` | A runbook a successor can operate cold, plus design notes and an evals explainer. |

## Safety-first by design

In benefits work, a confident wrong answer is worse than none. The tool therefore:
1. **Never invents facts** — every date/amount/number must trace to the source.
2. **Never gives advice** — it explains the notice; it doesn't predict eligibility.
3. **Keeps every deadline and action item.**
4. **Escalates** terminations, overpayments, denials, and ambiguous notices to a human.

See [`docs/DESIGN.md`](docs/DESIGN.md) for the reasoning behind these trade-offs.

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env          # then paste your Anthropic API key into .env

# Translate one notice:
python -m src.cli sample_docs/housing_voucher_notice.txt

# Run the quality checks:
python evals/run_evals.py
```

Full setup, costs, troubleshooting, and how to safely edit the tool are in
[`docs/RUNBOOK.md`](docs/RUNBOOK.md).

## How this maps to the Claude Corps Fellow role

The role embeds a fellow in a public-interest org to *build AI solutions, teach colleagues,
and ensure the work is maintainable after they leave.* This project is a miniature of
exactly that engagement: a scoped, high-impact tool for a benefits-serving org; an eval
harness that makes quality provable; a workshop that builds staff capability; and a runbook
that lets the work outlive its author.

## Project layout

```
src/         translator (prompts.py · translate.py · cli.py)
sample_docs/ four synthetic (fake-PII) benefits notices
evals/       golden dataset, judges, runner, and a committed sample report
docs/        RUNBOOK (handoff) · EVALS · DESIGN
workshop/    facilitator guide · slide outline · hands-on exercise
```

## Limitations & next steps

Text-in/text-out (no PDF upload yet), English-only, and a small four-case eval set. The
highest-value next features are multi-language output, document upload, and a caseworker
feedback loop that grows the eval set over time. Details in [`docs/DESIGN.md`](docs/DESIGN.md).

## A note on data

Every sample notice here is **fabricated**. Benefits notices contain sensitive personal
information; this project never uses real recipient data, and the runbook reminds operators
not to paste real personal data without their organization's approval.
