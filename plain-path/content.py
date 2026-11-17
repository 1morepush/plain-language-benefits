"""
content.py — loads the data files and decides what the website is allowed to show.

The most important job here is REVIEW GATING: an AI-drafted explanation is only sent
to the browser if a person has marked it as reviewed. English and Spanish are approved
separately ("reviewed_en" / "reviewed_es"), so an unchecked Spanish draft can never
ride along with a checked English one.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
LANGUAGES = ("en", "es")


def load_json(name: str, data_dir: Path | None = None):
    """Read one JSON data file (always as UTF-8, so Spanish accents are safe)."""
    with open((data_dir or DATA_DIR) / name, encoding="utf-8") as f:
        return json.load(f)


def gated_explanation(entry: dict | None, lang: str, official_text: str | None = None):
    """Return the explanation for one language, or None if it must stay hidden.

    Hidden when:
      * it is not reviewed. Only the exact value `true` counts, not "yes" or 1.
      * the official wording has changed since the explanation was written. A review
        of the old wording says nothing about the new wording.
    """
    if not entry or entry.get(f"reviewed_{lang}") is not True:
        return None
    if entry.get("written_for") not in (None, official_text):
        return None
    return {
        "text": entry.get(f"explanation_{lang}", ""),
        "you_will_need": entry.get(f"you_will_need_{lang}", []),
        "check_reason": entry.get(f"check_with_person_reason_{lang}", ""),
    }


def build_content(data_dir: Path | None = None) -> dict:
    """Bundle everything the page needs into one object.

    The files are re-read on every request. They are tiny, and it means an edit to
    a data file shows up on the next page refresh without restarting the server.
    """
    explanations = load_json("explanations.json", data_dir)

    questions = []
    for q in load_json("questions.json", data_dir):
        entry = explanations.get(q["id"])
        questions.append(
            {
                "id": q["id"],
                "section": q["section"],
                "official_text_en": q["official_text_en"],
                # Optional: null means "no official Spanish wording available".
                "official_text_es": q.get("official_text_es") or None,
                "source": q.get("source", ""),
                "high_risk": q.get("high_risk") is True,
                "explanation": {
                    lang: gated_explanation(entry, lang, q["official_text_en"])
                    for lang in LANGUAGES
                },
            }
        )

    return {
        "intake": load_json("intake.json", data_dir),
        "sections": load_json("sections.json", data_dir),
        "questions": questions,
        "checklist": load_json("checklist.json", data_dir),
        "help": load_json("help_links.json", data_dir),
    }
