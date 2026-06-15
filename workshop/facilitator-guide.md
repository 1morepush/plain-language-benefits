# Facilitator Guide — "Plain Language with AI" (60 minutes)

A workshop for **non-technical staff** at a benefits-serving organization (caseworkers,
intake coordinators, communications staff). Goal: by the end, participants can use the
tool responsibly, judge its output critically, and know when *not* to trust it.

This guide is the teaching artifact for the project. It is designed so that *another*
person could facilitate the session from these notes.

---

## Who it's for
Mixed technical comfort, including people who have never used an AI tool. Assume no coding.

## Learning objectives
By the end, each participant can:
1. Explain in one sentence what the tool does and does not do.
2. Run the tool on a sample notice (or watch it run) and read the output.
3. Spot a missing deadline or invented fact by checking output against the source.
4. Decide when a notice must go to a human instead.

## Materials
- This repo open on the facilitator's screen.
- Printed copies of one `sample_docs/` notice and its plain-language output.
- The one-page handout from `workshop/hands-on-exercise.md`.

## Run of show

| Time | Segment | What you do |
|------|---------|-------------|
| 0:00–0:05 | Welcome & why | Read a real-style notice aloud; ask "what's the deadline?" Watch people hunt. Name the problem. |
| 0:05–0:15 | What the tool is (and isn't) | Demo `python -m src.cli sample_docs/snap_recertification.txt`. Walk through plain text → action items → citations → escalate flag. Stress: it's a drafting aid, not a decision-maker. |
| 0:15–0:25 | The four safety rules | Explain: no invented facts, no advice, keep every deadline, escalate adverse actions. Show the housing-termination demo flagging `escalate: true`. |
| 0:25–0:45 | Hands-on | Participants do the exercise in `hands-on-exercise.md`: compare an output to its source and find anything missing or wrong. |
| 0:45–0:55 | Debrief | Collect what people caught. Reinforce: always check deadlines/amounts against the source; never paste real personal data without approval. |
| 0:55–1:00 | Wrap & resources | Point to `docs/RUNBOOK.md` for day-to-day use and where to get help. |

## Key messages to repeat
- "The tool drafts; **you decide**."
- "If a number isn't in the original, it shouldn't be in the rewrite — check."
- "When in doubt, escalate to a person."

## Common questions (be ready)
- *"Will this replace caseworkers?"* No — it saves time on explaining notices so staff can
  spend more time on people.
- *"Can we paste a real client's notice?"* Only with your organization's data-privacy
  approval. The demo uses fake notices on purpose.
- *"What if it gets something wrong?"* That's why every output shows source citations and
  why we run evals — and why a human checks high-stakes notices.
