"""
cli.py — run the translator from the command line on a single notice.

Usage:
    python -m src.cli sample_docs/snap_recertification.txt

It prints the plain-language version, the action items, the source citations, and
whether a human should get involved. This is the "see it work" entry point.
"""

import sys

from dotenv import load_dotenv

from .translate import translate

# Load ANTHROPIC_API_KEY from a local .env file if present (handy for non-coders).
load_dotenv()


def _print_result(result: dict) -> None:
    """Pretty-print the translation result for a human reading the terminal."""
    print("\n=== PLAIN-LANGUAGE VERSION " + "=" * 40)
    print(result.get("plain_text", "(none returned)"))

    print("\n=== WHAT YOU NEED TO DO " + "=" * 43)
    for item in result.get("action_items", []) or ["(none listed)"]:
        print(f"  • {item}")

    print("\n=== WHERE THIS COMES FROM (source quotes) " + "=" * 25)
    for quote in result.get("citations", []) or ["(none provided)"]:
        print(f"  “{quote}”")

    print("\n=== CONFIDENCE & SAFETY " + "=" * 43)
    print(f"  Confidence: {result.get('confidence', 'unknown')}")
    if result.get("escalate"):
        print("  ⚠ ESCALATE: A person should review this notice with you.")
        print(f"    Reason: {result.get('escalation_reason', '(not given)')}")
    else:
        print("  No escalation flagged.")
    print(f"\n(prompt version: {result.get('prompt_version', '?')})\n")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("Usage: python -m src.cli <path-to-notice.txt>")
        return 2

    path = argv[0]
    try:
        with open(path, "r", encoding="utf-8") as fh:
            notice_text = fh.read()
    except FileNotFoundError:
        print(f"Could not find file: {path}")
        return 1

    try:
        result = translate(notice_text)
    except (RuntimeError, ValueError) as err:
        # Expected, explainable problems (no key, bad JSON) — show the message, not a
        # scary Python traceback, since this tool is meant for non-coders.
        print(f"\n{err}")
        return 1

    _print_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
