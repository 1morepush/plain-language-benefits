"""
Offline tests for the eval runner's fault isolation and report rendering — NO API key.

The review found that one transient API error used to crash the whole batch and discard
every completed (already paid-for) result. These tests prove a failing case becomes a
stub row while the rest of the batch completes, and that the report renders both shapes.
"""

import evals.run_evals as run_evals

GOOD_SCORE = {
    "id": "good_case",
    "prompt_version": "vtest",
    "reading_grade": 5.0,
    "coverage": {"covered": 2, "total": 2, "missing": [], "passed": True},
    "forbidden": {"checked": 1, "found": [], "passed": True},
    "citations": {"total": 3, "ungrounded": [], "passed": True},
    "escalation": {"expected": False, "actual": False, "passed": True},
    "faithfulness": {"score": 5, "passed": True, "explanation": "ok"},
    "passed": True,
}


def test_one_failing_case_does_not_lose_the_batch(monkeypatch):
    cases = [{"id": "good_case"}, {"id": "boom"}, {"id": "good_case"}]

    def fake_score_case(case, client):
        if case["id"] == "boom":
            raise RuntimeError("simulated 529 overloaded")
        return dict(GOOD_SCORE)

    monkeypatch.setattr(run_evals, "score_case", fake_score_case)
    scores: list[dict] = []
    run_evals.run_cases(cases, client=None, scores=scores)

    assert len(scores) == 3                      # nothing was discarded
    assert scores[0]["passed"] and scores[2]["passed"]
    assert scores[1]["passed"] is False
    assert "simulated 529" in scores[1]["error"]


def test_render_report_handles_error_stub_rows():
    stub = {"id": "boom", "error": "RuntimeError: simulated 529", "passed": False}
    report = run_evals.render_report([dict(GOOD_SCORE), stub])

    assert "1/2 cases passed" in report
    assert "| good_case | ✅" in report
    assert "| boom | ❌ | — | — | — | — | — | — |" in report
    assert "did not complete" in report and "simulated 529" in report
    # prompt version comes from the completed row, not the stub
    assert "vtest" in report


def test_render_report_all_good_has_no_failures_section():
    report = run_evals.render_report([dict(GOOD_SCORE)])
    assert "1/1 cases passed" in report
    assert "Failures" not in report
