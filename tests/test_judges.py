"""
Offline unit tests for the eval judges — NO API key or network required.

These cover the pure-Python scoring logic, including the new checks (forbidden facts,
citation grounding) and the boolean-coercion fix in escalation_correct. They also verify
the committed demo example actually passes the local checks against its source notice, so
the "no-key" demo path stays honest.

Run with:  pytest -q
"""

import json
from pathlib import Path

from evals.judges import (
    _as_bool,
    citation_grounding,
    escalation_correct,
    fact_coverage,
    forbidden_facts,
    reading_grade,
)

ROOT = Path(__file__).resolve().parent.parent


# --- _as_bool (the escalation bug fix) ---------------------------------------

def test_as_bool_handles_real_booleans():
    assert _as_bool(True) is True
    assert _as_bool(False) is False


def test_as_bool_handles_string_false():
    # The bug this guards against: bool("false") is True. We must read it as False.
    assert _as_bool("false") is False
    assert _as_bool("False") is False
    assert _as_bool("true") is True
    assert _as_bool("yes") is True


# --- reading_grade ------------------------------------------------------------

def test_reading_grade_simple_text_is_easy():
    grade = reading_grade("The cat sat. The dog ran. We had fun.")
    assert grade <= 8.0


def test_reading_grade_empty_is_flagged():
    assert reading_grade("   ") == 99.0


# --- fact_coverage ------------------------------------------------------------

def test_fact_coverage_passes_when_all_present():
    result = {"plain_text": "Send Form FA-100 by 06/20/2026.", "action_items": [], "citations": []}
    cov = fact_coverage(result, ["Form FA-100", "06/20/2026"])
    assert cov["passed"] and cov["covered"] == 2


def test_fact_coverage_fails_on_missing_deadline():
    result = {"plain_text": "Send the form soon.", "action_items": [], "citations": []}
    cov = fact_coverage(result, ["06/20/2026"])
    assert not cov["passed"] and cov["missing"] == ["06/20/2026"]


# --- forbidden_facts ----------------------------------------------------------

def test_forbidden_facts_passes_when_none_present():
    result = {"plain_text": "Your benefit is $326.00.", "action_items": [], "citations": []}
    assert forbidden_facts(result, ["$362.00"])["passed"]


def test_forbidden_facts_catches_invented_value():
    result = {"plain_text": "Your benefit is $362.00.", "action_items": [], "citations": []}
    verdict = forbidden_facts(result, ["$362.00"])
    assert not verdict["passed"] and verdict["found"] == ["$362.00"]


# --- citation_grounding -------------------------------------------------------

def test_citation_grounding_passes_for_verbatim_quote():
    source = "Your interview is scheduled for 06/16/2026 between 9:00 AM and 11:00 AM."
    result = {"citations": ["Your interview is scheduled for 06/16/2026"]}
    assert citation_grounding(result, source)["passed"]


def test_citation_grounding_fails_for_invented_quote():
    source = "Your interview is scheduled for 06/16/2026."
    result = {"citations": ["You must repay $1,304.00 immediately"]}
    verdict = citation_grounding(result, source)
    assert not verdict["passed"] and verdict["ungrounded"]


def test_citation_grounding_handles_slash_joined_fragments():
    # Models sometimes join two real source lines with " / "; each fragment is still real.
    source = "New monthly amount: $182\n  Effective date: 07/15/2026"
    result = {"citations": ["New monthly amount: $182 / Effective date: 07/15/2026"]}
    assert citation_grounding(result, source)["passed"]


def test_citation_grounding_catches_short_invented_fragment():
    # The review's false-ACCEPT: short fragments (dollar amounts!) used to be skipped.
    # A real long quote joined to an invented short amount must FAIL grounding.
    source = "Your interview is scheduled for 06/16/2026 between 9:00 AM and 11:00 AM."
    result = {"citations": ["Your interview is scheduled for 06/16/2026 / $1,840"]}
    verdict = citation_grounding(result, source)
    assert not verdict["passed"] and verdict["ungrounded"]


def test_citation_grounding_accepts_valid_short_fragments():
    # The review's false-REJECT: two real SHORT fragments joined with " / " used to be
    # re-checked as one joined string (absent from source) and wrongly rejected.
    source = "New monthly amount: $182\n  Effective date: 07/15/26"
    result = {"citations": ["$182 / 07/15/26"]}
    assert citation_grounding(result, source)["passed"]


def test_citation_grounding_rejects_empty_citation():
    assert not citation_grounding({"citations": ['""']}, "some source text")["passed"]


# --- escalation_correct -------------------------------------------------------

def test_escalation_correct_matches_label():
    assert escalation_correct({"escalate": True}, True)["passed"]
    assert escalation_correct({"escalate": False}, False)["passed"]


def test_escalation_correct_with_string_false_label():
    # Even if the model returns the STRING "false", a routine notice must score as no-escalate.
    assert escalation_correct({"escalate": "false"}, False)["passed"]


# --- real demo example passes the local checks against its source -------------

def test_demo_example_is_grounded_and_clean():
    example = json.loads((ROOT / "examples" / "snap_demo.json").read_text(encoding="utf-8"))
    source = (ROOT / "sample_docs" / "snap_recertification.txt").read_text(encoding="utf-8")

    # Every citation is a real quote from the source.
    assert citation_grounding(example, source)["passed"]
    # No invented facts from the SNAP golden case.
    assert forbidden_facts(example, ["06/25/2026", "60 days"])["passed"]
    # Required SNAP facts all survive, and it reads easily.
    snap_facts = ["06/20/2026", "06/30/2026", "Form FA-100", "06/16/2026"]
    assert fact_coverage(example, snap_facts)["passed"]
    assert reading_grade(example["plain_text"]) <= 8.0
    # The safety disclaimer is attached.
    assert example.get("disclaimer")
