"""
Offline tests for translate()'s response handling — NO API key or network required.

A fake client stands in for the Anthropic API so we can prove the guards added after the
production-readiness review: an empty response, a non-object JSON reply, and a string
"false" escalate flag must all be handled safely instead of crashing or mis-reading.
"""

from types import SimpleNamespace

import pytest

from src.translate import DISCLAIMER, PROMPT_VERSION, _as_bool, translate


class FakeClient:
    """Mimics anthropic.Anthropic just enough for translate(): .messages.create(...)."""

    def __init__(self, reply_text=None, content=None):
        if content is None:
            content = [SimpleNamespace(type="text", text=reply_text)]
        self._response = SimpleNamespace(content=content)
        self.messages = SimpleNamespace(create=lambda **kwargs: self._response)


def test_happy_path_attaches_version_disclaimer_and_bool_escalate():
    client = FakeClient('{"plain_text": "Hi.", "escalate": true}')
    result = translate("notice", client=client)
    assert result["plain_text"] == "Hi."
    assert result["escalate"] is True
    assert result["prompt_version"] == PROMPT_VERSION
    assert result["disclaimer"] == DISCLAIMER


def test_string_false_escalate_is_normalized_to_real_false():
    # The bug this guards: bool("false") is True. A routine notice must not escalate.
    client = FakeClient('{"plain_text": "Hi.", "escalate": "false"}')
    assert translate("notice", client=client)["escalate"] is False


def test_valid_json_that_is_not_an_object_raises_valueerror():
    # A bare list is valid JSON but not a result object — must be a clear error,
    # not a TypeError leaking through the CLI/GUI boundaries.
    client = FakeClient('[{"plain_text": "Hi."}]')
    with pytest.raises(ValueError, match="not a result object"):
        translate("notice", client=client)


def test_empty_content_raises_valueerror():
    client = FakeClient(content=[])
    with pytest.raises(ValueError, match="empty response"):
        translate("notice", client=client)


def test_non_text_blocks_only_raises_valueerror():
    client = FakeClient(content=[SimpleNamespace(type="thinking", text="hmm")])
    with pytest.raises(ValueError, match="empty response"):
        translate("notice", client=client)


def test_as_bool_shared_helper():
    assert _as_bool("true") is True
    assert _as_bool("False") is False
    assert _as_bool(None) is False
