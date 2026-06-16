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
