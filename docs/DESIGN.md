# Design notes & decisions

This page records *why* the tool is built the way it is — the kind of reasoning a
fellow is expected to document for the people who inherit the work.

## The problem

People lose benefits they qualify for because official notices are written at a college
reading level, full of program jargon, and easy to skim past a critical deadline. The
goal is not to replace caseworkers — it is to help a recipient understand what a notice
says and what to do, and to know when they need a human.

## Why "safety first" instead of "helpful first"

In this domain a confident wrong answer is worse than no answer. A hallucinated deadline
or a casual "you probably still qualify" can directly cost someone their food or housing.
So the design makes three deliberate trade-offs:

1. **No invented facts.** Every date/amount/number in the rewrite must trace to the
   source. The prompt forbids guessing; the faithfulness eval enforces it.
2. **No advice.** The tool describes what the notice says and asks for; it never predicts
   eligibility or gives legal guidance.
3. **Escalate the high-stakes cases.** Adverse actions (terminations, overpayments,
   denials) and ambiguous notices are flagged for a caseworker or legal aid rather than
   "solved" by the tool. This is the human-in-the-loop safety valve.

## Why these components

- **`src/prompts.py` is separate and versioned** because the prompt is what a
  non-technical successor is most likely to tune. Isolating it keeps changes low-risk and
  lets eval reports track which version produced which result.
- **The output is structured JSON** (plain text + action items + citations + escalate
  flag) rather than a paragraph, so downstream tools and the eval harness can both use it,
  and so citations make every claim auditable. The `citation_grounding` eval enforces that
  those quotes are really in the source, so "auditable" is checked, not just claimed.
- **A safety disclaimer is attached to every result in code** (`DISCLAIMER` in
  `src/translate.py`), so the reader is never misled — and it can't be dropped by a prompt edit.
- **Five of six evals run locally** to keep quality checks fast and nearly free, and they
  double as offline unit tests in CI.

## Synthetic data, on purpose

All notices in `sample_docs/` are fabricated — realistic in structure and jargon but with
invented names, case numbers, and amounts. Public-benefits notices contain sensitive
personal information; a portfolio/demo project must never train, test, or ship on real
recipient data. This is itself a judgment call worth showing.

## Known limitations (and honest next steps)

- **Digital documents only.** PDF, DOCX, and TXT files are parsed (CLI and GUI), but a
  scanned image or photo of a letter has no selectable text — that still needs OCR, which
  a real deployment would add.
- **English only.** Many recipients need Spanish, Vietnamese, Haitian Creole, etc.
  Multi-language output is the highest-value next feature.
- **Still a modest eval set.** Seven notices — including adversarial cases (an internal
  contradiction, eligibility-advice bait, and an on-hold notice with no deadline) — is a
  solid start, not a guarantee. A real deployment grows the golden set continuously, ideally
  with examples flagged by caseworkers.
- **No live feedback loop.** The strongest version would let caseworkers mark a rewrite as
  good/bad and feed that back into the eval set.
- **Not a legal authority.** Every result carries a "this is a plain-language summary, not
  legal advice" disclaimer (set in code so it can't be dropped). A real deployment would also
  show it prominently in any UI.
