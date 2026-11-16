"""
generate_explanations.py — asks Claude to DRAFT a plain-language explanation for each
form question, and saves the drafts for a person to review.

Run it from the plain-path folder:

    python -m scripts.generate_explanations             draft every question that needs one
    python -m scripts.generate_explanations --dry-run   show what would happen, call nothing
    python -m scripts.generate_explanations --id ID     draft only this one question
    python -m scripts.generate_explanations --redo      also re-draft unreviewed drafts

How it stays safe:
  * It sends Claude only the official question text. No user data exists at this point.
  * Every draft is saved with "reviewed_en": false and "reviewed_es": false, so the
    website will not show it until a person approves it in data/explanations.json.
  * It never replaces an explanation a person has already reviewed, unless the official
    wording of that question has changed since the draft was written.
  * The API key is read from the ANTHROPIC_API_KEY environment variable. It is never
    written in this file.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import anthropic

from content import DATA_DIR, load_json

MODEL = "claude-sonnet-5-5"
SYSTEM_PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "system.md"

# Lets the API hand a declined request to another Claude model instead of failing.
# Each draft records which model actually wrote it (see "drafted_by").
FALLBACK_BETA = "server-side-fallback-2026-07-01"

# The exact shape Claude must reply in. The API enforces this, so the reply is always
# valid JSON with exactly these fields.
TEXT_FIELDS = [
    "explanation_en",
    "explanation_es",
    "check_with_person_reason_en",
    "check_with_person_reason_es",
]
LIST_FIELDS = ["you_will_need_en", "you_will_need_es"]
DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        **{name: {"type": "string"} for name in TEXT_FIELDS},
        **{name: {"type": "array", "items": {"type": "string"}} for name in LIST_FIELDS},
    },
    "required": TEXT_FIELDS + LIST_FIELDS,
    "additionalProperties": False,
}


def build_request(question: dict) -> str:
    """The message sent to Claude for one question."""
    risk = "yes" if question.get("high_risk") else "no"
    return f"""Draft the Plain Path entry for one question from the application.

<official_wording>
{question["official_text_en"]}
</official_wording>

Section of the form: {question["section"]}
Marked high risk by the project owner: {risk}

Write these fields:

- explanation_en: what this question is asking, in plain English. Explain the terms in it.
  Do not say or hint how to answer.
- explanation_es: the same explanation in plain Spanish.
- you_will_need_en: a short list of the kinds of documents or information a person would
  want next to them to answer this question truthfully. Base it only on what the wording
  asks for. Use an empty list if the question needs nothing looked up.
- you_will_need_es: the same list in Spanish.
- check_with_person_reason_en: if the question is marked high risk, one or two sentences on
  why it is worth talking with the agency or legal aid before answering, without predicting
  any outcome. If it is not marked high risk, use an empty string.
- check_with_person_reason_es: the same in Spanish."""


def needs_draft(question: dict, entry: dict | None, redo: bool) -> tuple[bool, str]:
    """Decide whether to draft this question, and say why (for the printed report)."""
    if question["official_text_en"].startswith("PLACEHOLDER"):
        return False, "skipped: placeholder text, nothing real to explain"
    if entry is None:
        return True, "no explanation yet"
    if entry.get("written_for") not in (None, question["official_text_en"]):
        return True, "the official wording changed since the last draft"
    if entry.get("reviewed_en") is True or entry.get("reviewed_es") is True:
        return False, "skipped: already reviewed by a person"
    if redo:
        return True, "re-drafting an unreviewed draft (--redo)"
    return False, "skipped: a draft is already waiting for review"


def draft_one(client, system_prompt: str, question: dict) -> dict:
    """Call Claude once for one question and return the new entry for explanations.json.

    Raises ValueError with a plain reason if Claude's reply cannot be used.
    """
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=system_prompt,
        messages=[{"role": "user", "content": build_request(question)}],
        output_config={"format": {"type": "json_schema", "schema": DRAFT_SCHEMA}},
        betas=[FALLBACK_BETA],
        fallbacks="default",
    )

    if response.stop_reason == "refusal":
        raise ValueError("Claude declined to write this one")
    if response.stop_reason == "max_tokens":
        raise ValueError("the reply was cut off before it finished")

    text = next((block.text for block in response.content if block.type == "text"), None)
    if text is None:
        raise ValueError("the reply had no text in it")
    try:
        draft = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError("the reply was not valid JSON") from error

    # Double-check the shape ourselves, so a bad reply can never reach the data file.
    for name in TEXT_FIELDS:
        if not isinstance(draft.get(name), str):
            raise ValueError(f"the reply is missing '{name}'")
    for name in LIST_FIELDS:
        items = draft.get(name)
        if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
            raise ValueError(f"the reply is missing '{name}'")
    if not draft["explanation_en"].strip() or not draft["explanation_es"].strip():
        raise ValueError("the explanation came back empty")

    entry = {name: draft[name] for name in TEXT_FIELDS + LIST_FIELDS}
    # A new draft is NEVER reviewed. Only a person changes these to true.
    entry["reviewed_en"] = False
    entry["reviewed_es"] = False
    # Remember exactly which wording this was written for, and which model wrote it.
    entry["written_for"] = question["official_text_en"]
    entry["drafted_by"] = response.model
    return entry


def save(explanations: dict, data_dir: Path) -> None:
    with open(data_dir / "explanations.json", "w", encoding="utf-8") as f:
        json.dump(explanations, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main(argv=None, client=None, data_dir: Path = DATA_DIR) -> int:
    parser = argparse.ArgumentParser(description="Draft plain-language explanations with Claude.")
    parser.add_argument("--id", help="draft only the question with this id")
    parser.add_argument("--redo", action="store_true", help="also re-draft unreviewed drafts")
    parser.add_argument("--dry-run", action="store_true", help="show the plan, call nothing")
    args = parser.parse_args(argv)

    questions = load_json("questions.json", data_dir)
    explanations = load_json("explanations.json", data_dir)
    if args.id:
        questions = [q for q in questions if q["id"] == args.id]
        if not questions:
            print(f"No question with id '{args.id}' in data/questions.json.")
            return 1

    plan = [(q, *needs_draft(q, explanations.get(q["id"]), args.redo)) for q in questions]
    todo = [(q, reason) for q, wanted, reason in plan if wanted]
    for q, wanted, reason in plan:
        print(f"  {'DRAFT' if wanted else '  -  '}  {q['id']}: {reason}")

    if args.dry_run or not todo:
        print(f"\n{len(todo)} question(s) to draft. Nothing was sent to Claude.")
        return 0

    if client is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("\nANTHROPIC_API_KEY is not set. See the README for how to set it.")
            return 1
        client = anthropic.Anthropic()
    system_prompt = SYSTEM_PROMPT_FILE.read_text(encoding="utf-8")

    drafted, failed = 0, 0
    for question, _reason in todo:
        try:
            explanations[question["id"]] = draft_one(client, system_prompt, question)
        except anthropic.AuthenticationError:
            print("\nThe API key was rejected. Check ANTHROPIC_API_KEY and try again.")
            return 1
        except (ValueError, anthropic.APIStatusError, anthropic.APIConnectionError) as error:
            # One bad question must not stop the rest.
            failed += 1
            print(f"  FAILED  {question['id']}: {error}")
            continue
        # Save after every question, so a crash never loses work already paid for.
        save(explanations, data_dir)
        drafted += 1
        print(f"  saved   {question['id']}")

    print(f"\n{drafted} drafted, {failed} failed.")
    print("Drafts are hidden on the site until you review them in data/explanations.json.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
