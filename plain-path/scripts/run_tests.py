"""
run_tests.py — sends each test question to Claude and saves the replies to a CSV file
that you score by hand for the findings report.

Run it from the plain-path folder:

    python -m scripts.run_tests              run every row of tests/test_questions.csv
    python -m scripts.run_tests --dry-run    show what would be sent, call nothing
    python -m scripts.run_tests --allow-placeholders
                                             run even though the form questions are fake

Each test question goes down the same path as a real message in the "Ask about this
question" box: SSN check, then "is this question in the data file?", then one call to
Claude. The results file records:

    raw_response    exactly what Claude wrote (before the safety check)
    shown_to_user   what the website would have shown (the safe message if flagged)
    auto_check      ok / FLAGGED / blocked_ssn / not_in_file / error
    auto_flags      what the keyword check found, if anything

followed by empty columns for you to score 1 to 3 on each RACCCA criterion
(Relevance, Accuracy, Completeness, Clarity, Coherence, Appropriateness) and a notes
column. The script never fills those in.
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

import anthropic

import ask
from content import build_content
from safety_check import find_flags
from ssn_guard import WARNING_EN, WARNING_ES, looks_like_ssn

HERE = Path(__file__).parent.parent
TEST_FILE = HERE / "tests" / "test_questions.csv"
RESULTS_DIR = HERE / "tests" / "results"

RACCCA = ["relevance", "accuracy", "completeness", "clarity", "coherence", "appropriateness"]
COLUMNS = [
    "id", "category", "expected", "lang", "question_id", "test_question",
    "raw_response", "shown_to_user", "auto_check", "auto_flags", "model",
    *RACCCA, "notes",
]


def read_tests(path: Path) -> list[dict]:
    # utf-8-sig also reads files saved by Excel, which adds a hidden mark at the start.
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [row for row in csv.DictReader(f) if (row.get("test_question") or "").strip()]


def run_one(client, questions: dict, test: dict) -> dict:
    """Run one test row and return the result columns for it."""
    lang = "es" if test.get("lang") == "es" else "en"
    message = test["test_question"].strip()
    result = {"raw_response": "", "shown_to_user": "", "auto_flags": "", "model": ""}

    # Step 1: the SSN blocker. A blocked message is never sent to Claude.
    if looks_like_ssn(message):
        result["shown_to_user"] = WARNING_ES if lang == "es" else WARNING_EN
        result["auto_check"] = "blocked_ssn"
        return result

    # Step 2: only questions in the data file can be discussed.
    question = questions.get(test.get("question_id"))
    if question is None:
        result["shown_to_user"] = ask.NOT_IN_FILE[lang]
        result["auto_check"] = "not_in_file"
        return result

    # Step 3: one call to Claude, then the same keyword check the website uses.
    raw = ask.ask_claude(client, question, message, lang)
    flags = find_flags(raw["text"])
    result["raw_response"] = raw["text"]
    result["shown_to_user"] = ask.checked_reply(raw, lang)["reply"]
    result["model"] = raw["model"]
    result["auto_flags"] = "; ".join(f'{flag["kind"]}: "{flag["match"]}"' for flag in flags)
    if flags:
        result["auto_check"] = "FLAGGED"
    elif raw["stop_reason"] != "end_turn":
        result["auto_check"] = f"FLAGGED (reply ended early: {raw['stop_reason']})"
    else:
        result["auto_check"] = "ok"
    return result


def write_results(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig makes Excel show Spanish accents correctly.
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None, client=None, test_file: Path = TEST_FILE, out_file: Path | None = None):
    parser = argparse.ArgumentParser(description="Run the Plain Path test questions.")
    parser.add_argument("--dry-run", action="store_true", help="show the plan, call nothing")
    parser.add_argument("--allow-placeholders", action="store_true",
                        help="run even if a test points at a PLACEHOLDER form question")
    args = parser.parse_args(argv)

    tests = read_tests(test_file)
    questions = {q["id"]: q for q in build_content()["questions"]}
    print(f"{len(tests)} test question(s) in {test_file.name}.")

    # Asking about fake form questions tells you nothing, so stop unless told otherwise.
    fake = sorted({
        t["question_id"] for t in tests
        if t.get("question_id") in questions
        and questions[t["question_id"]]["official_text_en"].startswith("PLACEHOLDER")
    })
    if fake and not args.allow_placeholders:
        print(f"\nThese tests point at PLACEHOLDER form questions: {', '.join(fake)}")
        print("Add real questions to data/questions.json and update the question_id column")
        print("in tests/test_questions.csv, or re-run with --allow-placeholders.")
        return 1

    if args.dry_run:
        for test in tests:
            print(f"  {test['id']}  [{test['category']}]  {test['test_question']}")
        print("\nNothing was sent to Claude.")
        return 0

    if client is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("\nANTHROPIC_API_KEY is not set. See the README for how to set it.")
            return 1
        client = anthropic.Anthropic(timeout=60.0)

    rows = []
    for test in tests:
        row = {column: test.get(column, "") for column in COLUMNS[:6]}
        try:
            row.update(run_one(client, questions, test))
        except anthropic.AuthenticationError:
            print("\nThe API key was rejected. Check ANTHROPIC_API_KEY and try again.")
            return 1
        except anthropic.APIError as error:
            # One failed call must not lose the rest of the run.
            row.update({"auto_check": "error", "auto_flags": str(error)})
        rows.append(row)
        print(f"  {row['id']}  {row['auto_check']}")

    if out_file is None:
        out_file = RESULTS_DIR / f"results-{datetime.now():%Y%m%d-%H%M%S}.csv"
    write_results(out_file, rows)

    flagged = sum(1 for row in rows if row["auto_check"].startswith("FLAGGED"))
    errors = sum(1 for row in rows if row["auto_check"] == "error")
    print(f"\nSaved {len(rows)} row(s) to {out_file}")
    print(f"{flagged} flagged by the automatic check, {errors} error(s).")
    print("The automatic check is a keyword match. Read every reply and score it yourself.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
