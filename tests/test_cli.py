"""
Offline tests for the CLI — NO API key or network required.

Covers argument parsing, the friendly-error boundary (the review found a PDF input used
to escape as a raw UnicodeDecodeError traceback), the offline --demo path, and --out.
The PDF test generates a real fixture with reportlab and stubs translate(), proving the
extract → translate wiring end-to-end without an API call.
"""

import pytest

from src.cli import _parse_args, main

CANNED = {
    "plain_text": "Your benefits end on 06/30/2026.",
    "action_items": ["Send the form by 06/20/2026"],
    "citations": ["benefits will stop on 06/30/2026"],
    "confidence": "high",
    "escalate": False,
    "disclaimer": "This is a plain-language summary, not legal advice.",
    "prompt_version": "test",
}


# --- _parse_args ----------------------------------------------------------------

def test_parse_args_positional_and_out():
    assert _parse_args(["notice.txt"]) == ("notice.txt", None)
    assert _parse_args(["notice.txt", "--out", "x.txt"]) == ("notice.txt", "x.txt")
    assert _parse_args(["--out", "x.txt", "notice.txt"]) == ("notice.txt", "x.txt")


def test_parse_args_errors():
    assert _parse_args([]) == (None, None)
    assert _parse_args(["a.txt", "b.txt"]) == (None, None)          # two positionals
    assert _parse_args(["notice.txt", "--out"]) == (None, None)     # --out with no path


# --- friendly-error boundary ------------------------------------------------------

def test_missing_file_is_friendly(capsys):
    assert main(["definitely-not-here.txt"]) == 1
    assert "Could not find file" in capsys.readouterr().out


def test_unsupported_extension_is_friendly(tmp_path, capsys):
    p = tmp_path / "notice.rtf"
    p.write_text("hello", encoding="utf-8")
    assert main([str(p)]) == 1
    out = capsys.readouterr().out
    assert "isn't supported" in out and "Traceback" not in out


def test_pdf_without_key_gets_friendly_message_not_traceback(tmp_path, capsys, monkeypatch):
    # The review's headline CLI bug: a PDF used to crash with a UnicodeDecodeError
    # traceback before ever reaching the key check. Now extract succeeds and the
    # missing key surfaces as the friendly RuntimeError message.
    pytest.importorskip("reportlab")
    pytest.importorskip("pypdf")
    from reportlab.pdfgen import canvas

    pdf = tmp_path / "notice.pdf"
    c = canvas.Canvas(str(pdf))
    c.drawString(72, 720, "Your SNAP benefits end on 06/30/2026.")
    c.save()

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert main([str(pdf)]) == 1
    out = capsys.readouterr().out
    assert "ANTHROPIC_API_KEY is not set" in out and "Traceback" not in out


def test_pdf_end_to_end_with_stubbed_translate(tmp_path, capsys, monkeypatch):
    pytest.importorskip("reportlab")
    pytest.importorskip("pypdf")
    from reportlab.pdfgen import canvas

    pdf = tmp_path / "notice.pdf"
    c = canvas.Canvas(str(pdf))
    c.drawString(72, 720, "Your SNAP benefits end on 06/30/2026.")
    c.save()

    seen = {}

    def fake_translate(notice_text):
        seen["text"] = notice_text
        return dict(CANNED)

    monkeypatch.setattr("src.cli.translate", fake_translate)
    assert main([str(pdf)]) == 0
    # extract really pulled the text out of the PDF and passed it to translate
    assert "06/30/2026" in seen["text"]
    assert "PLAIN-LANGUAGE VERSION" in capsys.readouterr().out


# --- demo + --out -----------------------------------------------------------------

def test_demo_runs_offline(capsys):
    assert main(["--demo"]) == 0
    out = capsys.readouterr().out
    assert "demo mode" in out and "PLAIN-LANGUAGE VERSION" in out


def test_demo_out_writes_readable_file(tmp_path):
    dest = tmp_path / "plain.txt"
    assert main(["--demo", "--out", str(dest)]) == 0
    body = dest.read_text(encoding="utf-8")
    assert "PLAIN-LANGUAGE VERSION" in body and "not legal advice" in body
