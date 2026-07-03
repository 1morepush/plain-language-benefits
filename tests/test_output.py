"""
Offline tests for the output writers and format resolution — no API key needed.

TXT and resolve_format run everywhere; the DOCX/PDF tests skip if their libraries
aren't installed.
"""

import pytest

from src.output import resolve_format, write_output

SAMPLE = {
    "plain_text": "Your SNAP benefits end on 06/30/2026. Send Form FA-100 by 06/20/2026.",
    "action_items": ["Send Form FA-100 by 06/20/2026"],
    "citations": ["your SNAP benefits will stop on 06/30/2026"],
    "confidence": "high",
    "escalate": False,
    "disclaimer": "This is a plain-language summary, not legal advice.",
}


def test_resolve_format_explicit_and_same_as_input():
    assert resolve_format("PDF", "x.txt") == "pdf"
    assert resolve_format("Same as input", "notice.docx") == "docx"
    assert resolve_format("Same as input", "notice.pdf") == "pdf"
    # An input we can't write back to (or unknown choice) falls back to txt.
    assert resolve_format("Same as input", "notice.rtf") == "txt"
    assert resolve_format("nonsense", "notice.txt") == "txt"


def test_write_txt(tmp_path):
    out = tmp_path / "out.txt"
    write_output(SAMPLE, "txt", str(out))
    body = out.read_text(encoding="utf-8")
    assert "06/30/2026" in body and "not legal advice" in body


def test_write_docx(tmp_path):
    pytest.importorskip("docx")
    out = tmp_path / "out.docx"
    write_output(SAMPLE, "docx", str(out))
    assert out.exists() and out.stat().st_size > 0


def test_write_pdf(tmp_path):
    pytest.importorskip("reportlab")
    out = tmp_path / "out.pdf"
    write_output(SAMPLE, "pdf", str(out))
    assert out.exists() and out.stat().st_size > 0


# Real notices contain & / < / >, and a malicious one could carry reportlab markup like
# <img src=...> (SSRF/local-file read). The review found the PDF writer passed this text
# to reportlab unescaped; every writer must handle it safely.
HOSTILE = {
    "plain_text": 'Aid & Attendance: income < $2,000 and rent > $500.\n<img src="http://evil/x.png"/>',
    "action_items": ["Reply if income < $2,000 & rent > $500"],
    "citations": ['<img src="/etc/passwd"/> & other markup'],
    "confidence": "high",
    "escalate": False,
    "disclaimer": "This is a plain-language summary, not legal advice.",
}


def test_write_txt_with_markup_characters(tmp_path):
    out = tmp_path / "hostile.txt"
    write_output(HOSTILE, "txt", str(out))
    assert "Aid & Attendance" in out.read_text(encoding="utf-8")


def test_write_docx_with_markup_characters(tmp_path):
    pytest.importorskip("docx")
    out = tmp_path / "hostile.docx"
    write_output(HOSTILE, "docx", str(out))
    assert out.stat().st_size > 0


def test_write_pdf_with_markup_characters_does_not_crash_or_interpret(tmp_path):
    # Before the fix this raised inside reportlab's markup parser; a crafted <img> tag
    # could even trigger a network fetch or local-file open during build().
    pytest.importorskip("reportlab")
    out = tmp_path / "hostile.pdf"
    write_output(HOSTILE, "pdf", str(out))
    assert out.exists() and out.stat().st_size > 0
