# Plain Path: An AI Helper for Understanding Unemployment Forms

A class prototype for CRD 494 (AI Literacy) at ASU.

Plain Path explains the questions on the Arizona unemployment insurance (UI) application
in plain English and Spanish. **It is a reading aid only.**

> Plain Path is a student prototype, not legal advice and not affiliated with Arizona DES.

## Build status

| Stage | What it covers | Status |
|-------|----------------|--------|
| 1 | Project setup, data files, walkthrough, intake, checklist, language toggle, SSN blocker | **Built** |
| 2 | System prompt, explanation generator script, review gating | **Built** |
| 3 | "Ask about this question" chat | Not built yet |
| 4 | Test harness and RACCCA scoring CSV | Not built yet |

Everything in `data/` is currently **fake placeholder content**, labelled `PLACEHOLDER`.

## Hard rules

1. Never fill out, submit, or connect to the real application.
2. Never decide or predict eligibility.
3. Never suggest, rank, or reword an answer for the user.
4. No personal data. SSN-shaped text is blocked before it can reach the AI.
5. Never make up form content. Official wording comes only from `data/questions.json`.
6. The disclaimer above appears on every page.

## Setup

You need Python 3.10 or newer.

```bash
cd plain-path
```

```bash
python -m venv .venv
```

Turn the virtual environment on. On Windows:

```bash
.venv\Scripts\activate
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install the requirements and start the site:

```bash
pip install -r requirements.txt
```

```bash
python app.py
```

Then open <http://127.0.0.1:5000> in a browser. The website itself needs no API key.
The key is only needed to draft explanations (see below).

## What each file does

```
app.py               the Flask server: serves the page and /api/content, blocks SSNs
content.py           loads the data files; hides explanations that are not reviewed
ssn_guard.py         the SSN pattern and the warning text (server side)
data/
  questions.json     official question wording (you fill this in)
  explanations.json  plain-language explanations + "reviewed" flags
  sections.json      the sections of the form, in order
  intake.json        the five yes/no intake questions
  checklist.json     the document checklist
  help_links.json    DES help line and legal aid links
static/
  index.html         the one web page (header, footer, disclaimer)
  app.js             draws each screen: welcome, intake, documents, walkthrough, done
  i18n.js            all website text in English and Spanish
  ssn_guard.js       the browser copy of the SSN check
  style.css          the look of the site
prompts/
  system.md          the system prompt: every hard rule, in one file you can cite
scripts/
  generate_explanations.py   asks Claude to draft explanations (never marks them reviewed)
tests/               automated tests (SSN blocker, review gating, generator, data files)
```

## How to add questions

Add one entry per form question to `data/questions.json`:

```json
{
  "id": "separation_reason",
  "section": "separation",
  "official_text_en": "Exact wording copied from the official form.",
  "official_text_es": "Exact official Spanish wording, if you have it.",
  "source": "Document name and page number the wording came from",
  "high_risk": true
}
```

- `id` must be unique. `section` must match an `id` in `data/sections.json`.
- `official_text_es` is optional. Without it, the Spanish view shows the English wording
  with a note that the official text is only available in English.
- `high_risk: true` adds the "Check with a person" box.

To make a section or checklist item appear only for some people, add
`"show_if": "<intake key>"` to it in `sections.json` or `checklist.json`. It then shows
only when that intake question was answered Yes. The intake keys are in `intake.json`.

## How to draft explanations with Claude

The drafts are written ahead of time, not live for each visitor. That way you can read
every one before anyone else sees it.

1. Get an API key from the Anthropic Console and set it as an environment variable. The
   key is never written in the code. On Windows (PowerShell):

   ```bash
   $env:ANTHROPIC_API_KEY = "paste-your-key-here"
   ```

   On macOS or Linux:

   ```bash
   export ANTHROPIC_API_KEY="paste-your-key-here"
   ```

2. From the `plain-path` folder, see what would be drafted, without calling Claude:

   ```bash
   python -m scripts.generate_explanations --dry-run
   ```

3. Draft them:

   ```bash
   python -m scripts.generate_explanations
   ```

What the script does:

- Makes one call per question to `claude-sonnet-5-5`, using `prompts/system.md` as the
  system prompt. It sends only the official question text.
- Saves each draft to `data/explanations.json` with `reviewed_en` and `reviewed_es` set
  to `false`, so the site keeps showing "Explanation coming soon".
- Skips `PLACEHOLDER` questions, drafts that are waiting for review, and anything you
  have already reviewed. Add `--redo` to re-draft unreviewed drafts, or `--id <id>` to
  draft one question.
- Records `written_for` (the exact wording the draft explains) and `drafted_by` (the
  model that wrote it). If Claude declines a request, the API may hand it to another
  Claude model; `drafted_by` shows when that happened.

If you later change a question's official wording, its old explanation is hidden
automatically, even if it was reviewed, and the next run drafts a new one.

## How to review explanations

Each question has an entry in `data/explanations.json` under the same `id`:

```json
"separation_reason": {
  "explanation_en": "...",
  "explanation_es": "...",
  "you_will_need_en": ["..."],
  "you_will_need_es": ["..."],
  "check_with_person_reason_en": "...",
  "check_with_person_reason_es": "...",
  "reviewed_en": false,
  "reviewed_es": false,
  "written_for": "The official wording this draft explains.",
  "drafted_by": "claude-sonnet-5-5"
}
```

1. Read the draft next to the official wording.
2. Fix anything wrong, unclear, or that sounds like advice.
3. Change `reviewed_en` to `true`. Do the same for `reviewed_es` once the Spanish has
   been checked (ideally by a fluent speaker).

English and Spanish are approved separately. Until a language is marked `true`, the site
shows "Explanation coming soon. See official instructions." for it. The unreviewed text
never leaves the server.

## How to run the tests

```bash
pip install pytest
```

```bash
pytest -q
```

The tests cover the SSN blocker (including the server block and that the browser copy
matches), review gating, the explanation generator, and that the data files fit together.
They use a fake Claude, so they need no API key and cost nothing.

## Privacy

- The intake answers and checklist ticks stay in the browser (`sessionStorage`) and are
  deleted when the tab is closed. They are never sent to the server.
- Only the language choice is remembered between visits.
- The server stores and logs nothing a user types.

## Before a demo: things to verify

- The phone number and links in `data/help_links.json` were written from memory and
  **have not been checked** against the live websites. Confirm each one.
- The Spanish website text in `static/i18n.js` and `data/intake.json` should be read by a
  fluent Spanish speaker.
- Replace every `PLACEHOLDER` in `data/`.

## AI Use

This project was built with help from Claude Code (Anthropic). Claude Code wrote the
first version of the code, tests, and this README from my project proposal, and I
reviewed each stage. Plain-language explanations are drafted by the Claude API
(`claude-sonnet-5-5`) using the system prompt in `prompts/system.md`, and are shown only
after a person has reviewed them.
