# Plain Language — A Benefits Notice Translator

[![CI](https://github.com/1morepush/WIP-Project/actions/workflows/ci.yml/badge.svg)](https://github.com/1morepush/WIP-Project/actions/workflows/ci.yml)

> A safety-first AI tool that rewrites confusing government benefits notices into clear,
> plain language — with a drag-and-drop app, an evaluation harness, automated tests + CI,
> a staff workshop, and a handoff runbook.

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
- [In plain words (easy-reading summary)](#in-plain-words)
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

## In plain words

*(The whole project, explained simply. This section is written to be very easy to read — it
scores about **grade 2** on the same Flesch-Kincaid check the app runs on every notice, well
below the 6th-grade target.)*

**The problem.** The government sends letters about help like food, health care, and
housing. These letters are hard to read. People miss a date or a step. Then they lose help
they should get.

**What this does.** This tool takes one of those letters. It writes it again in clear,
simple words. It tells you what to do and by when. It shows the exact lines from your
letter, so you can check it. If the letter is serious or confusing, it tells you to ask a
real person. It never makes up a date or an amount.

**How you use it.** You can drag your letter into a simple app and download an easy version.
Or you can run it with one command if you like computers.

**How we know it works.** We made test letters with known answers. A checker grades each new
version. Is it easy to read? Did it keep every date? Did it make up anything? Did it know
when to ask for help? The tests run on their own each time we change the code.

**Why it is safe.** It does not give legal advice. It does not guess. Every fact comes from
your letter. Your letter and your key stay on your computer.

**What is in here.** The tool, the test letters and the checker, a short class to teach
staff, a guide so a new person can run it, and notes on how it was built.

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
- **A standing disclaimer** on every result: "this is a plain-language summary, not legal
  advice" — attached in code so it can never be dropped.

It is powered by the Claude API and is intentionally small and heavily commented, so that a
non-technical person can run it and a successor can maintain it.

**Two ways to use it:**
- a **command-line tool** (`python -m src.cli …`) for technical users and automation, and
- a **drag-and-drop web app** (`run_gui.sh` / `run_gui.bat`) for non-technical users — drag
  in a PDF/DOCX/TXT notice, download a plain-language file. See
  [Option C](#how-to-run-it) and [`docs/GUI.md`](docs/GUI.md).

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
  a notice file (.pdf / .docx / .txt)
        │  src/extract.py  (pull out the text)
        ▼
  src/translate.py  ──uses──▶  src/prompts.py   (the versioned, safety-first instructions)
        │                        Claude API
        ▼
  structured result:  plain_text · action_items · citations · confidence · escalate · disclaimer
        │
        ├──▶  src/cli.py            prints it / saves a .txt (--out)
        ├──▶  src/gui.py + output.py drag-drop app → download TXT/DOCX/PDF  (experimental)
        └──▶  evals/run_evals.py     scores it against the golden test cases
```

Everything funnels through one `translate()` call, so the CLI, the GUI, and the eval harness
share identical behavior. The instructions that govern the model live in one place
(`src/prompts.py`) and are **versioned**, so a non-technical successor can tune the wording
without touching code, and every eval report records which prompt version produced it.

---

## Proven with evaluations

"It worked once when I tried it" is not good enough for a tool that affects people's food
and housing. The harness (`evals/run_evals.py`) scores every change against fixed
[golden cases](evals/dataset.jsonl) on six dimensions:

| Metric | What it checks | Needs API? |
|--------|----------------|------------|
| **Reading grade** | Flesch-Kincaid grade of the rewrite (target ≤ 8) | No (local) |
| **Fact coverage** | Did every required deadline / amount / form survive? | No (local) |
| **Forbidden facts** | Did it invent a plausible-but-wrong fact (e.g. a transposed amount)? | No (local) |
| **Citation grounding** | Is every source quote really present in the original notice? | No (local) |
| **Escalation** | Did it flag a human on adverse actions, and stay quiet on routine ones? | No (local) |
| **Faithfulness** | An independent LLM judge checks for invented or changed facts | Yes |

The five local checks also run as fast **offline tests** in **GitHub Actions CI** on every
push — no API key required — so a broken change is caught before it merges. The suite (in
[`tests/`](tests/)) covers the judges, dataset integrity (every required fact is really in
its source, every "forbidden" fact really absent), and the GUI's file extraction and output
writers. See the regression evidence in
[`evals/results/v1-vs-v2.md`](evals/results/v1-vs-v2.md).

**Latest committed run (real — at [`evals/results/sample-report.md`](evals/results/sample-report.md)):**
_The suite has since grown to **7 golden cases**, including three adversarial ones (a
self-contradicting reduction, eligibility-advice bait, and an on-hold notice with no
deadline); this committed report shows the original four._

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
1. **Never invents facts** — every date/amount/number must trace to the source (enforced by
   the forbidden-facts and citation-grounding evals).
2. **Never gives advice** — it explains the notice; it doesn't predict eligibility.
3. **Keeps every deadline and action item.**
4. **Escalates** terminations, overpayments, denials, and ambiguous notices to a human.
5. **Always carries a disclaimer** — "a plain-language summary, not legal advice" — attached
   in code so a prompt edit can't remove it.

See [`docs/DESIGN.md`](docs/DESIGN.md) for the reasoning behind these trade-offs.

---

## How to run it

### Option A — see it without an API key
- See a **committed before→after**: input [`sample_docs/snap_recertification.txt`](sample_docs/snap_recertification.txt)
  → output [`outputs/snap_recertification.plain.txt`](outputs/snap_recertification.plain.txt).
- Open [`evals/results/sample-report.md`](evals/results/sample-report.md) for a real eval run.
- Or run the **offline demo** (a saved example, no key, no network):
```bash
pip install -r requirements.txt
python -m src.cli --demo
```

### Option B — run it live
Requires Python 3.10+ and an Anthropic API key (each notice costs a fraction of a cent).

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your API key (creates a private file that is git-ignored)
cp .env.example .env          # macOS/Linux  (Windows: copy .env.example .env)
#   then paste your key after ANTHROPIC_API_KEY=

# 3. Translate one notice (add --out to also save a readable .txt)
python -m src.cli sample_docs/snap_recertification.txt
python -m src.cli sample_docs/medicaid_renewal.txt --out outputs/medicaid_renewal.plain.txt
#   → prints the plain-language rewrite, action list, source quotes,
#     disclaimer, and the confidence / escalation status

# 4. Run the quality checks
python evals/run_evals.py
#   → scores all golden cases and writes a timestamped report into evals/results/

# (optional) run the offline unit tests
pip install -r requirements-dev.txt && pytest -q
```

> **Never put your API key in a tracked file.** It belongs only in the git-ignored `.env`.
> Full setup, costs, troubleshooting, and how to safely edit the prompt are in
> [`docs/RUNBOOK.md`](docs/RUNBOOK.md).

### Option C — the drag-and-drop app (no terminal)
For non-technical users: double-click **`run_gui.sh`** (macOS/Linux) or **`run_gui.bat`**
(Windows) to launch a browser app — paste your key once, drag in a `.pdf`/`.docx`/`.txt`
notice, and download a plain-language **TXT / DOCX / PDF**. See [`docs/GUI.md`](docs/GUI.md).
The first launch installs the extra deps in `requirements-gui.txt` (kept separate so the
core stays lean). The web UI is a thin layer over the same `translate()` — still a prototype
(not yet packaged as a double-click executable).

---

## Project layout

```
src/             core: prompts.py · translate.py · cli.py
                 GUI layer: extract.py (read PDF/DOCX/TXT) · output.py (write TXT/DOCX/PDF) · gui.py
sample_docs/     synthetic (fake-PII) benefits notices — the inputs (7, incl. adversarial)
outputs/         committed plain-language outputs (e.g. snap_recertification.plain.txt)
evals/           golden dataset, judges, runner, sample report + v1→v2 evidence
tests/           offline tests: judges, dataset integrity, extraction, output (run in CI)
examples/        a saved output for the offline `--demo`
docs/            RUNBOOK (handoff) · EVALS · DESIGN · PORTFOLIO · GUI
workshop/        facilitator guide · slide outline · hands-on exercise
run_gui.sh/.bat  one-click launchers for the drag-and-drop app
requirements*.txt core · -dev (tests/lint) · -gui (app only)
.github/         CI workflow (ruff + pytest on every push)
```

---

## How this maps to the Claude Corps Fellow role

The fellowship embeds you in a public-interest org to *build AI solutions, teach colleagues,
and ensure the work is maintainable after you leave.* This project is a deliberate miniature
of that engagement, mapped to the role's own responsibilities:

| Fellowship responsibility | In this project |
|---------------------------|-----------------|
| **Discovery & scoping** | Identified a concrete, high-impact problem (unreadable benefits notices) and scoped a tool with measurable outcomes (reading grade, facts kept). |
| **Development** | Built a working Claude-powered tool with structured output, a six-metric eval harness, offline tests, and CI — "agents, automations, internal tools, evaluation harnesses." |
| **Accessibility** | A drag-and-drop web app ([`docs/GUI.md`](docs/GUI.md)) so non-technical staff and recipients can use it with no terminal — meeting people where they are. |
| **Training & enablement** | A 60-minute workshop ([`workshop/`](workshop/)) for mixed technical / non-technical staff, with a hands-on exercise. |
| **Handoff & documentation** | A runbook ([`docs/RUNBOOK.md`](docs/RUNBOOK.md)) a successor can operate cold, plus design and eval docs. |
| **Strategic judgment** | Deliberate safety calls: no invented facts, no legal advice, human escalation on high-stakes notices, and synthetic-only data to protect PII. |

---

## Limitations & next steps

This is a **working prototype on synthetic data**, not a deployed system serving real people.
What's done so far: a CLI, a 7-case six-metric eval harness with CI, and a drag-and-drop GUI
that reads PDF/DOCX/TXT and writes TXT/DOCX/PDF. Honest next steps:
- **OCR for scanned notices** — the GUI reads digital PDFs/DOCX today, but a photo or scan of
  a letter has no selectable text yet.
- **Multi-language output** (Spanish, Vietnamese, Haitian Creole, and more).
- **A caseworker feedback loop** that grows the eval set with real, expert-flagged examples.
- **Package the GUI** as a true double-click app (PyInstaller) and prettify the PDF layout.

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
