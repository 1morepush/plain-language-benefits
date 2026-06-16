"""
extract.py — pull plain text out of an uploaded file (.txt, .pdf, or .docx).

The GUI lets people drag in the file they actually received. This module turns that
file into the plain text the translator expects. It is deliberately small and gives
friendly, specific errors (non-coders will read them).
"""

import os


def _read_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _read_pdf(path: str) -> str:
    from pypdf import PdfReader  # imported lazily so the core stays dependency-free

    reader = PdfReader(path)
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(pages)


def _read_docx(path: str) -> str:
    from docx import Document  # python-docx, imported lazily

    document = Document(path)
    return "\n".join(p.text for p in document.paragraphs)


def extract_text(path: str) -> str:
    """Return the text content of a .txt/.pdf/.docx file.

    Raises ValueError with a plain-English message for unsupported types or when no
    text could be read (e.g. a scanned-image PDF, which would need OCR we don't do yet).
    """
    ext = os.path.splitext(path)[1].lower()
    readers = {".txt": _read_txt, ".pdf": _read_pdf, ".docx": _read_docx}
    if ext not in readers:
        raise ValueError(
            f"Sorry, '{ext or 'this file type'}' isn't supported. "
            "Please upload a .txt, .pdf, or .docx file."
        )

    text = readers[ext](path).strip()
    if not text:
        raise ValueError(
            "I couldn't read any text from that file. If it's a scanned image or photo, "
            "the text isn't selectable — try a version you can copy text from, or paste "
            "the text into a .txt file."
        )
    return text
