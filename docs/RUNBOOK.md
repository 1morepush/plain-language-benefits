# Runbook — Plain Language Benefits Translator

This is the **handoff document**. If you are taking this project over from someone who
has left, you can run, operate, and safely update the tool using only this page. No prior
experience with the code is assumed.

---

## 1. What this tool does (in one sentence)

It rewrites confusing public-benefits notices (SNAP, Medicaid, housing, unemployment)
into plain language a stressed reader can act on, while refusing to guess facts and
flagging high-stakes notices for a human to review.

## 2. One-time setup (about 10 minutes)

1. Install Python 3.10 or newer. Check with: `python --version`
2. In a terminal, go to this project folder.
3. Install the libraries it needs:
   ```
   pip install -r requirements.txt
   ```
4. Get an API key from <https://console.anthropic.com> → **Settings → API Keys**.
5. Copy the example secrets file and paste your key into it:
   ```
   cp .env.example .env          # macOS / Linux
   copy .env.example .env        # Windows (Command Prompt)
   ```
   Open `.env` in any text editor and put your key after `ANTHROPIC_API_KEY=` (no spaces,
   no quotes). The file must be named exactly `.env`. **Never share or commit this file** —
   it is already git-ignored. Do not put your key in any other (tracked) file.

## 3. Everyday use

Translate one notice and print the result:
```
python -m src.cli sample_docs/snap_recertification.txt
```
Swap in any `.txt` file path to translate a different notice. (To translate a PDF, first
copy its text into a `.txt` file — PDF reading is intentionally out of scope, see DESIGN.md.)

No API key handy? See a saved example output with no key and no network:
```
python -m src.cli --demo
```

## 4. Running the quality checks (evals)

Before trusting the tool after any change, run:
```
python evals/run_evals.py
```
It scores the tool on seven real-style notices (including adversarial ones) and writes a
report into `evals/results/`. You want **all cases passed**. If something fails, the report
lists exactly what to look at. See `docs/EVALS.md` for what each score means.

## 5. How to safely change how it writes

The wording rules live in **`src/prompts.py`** — that is the only file most people will
ever need to touch. To change behavior (e.g. "always explain acronyms"):

1. Edit the text inside `SYSTEM_PROMPT` in `src/prompts.py`.
2. Bump `PROMPT_VERSION` (e.g. `"v2"` → `"v3"`) so reports track your change.
3. Run `python evals/run_evals.py` and confirm you still get a clean pass.
4. If a score dropped, your wording change caused a regression — adjust and re-run.

**Do not** remove the four HARD RULES in the prompt without discussing it with a
program lead. They are what keep the tool from inventing deadlines or giving advice.

## 5b. Running the automated tests (no API key needed)

The fast, offline checks (reading level, fact coverage, forbidden facts, citation
grounding, escalation logic) run as unit tests:
```
pip install -r requirements-dev.txt
pytest -q
```
These same tests run automatically in GitHub Actions (`.github/workflows/ci.yml`) on every
push and pull request, so a broken change is caught before it merges.

## 6. Cost

The tool uses the `claude-sonnet-4-6` model by default for accuracy. Each notice is a
short request, so cost per notice is a fraction of a cent. To reduce cost further, change
`TRANSLATOR_MODEL` in `src/translate.py` to `"claude-haiku-4-5"` and re-run the evals to
confirm quality holds. The eval run makes a few extra calls for the faithfulness judge.

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| "ANTHROPIC_API_KEY is not set" | No `.env` or empty key | Redo step 2.4–2.5 |
| "Claude did not return valid JSON" | A prompt edit broke the output format | Revert your last edit to `src/prompts.py`; keep the JSON instructions intact |
| `ModuleNotFoundError` | Libraries not installed | Re-run `pip install -r requirements.txt` |
| Eval case fails on facts | A deadline/amount got dropped | Read the failure detail in the report; usually a prompt wording fix |

## 8. Who to contact

- **Program/technical lead:** _[template — fill in name + email at handoff]_
- **Anthropic API status:** <https://status.anthropic.com>
- This tool does **not** store or transmit any personal data beyond the single notice you
  paste in for that one request. Do not paste real notices containing other people's
  personal information without your organization's approval.
