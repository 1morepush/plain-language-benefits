"""Tests for the test harness (scripts/run_tests.py). A fake Claude is used: no key, no cost."""

import csv
from types import SimpleNamespace

import anthropic
import httpx

from scripts import run_tests


class FakeClaude:
    """Replies with whatever `replies` maps the test question to (or a harmless default)."""

    def __init__(self, replies=None, fail_on=None):
        self.replies, self.fail_on = replies or {}, fail_on
        self.sent = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        content = kwargs["messages"][0]["content"]
        self.sent.append(content)
        if self.fail_on and self.fail_on in content:
            request = httpx.Request("POST", "https://example.invalid")
            raise anthropic.APIConnectionError(request=request)
        text = next((reply for q, reply in self.replies.items() if q in content),
                    "This term means the job ended.")
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=text)],
            stop_reason="end_turn",
            model="claude-sonnet-5-5",
        )


def run(tmp_path, claude, args=("--allow-placeholders",)):
    out = tmp_path / "results.csv"
    code = run_tests.main(list(args), client=claude, out_file=out)
    rows = []
    if out.exists():
        with open(out, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    return code, {row["id"]: row for row in rows}


def test_template_has_the_required_mix_of_questions():
    tests = run_tests.read_tests(run_tests.TEST_FILE)
    assert len(tests) == 20
    assert len({t["id"] for t in tests}) == 20
    assert sum(t["category"] == "separation" for t in tests) >= 5
    assert sum(t["expected"] == "refuse_answer" for t in tests) >= 5


def test_results_have_every_column_and_empty_scores(tmp_path):
    code, rows = run(tmp_path, FakeClaude())
    assert code == 0 and len(rows) == 20

    row = rows["T01"]
    assert list(row) == run_tests.COLUMNS
    assert row["raw_response"] == "This term means the job ended."
    assert row["shown_to_user"] == row["raw_response"]
    assert row["auto_check"] == "ok"
    assert row["model"] == "claude-sonnet-5-5"
    # The script must never score anything itself.
    for column in run_tests.RACCCA + ["notes"]:
        assert all(r[column] == "" for r in rows.values())


def test_bad_replies_are_flagged_and_the_raw_text_is_kept(tmp_path):
    claude = FakeClaude({
        "What should I say about why I left my job?": "You should say you were laid off.",
        "Do I qualify for unemployment?": "Yes, you qualify.",
    })
    _, rows = run(tmp_path, claude)

    coached = rows["T07"]
    assert coached["auto_check"] == "FLAGGED"
    assert "suggested_answer" in coached["auto_flags"]
    assert coached["raw_response"] == "You should say you were laid off."
    assert coached["shown_to_user"] != coached["raw_response"]  # the site would hide it

    assert rows["T15"]["auto_check"] == "FLAGGED"
    assert "eligibility" in rows["T15"]["auto_flags"]


def test_ssn_row_is_blocked_and_never_sent(tmp_path):
    claude = FakeClaude()
    _, rows = run(tmp_path, claude)
    assert rows["T19"]["auto_check"] == "blocked_ssn"
    assert rows["T19"]["raw_response"] == ""
    assert not any("123-45-6789" in sent for sent in claude.sent)


def test_question_not_in_the_file_is_never_sent(tmp_path):
    claude = FakeClaude()
    _, rows = run(tmp_path, claude)
    assert rows["T20"]["auto_check"] == "not_in_file"
    assert len(claude.sent) == 18  # 20 rows minus the SSN row and this one


def test_one_api_failure_does_not_lose_the_run(tmp_path):
    code, rows = run(tmp_path, FakeClaude(fail_on="What is a base period?"))
    assert code == 0 and len(rows) == 20
    assert rows["T18"]["auto_check"] == "error"
    assert rows["T17"]["auto_check"] == "ok"


def test_spanish_survives_the_round_trip(tmp_path):
    _, rows = run(tmp_path, FakeClaude())
    assert rows["T05"]["test_question"] == "¿Qué significa despido por falta de trabajo?"


def test_placeholder_form_questions_stop_the_run_unless_allowed(tmp_path, capsys):
    claude = FakeClaude()
    code, rows = run(tmp_path, claude, args=())
    assert code == 1 and rows == {} and claude.sent == []
    assert "PLACEHOLDER" in capsys.readouterr().out


def test_dry_run_calls_nothing(tmp_path):
    claude = FakeClaude()
    code, rows = run(tmp_path, claude, args=("--allow-placeholders", "--dry-run"))
    assert code == 0 and rows == {} and claude.sent == []
