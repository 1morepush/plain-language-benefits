"""Tests for the explanation generator. They use a fake Claude, so no API key is needed."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import generate_explanations as gen

GOOD_REPLY = {
    "explanation_en": "This asks about your last job.",
    "explanation_es": "Esto pregunta sobre su último trabajo.",
    "you_will_need_en": ["Your last pay stub"],
    "you_will_need_es": ["Su último talón de pago"],
    "check_with_person_reason_en": "",
    "check_with_person_reason_es": "",
}


class FakeClaude:
    """Stands in for the Anthropic client. Records what it was sent."""

    def __init__(self, reply_text=None, stop_reason="end_turn"):
        self.reply_text = json.dumps(GOOD_REPLY) if reply_text is None else reply_text
        self.stop_reason = stop_reason
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=self.reply_text)],
            stop_reason=self.stop_reason,
            model="claude-sonnet-5-5",
        )


def make_data(tmp_path, questions, explanations=None):
    (tmp_path / "questions.json").write_text(json.dumps(questions), encoding="utf-8")
    (tmp_path / "explanations.json").write_text(json.dumps(explanations or {}), encoding="utf-8")
    return tmp_path


def read_explanations(data_dir):
    return json.loads((data_dir / "explanations.json").read_text(encoding="utf-8"))


def question(qid="q1", text="Why did you leave your last job?", high_risk=False):
    return {"id": qid, "section": "s", "official_text_en": text, "source": "x",
            "high_risk": high_risk}


def test_new_draft_is_saved_unreviewed(tmp_path):
    data = make_data(tmp_path, [question()])
    claude = FakeClaude()
    assert gen.main([], client=claude, data_dir=data) == 0

    entry = read_explanations(data)["q1"]
    assert entry["reviewed_en"] is False and entry["reviewed_es"] is False
    assert entry["explanation_es"] == GOOD_REPLY["explanation_es"]  # accents survive
    assert entry["written_for"] == "Why did you leave your last job?"
    assert entry["drafted_by"] == "claude-sonnet-5-5"


def test_request_uses_the_system_prompt_file_and_the_right_model(tmp_path):
    data = make_data(tmp_path, [question()])
    claude = FakeClaude()
    gen.main([], client=claude, data_dir=data)

    call = claude.calls[0]
    assert call["model"] == "claude-sonnet-5-5"
    assert call["system"] == gen.SYSTEM_PROMPT_FILE.read_text(encoding="utf-8")
    assert "Why did you leave your last job?" in call["messages"][0]["content"]


def test_reviewed_explanation_is_never_replaced(tmp_path):
    reviewed = {"q1": {"explanation_en": "Checked by a person.", "reviewed_en": True}}
    data = make_data(tmp_path, [question()], reviewed)
    claude = FakeClaude()
    gen.main(["--redo"], client=claude, data_dir=data)

    assert claude.calls == []
    assert read_explanations(data) == reviewed


def test_reviewed_explanation_is_redrafted_when_the_wording_changed(tmp_path):
    old = {"q1": {"explanation_en": "Old.", "reviewed_en": True, "written_for": "Old wording?"}}
    data = make_data(tmp_path, [question(text="New wording?")], old)
    gen.main([], client=FakeClaude(), data_dir=data)

    entry = read_explanations(data)["q1"]
    assert entry["reviewed_en"] is False
    assert entry["written_for"] == "New wording?"


def test_waiting_draft_is_left_alone_unless_redo(tmp_path):
    waiting = {"q1": {"explanation_en": "Draft.", "reviewed_en": False, "reviewed_es": False}}
    data = make_data(tmp_path, [question()], waiting)

    claude = FakeClaude()
    gen.main([], client=claude, data_dir=data)
    assert claude.calls == []

    gen.main(["--redo"], client=claude, data_dir=data)
    assert len(claude.calls) == 1


def test_placeholder_questions_are_never_sent(tmp_path):
    data = make_data(tmp_path, [question(text="PLACEHOLDER: fake question")])
    claude = FakeClaude()
    gen.main([], client=claude, data_dir=data)
    assert claude.calls == []


def test_dry_run_calls_nothing(tmp_path):
    data = make_data(tmp_path, [question()])
    claude = FakeClaude()
    assert gen.main(["--dry-run"], client=claude, data_dir=data) == 0
    assert claude.calls == [] and read_explanations(data) == {}


@pytest.mark.parametrize(
    "claude",
    [
        FakeClaude(stop_reason="refusal"),
        FakeClaude(stop_reason="max_tokens"),
        FakeClaude(reply_text="not json"),
        FakeClaude(reply_text=json.dumps({"explanation_en": "only one field"})),
        FakeClaude(reply_text=json.dumps({**GOOD_REPLY, "explanation_es": "  "})),
    ],
)
def test_bad_reply_is_reported_and_nothing_is_saved(tmp_path, claude):
    data = make_data(tmp_path, [question()])
    assert gen.main([], client=claude, data_dir=data) == 1
    assert read_explanations(data) == {}


def test_one_failure_does_not_stop_the_others(tmp_path):
    data = make_data(tmp_path, [question("q1"), question("q2")])
    claude = FakeClaude()
    replies = iter(["not json", json.dumps(GOOD_REPLY)])
    original = claude._create

    def flaky(**kwargs):
        claude.reply_text = next(replies)
        return original(**kwargs)

    claude.beta.messages.create = flaky
    assert gen.main([], client=claude, data_dir=data) == 1
    assert list(read_explanations(data)) == ["q2"]


def test_missing_key_is_explained(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    data = make_data(tmp_path, [question()])
    assert gen.main([], data_dir=data) == 1
    assert "ANTHROPIC_API_KEY is not set" in capsys.readouterr().out


def test_no_key_is_written_in_the_code():
    for path in Path(gen.__file__).parent.parent.rglob("*"):
        if path.suffix in {".py", ".js", ".html", ".md", ".json"} and ".venv" not in path.parts:
            # Real keys start with these letters. (Split so this file does not match.)
            assert "sk-" + "ant-" not in path.read_text(encoding="utf-8"), path


def test_system_prompt_contains_every_hard_rule():
    prompt = gen.SYSTEM_PROMPT_FILE.read_text(encoding="utf-8").lower()
    for phrase in [
        "never answer it",                       # no suggested answers
        "never decide or predict eligibility",
        "never fill out, submit, or connect",
        "no personal data",
        "never make up form content",
        "not legal advice",
    ]:
        assert phrase in prompt, phrase
