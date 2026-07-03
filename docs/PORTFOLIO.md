# Talking points — Plain Language (for applications, résumé, interviews)

Honest framing: this is a **working prototype built on synthetic data**, not a deployed
system serving real people. Describe it as a proof-of-concept that demonstrates the full
build → evaluate → teach → hand-off lifecycle. Don't claim usage numbers or real impact.

---

## Résumé bullets (pick 2–3)

- Built a safety-first AI tool (Python, Claude API) that rewrites dense public-benefits
  notices — SNAP, Medicaid, housing vouchers, unemployment — into 6th-grade plain language,
  with source citations and an automatic human-escalation flag for high-stakes notices.
- Designed a six-metric evaluation harness (reading level, fact coverage, a forbidden-facts
  hallucination guard, citation grounding, escalation accuracy, and an LLM-as-judge
  faithfulness check) with prompt-version regression tracking; used it across two real
  improvement rounds — cutting output from ~grade 8–10 to grade 5–6, then catching a missed
  escalation and a parsing bug in a live run — to reach 7/7 passing golden cases.
- Wrote a runbook, design docs, and a 60-minute hands-on workshop so non-technical staff
  could operate and maintain the tool — demonstrating the full delivery-and-handoff lifecycle.
- Made deliberate safety/judgment calls: forbade the model from inventing deadlines or
  amounts, blocked it from giving legal advice, and used only synthetic data to protect PII.

## One-line version

> Built and evaluated a Claude-powered tool that turns confusing government benefits
> notices into plain language, with a safety-first design and an eval harness to prove it
> works — plus a workshop and runbook so non-technical staff can run it.

## Short project summary (~120 words — good for an application essay box)

People lose benefits they qualify for because official notices are written at a college
reading level and easy to skim past a deadline. I built **Plain Language**, a tool that
rewrites SNAP, Medicaid, housing, and unemployment notices into clear 6th-grade language
a stressed reader can act on. It's safety-first: it never invents facts, won't give legal
advice, cites the source for every claim, and flags high-stakes notices (terminations,
overpayments) for a human. I didn't stop at building it — I wrote a six-metric evaluation
harness (reading level, fact retention, hallucination and citation checks, escalation,
faithfulness) and used it through two real improvement rounds: tuning the prompt from grade
8–10 down to grade 5–6, then catching a missed escalation and a parsing bug in a live run,
ending at 7/7 passing cases. I also wrote a staff workshop and a runbook so the work
outlives me.

## LinkedIn / blog post (first person)

I built a small AI tool to tackle a problem I find quietly infuriating: people lose food
assistance, health coverage, and housing they qualify for — not because they're ineligible,
but because the notices are impossible to read.

**Plain Language** rewrites dense benefits notices (SNAP, Medicaid, housing, unemployment)
into clear, 6th-grade language, with the deadlines and steps up front. But the interesting
part isn't the rewrite — it's the guardrails. In benefits work, a confident wrong answer
can cost someone their housing. So the tool never invents a date or dollar amount, refuses
to give legal advice, cites the original notice for every claim, and flags high-stakes
notices for a caseworker instead of guessing.

To prove it actually works, I built an evaluation harness that scores reading level, whether
every deadline survived, whether it invented any fact, whether its citations are real quotes,
whether it escalated the right cases, and whether it stayed faithful to the source. The first
run flagged output reading at a grade 8–10 level — too hard; a later live run caught a missed
escalation on a benefits-hold notice and a parsing bug. Each fix was proven by re-running the
suite to 7/7. That loop — measure, find the weak spot, fix it, prove it — is the whole game
with AI tools.

I also wrote a staff workshop and a runbook, because a tool nobody can run or maintain isn't
much help.

#AIforGood #CivicTech #PublicBenefits

## Cover-letter paragraph (drop into your application)

> I'm drawn to Claude Corps because I want to put AI to work where it's needed most and
> least available — public-benefits and civic services — and because the role values the
> whole lifecycle, not just a demo. To show what that looks like, I built **Plain Language**,
> a tool that rewrites confusing government benefits notices (SNAP, Medicaid, housing,
> unemployment) into clear, 6th-grade language, with source citations and a human-escalation
> safeguard for high-stakes notices like terminations and overpayments. I treated it like a
> real deployment: I wrote a six-metric evaluation harness (reading level, fact retention,
> hallucination and citation checks, escalation accuracy, faithfulness) and used it through
> two real improvement rounds — tuning grade 8–10 output down to grade 5–6, then catching a
> missed escalation in a live run — to reach 7/7 passing cases. I
> also wrote a staff workshop and a handoff runbook, because a tool nobody can run or maintain
> doesn't help anyone. That instinct — build it, prove it works, teach it, and make it
> outlast me — is exactly the kind of utility-player work I want to do for a host organization
> as a Fellow.

## Likely interview questions (be ready)

- *"How do you stop it from hallucinating a deadline?"* → Prompt forbids unsupported facts;
  faithfulness eval (independent LLM judge) measures it; every claim shows a source citation.
- *"How would you deploy this for real?"* → Add document upload + OCR, multi-language output,
  a caseworker feedback loop that grows the eval set, and a "not legal advice" disclaimer.
  Pilot with one office, measure, then expand. (See docs/DESIGN.md.)
- *"How did you decide what to escalate?"* → Adverse actions (termination, overpayment,
  denial) and ambiguous notices go to a human; routine renewals don't. It's a judgment call
  I encoded in the prompt and test in the eval.
- *"What would you teach non-technical staff first?"* → "The tool drafts; you decide" — always
  check deadlines and amounts against the original. (See workshop/.)
