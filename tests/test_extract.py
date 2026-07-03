"""
Offline tests for file text extraction — no API key needed.

.txt and the error paths run everywhere; the .docx test skips if python-docx isn't installed.
"""

import pytest

from src.extract import extract_text


def test_extract_txt(tmp_path):
    p = tmp_path / "notice.txt"
    p.write_text("Your SNAP benefits end on 06/30/2026.", encoding="utf-8")
    assert "SNAP benefits" in extract_text(str(p))


def test_unsupported_type_raises(tmp_path):
    p = tmp_path / "notice.rtf"
    p.write_text("hello", encoding="utf-8")
    with pytest.raises(ValueError, match="supported"):
        extract_text(str(p))


def test_empty_file_raises(tmp_path):
    p = tmp_path / "blank.txt"
    p.write_text("   \n", encoding="utf-8")
    with pytest.raises(ValueError, match="couldn't read any text"):
        extract_text(str(p))


def test_extract_docx(tmp_path):
    docx = pytest.importorskip("docx")  # python-docx
    path = tmp_path / "notice.docx"
    document = docx.Document()
    document.add_paragraph("Your interview is scheduled for 06/16/2026.")
    document.save(str(path))
    assert "06/16/2026" in extract_text(str(path))


def test_extract_pdf(tmp_path):
    # A real PDF fixture, generated on the fly — the review flagged this path as untested.
    pytest.importorskip("reportlab")
    pytest.importorskip("pypdf")
    from reportlab.pdfgen import canvas

    path = tmp_path / "notice.pdf"
    c = canvas.Canvas(str(path))
    c.drawString(72, 720, "Your SNAP benefits end on 06/30/2026.")
    c.save()
    assert "06/30/2026" in extract_text(str(path))


def test_corrupt_pdf_gets_friendly_error(tmp_path):
    # pypdf raises its own exception types; they must surface as a plain-English
    # ValueError, not escape as a raw library error (review finding).
    pytest.importorskip("pypdf")
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"this is not a pdf at all")
    with pytest.raises(ValueError, match="damaged, password-protected"):
        extract_text(str(path))


def test_renamed_nondocx_gets_friendly_error(tmp_path):
    pytest.importorskip("docx")
    path = tmp_path / "fake.docx"
    path.write_text("just text pretending to be docx", encoding="utf-8")
    with pytest.raises(ValueError, match="damaged, password-protected"):
        extract_text(str(path))


def test_cp1252_text_decodes_instead_of_mangling(tmp_path):
    # A Windows-encoded notice (smart quotes / accents) must decode correctly, not be
    # silently replaced with � characters (integrity matters in a facts-critical app).
    path = tmp_path / "windows.txt"
    path.write_bytes("Renewal deadline: July 15 — café’s notice".encode("cp1252"))
    text = extract_text(str(path))
    assert "café’s" in text and "�" not in text


def test_oversize_file_is_refused(tmp_path, monkeypatch):
    import src.extract as extract_mod

    monkeypatch.setattr(extract_mod, "MAX_BYTES", 10)  # tiny cap for the test
    path = tmp_path / "big.txt"
    path.write_text("x" * 100, encoding="utf-8")
    with pytest.raises(ValueError, match="larger than"):
        extract_text(str(path))
