"""
cli.py — run the translator from the command line on a single notice.

Usage:
    python -m src.cli notice.txt                    # translate a .txt/.pdf/.docx (needs API key)
    python -m src.cli notice.pdf --out out.txt      # also save the readable text to a file
    python -m src.cli --demo                        # show a saved example (no key)
    python -m src.cli --demo --out out.txt          # save the example to a file

It prints the plain-language version, the action items, the source citations, and
whether a human should get involved. With --out it also saves that readable text to a file.
"""

import json
import os
import sys

from dotenv import load_dotenv

from .extract import extract_text
from .translate import translate

# Load ANTHROPIC_API_KEY from a local .env file if present (handy for non-coders).
load_dotenv()

# A committed example output so anyone can see the tool's shape without an API key.
DEMO_FILE = os.path.join(os.path.dirname(__file__), "..", "examples", "snap_demo.json")


def render_text(result: dict) -> str:
    """Build the human-readable plain-language output as a single string.

    Used both to print to the screen and (with --out) to save a readable .txt file.
    """
    lines = ["=== PLAIN-LANGUAGE VERSION " + "=" * 40, result.get("plain_text", "(none returned)")]

    lines.append("\n=== WHAT YOU NEED TO DO " + "=" * 43)
    for item in result.get("action_items", []) or ["(none listed)"]:
        lines.append(f"  • {item}")

    lines.append("\n=== WHERE THIS COMES FROM (source quotes) " + "=" * 25)
    for quote in result.get("citations", []) or ["(none provided)"]:
        lines.append(f"  “{quote}”")

    lines.append("\n=== CONFIDENCE & SAFETY " + "=" * 43)
    lines.append(f"  Confidence: {result.get('confidence', 'unknown')}")
    if result.get("escalate"):
        lines.append("  ⚠ ESCALATE: A person should review this notice with you.")
        lines.append(f"    Reason: {result.get('escalation_reason', '(not given)')}")
    else:
        lines.append("  No escalation flagged.")

    if result.get("disclaimer"):
        lines.append("\n=== PLEASE NOTE " + "=" * 51)
        lines.append(f"  {result['disclaimer']}")

    lines.append(f"\n(prompt version: {result.get('prompt_version', '?')})")
    return "\n".join(lines)


def _emit(result: dict, out_path: str | None) -> None:
    """Print the result, and also write it to out_path if one was given."""
    text = render_text(result)
    print("\n" + text + "\n")
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"Saved readable output to: {out_path}\n")


def _parse_args(argv: list[str]) -> tuple[str | None, str | None]:
    """Return (source, out_path). source is the input path or '--demo'."""
    out_path = None
    positional = []
    i = 0
    while i < len(argv):
        if argv[i] == "--out":
            if i + 1 >= len(argv):
                return None, None  # --out with no path -> usage error
            out_path = argv[i + 1]
            i += 2
        else:
            positional.append(argv[i])
            i += 1
    if len(positional) != 1:
        return None, out_path
    return positional[0], out_path


def main(argv: list[str]) -> int:
    source, out_path = _parse_args(argv)
    if source is None:
        print(
            "Usage: python -m src.cli <notice.txt|.pdf|.docx> [--out file.txt]   (or: --demo)"
        )
        return 2

    if source == "--demo":
        try:
            with open(DEMO_FILE, "r", encoding="utf-8") as fh:
                result = json.load(fh)
        except (OSError, json.JSONDecodeError) as err:
            print(f"The saved demo example could not be read: {err}")
            return 1
        print("(demo mode — showing a saved example output; no API call was made)")
        _emit(result, out_path)
        return 0

    try:
        notice_text = extract_text(source)
    except FileNotFoundError:
        print(f"Could not find file: {source}")
        return 1
    except ValueError as err:
        print(f"\n{err}")
        return 1

    try:
        result = translate(notice_text)
    except Exception as err:
        # This is the user-facing boundary for non-coders: whatever went wrong (no key,
        # bad model output, a network/API error), show the message — never a traceback.
        print(f"\n{err}")
        return 1

    _emit(result, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
