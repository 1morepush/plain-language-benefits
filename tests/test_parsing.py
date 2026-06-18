"""
Offline tests for the JSON extractor in src/translate.py — no API key needed.

Models usually return bare JSON, but sometimes add a ```json fence or a sentence of
preamble. The extractor must recover the JSON object either way so one chatty reply
can't crash a whole eval batch.
"""

import json

from src.translate import _extract_json

OBJ = '{"escalate": true, "confidence": "low"}'


def test_plain_json_passes_through():
    assert json.loads(_extract_json(OBJ))["escalate"] is True


def test_fenced_json():
    assert json.loads(_extract_json(f"```json\n{OBJ}\n```"))["confidence"] == "low"


def test_preamble_before_json():
    # The exact shape that crashed the live batch: a sentence, then a fenced object.
    raw = f"Escalation is required.\n\n```json\n{OBJ}\n```"
    assert json.loads(_extract_json(raw))["escalate"] is True


def test_trailing_text_after_json():
    assert json.loads(_extract_json(f"{OBJ}\n\nLet me know if you need anything else."))
