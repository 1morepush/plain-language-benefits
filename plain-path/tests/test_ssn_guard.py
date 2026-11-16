"""Unit tests for the SSN blocker (ssn_guard.py), its browser copy, and the server hook."""

from pathlib import Path

import pytest

from app import app
from ssn_guard import SSN_PATTERN, looks_like_ssn

STATIC = Path(__file__).parent.parent / "static"


@pytest.mark.parametrize(
    "text",
    [
        "123-45-6789",
        "my ssn is 123-45-6789 ok",
        "123456789",
        "SSN:123456789.",
        "123 45 6789",
        "123.45.6789",
        "123–45–6789",  # long dashes, which phones sometimes type automatically
        "mi número es 123-45-6789",
    ],
)
def test_blocks_ssn_shapes(text):
    assert looks_like_ssn(text)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "What does 'laid off' mean?",
        "I worked there for 18 months",
        "call 602-555-0100",  # phone number: 3-3-4, not 3-2-4
        "6025550100",  # 10 digits in a row is a phone number, not an SSN
        "1234567890123",  # part of a longer number
        "form UB-105, page 12",
        "in 2024 I earned 12345 dollars",
    ],
)
def test_allows_ordinary_text(text):
    assert not looks_like_ssn(text)


def test_browser_copy_uses_the_same_pattern():
    """The browser warning and the server block must agree on what an SSN looks like."""
    js = (STATIC / "ssn_guard.js").read_text(encoding="utf-8")
    assert SSN_PATTERN in js


def test_server_blocks_ssn_in_a_request_body():
    client = app.test_client()
    response = client.post("/api/ask", json={"message": "my number is 123-45-6789"})
    assert response.status_code == 400
    assert response.get_json()["error"] == "ssn_blocked"
    # The warning must never repeat the number back.
    assert "123" not in response.get_data(as_text=True)


def test_server_blocks_ssn_in_the_address_bar():
    client = app.test_client()
    assert client.get("/api/content?q=123456789").status_code == 400


def test_server_lets_ordinary_requests_through():
    client = app.test_client()
    assert client.post("/api/ask", json={"message": "what is severance?"}).status_code == 501
    assert client.get("/api/content").status_code == 200
