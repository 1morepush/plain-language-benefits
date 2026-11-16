"""Tests for the "Ask about this question" chat. They use a fake Claude: no key, no cost."""

from types import SimpleNamespace

import anthropic
import httpx
import pytest

import ask
from app import app

GOOD_REPLY = "A layoff means the employer ended the job because there was no more work."


class FakeClaude:
    def __init__(self, reply=GOOD_REPLY, stop_reason="end_turn", error=None):
        self.reply, self.stop_reason, self.error = reply, stop_reason, error
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=self.reply)],
            stop_reason=self.stop_reason,
        )


@pytest.fixture
def use_claude():
    """Put a fake Claude into the app for one test, then take it out again."""

    def install(claude):
        app.config["CLAUDE_CLIENT"] = claude
        return app.test_client()

    yield install
    app.config.pop("CLAUDE_CLIENT", None)


def post(client, message="What does this mean?", question_id="placeholder_1", lang="en"):
    return client.post(
        "/api/ask", json={"message": message, "question_id": question_id, "lang": lang}
    )


def test_normal_question_gets_the_ai_reply(use_claude):
    claude = FakeClaude()
    response = post(use_claude(claude))
    assert response.get_json() == {"reply": GOOD_REPLY, "source": "ai"}


def test_request_carries_every_rule_and_only_this_question(use_claude):
    claude = FakeClaude()
    post(use_claude(claude), message="What does this mean?", lang="es")

    call = claude.calls[0]
    assert call["model"] == "claude-sonnet-5-5"
    assert "Never decide or predict eligibility" in call["system"]
    assert "Stay on this one question" in call["system"]
    sent = call["messages"][0]["content"]
    assert "fake official question text number one" in sent
    assert "number two" not in sent  # other questions are not included
    assert "<user_message>\nWhat does this mean?\n</user_message>" in sent
    assert "Reply in Spanish." in sent


def test_unreviewed_explanation_is_not_given_to_the_ai(use_claude):
    claude = FakeClaude()
    post(use_claude(claude), question_id="placeholder_3")
    assert "Unreviewed draft" not in claude.calls[0]["messages"][0]["content"]


def test_ssn_never_reaches_the_ai(use_claude):
    claude = FakeClaude()
    response = post(use_claude(claude), message="my ssn is 123-45-6789, what do I put?")
    assert response.status_code == 400
    assert response.get_json()["error"] == "ssn_blocked"
    assert claude.calls == []


def test_question_not_in_the_file_gets_a_fixed_reply_without_calling_the_ai(use_claude):
    claude = FakeClaude()
    response = post(use_claude(claude), question_id="not_a_real_question")
    assert response.get_json() == {"reply": ask.NOT_IN_FILE["en"], "source": "fixed"}
    assert claude.calls == []


@pytest.mark.parametrize(
    "bad_reply",
    [
        "Based on that, you qualify for benefits.",
        "You should say you were laid off.",
        "The best answer here is 'lack of work'.",
        "Usted califica para beneficios.",
        "Debería responder que lo despidieron.",
    ],
)
def test_flagged_reply_is_replaced_with_the_safe_message(use_claude, bad_reply):
    response = post(use_claude(FakeClaude(reply=bad_reply)))
    assert response.get_json() == {"reply": ask.SAFE_REPLY["en"], "source": "fixed"}


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_incomplete_or_declined_reply_is_replaced(use_claude, stop_reason):
    response = post(use_claude(FakeClaude(stop_reason=stop_reason)), lang="es")
    assert response.get_json() == {"reply": ask.SAFE_REPLY["es"], "source": "fixed"}


def test_empty_and_too_long_messages_are_rejected(use_claude):
    claude = FakeClaude()
    client = use_claude(claude)
    assert post(client, message="   ").status_code == 400
    assert post(client, message="x" * (ask.MAX_MESSAGE_LENGTH + 1)).status_code == 400
    assert claude.calls == []


def test_no_api_key_means_the_chat_is_switched_off(use_claude):
    client = use_claude(None)
    assert post(client).status_code == 503
    assert client.get("/api/content").get_json()["chat_enabled"] is False


def test_api_trouble_gives_a_plain_message_not_a_crash(use_claude):
    error = anthropic.APIConnectionError(request=httpx.Request("POST", "https://example.invalid"))
    response = post(use_claude(FakeClaude(error=error)))
    assert response.status_code == 503
    assert response.get_json()["message"] == ask.UNAVAILABLE["en"]


def test_reply_never_contains_the_api_key(use_claude, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-value")
    client = use_claude(FakeClaude())
    for response in (client.get("/api/content"), client.get("/"), post(client)):
        assert "test-key-value" not in response.get_data(as_text=True)
