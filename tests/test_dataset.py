"""
Offline integrity tests for the golden dataset — NO API key or network required.

These don't run the model; they check that each golden case is well-formed and honest:
  - the referenced source notice exists,
  - every `must_include_fact` really appears in that source (so the test isn't checking for
    something the notice never said),
  - every `forbidden_fact` is genuinely ABSENT from the source (so it's real hallucination
    bait, not a word the notice already contains),
  - `expected_escalate` is a boolean.

This catches dataset authoring mistakes (typos, a "forbidden" phrase that's actually in the
source) the moment they're introduced. Runs in CI.
"""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "evals" / "dataset.jsonl"


def _load_cases():
    cases = []
    for line in DATASET.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


CASES = _load_cases()
CASE_IDS = [c["id"] for c in CASES]


def test_dataset_is_nonempty():
    assert len(CASES) >= 4


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
def test_case_is_well_formed(case):
    source_path = ROOT / case["doc"]
    assert source_path.exists(), f"missing source doc: {case['doc']}"
    source = source_path.read_text(encoding="utf-8").lower()

    # Every required fact must actually be in the source notice.
    for fact in case["must_include_facts"]:
        assert fact.lower() in source, f"{case['id']}: required fact not in source: {fact!r}"

    # Every forbidden fact must NOT be in the source (otherwise it isn't hallucination bait).
    for bad in case.get("forbidden_facts", []):
        assert bad.lower() not in source, f"{case['id']}: forbidden fact is in source: {bad!r}"

    assert isinstance(case["expected_escalate"], bool), f"{case['id']}: escalate not a bool"
