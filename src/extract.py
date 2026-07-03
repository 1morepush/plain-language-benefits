"""
extract.py — pull plain text out of an uploaded file (.txt, .pdf, or .docx).

The GUI and CLI let people hand over the file they actually received. This module turns
that file into the plain text the translator expects. It is deliberately small and gives
friendly, specific errors (non-coders will read them). Every failure a reader library can
throw is converted to a plain-English ValueError, so the frontends only ever need to
catch one exception type.
"""

import os

# Guardrails against accidental (or hostile) resource exhaustion: parsing loads the whole
# document into memory, so refuse absurd inputs with a clear message instead of hanging.
MAX_BYTES = 20 * 1024 * 1024  # 20 MB
MAX_PDF_PAGES = 200


def _read_txt(path: str) -> str:
    # Try strict UTF-8 first so correct files can never be silently altered; fall back to
    # cp1252 (Word-style smart quotes, accents) rather than mangling characters — in a
    # tool about facts, a silently corrupted digit is worse than an error.
    raw = open(path, "rb").read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return raw.decode("cp1252")
        except UnicodeDecodeError as err:
            raise ValueError(
                "I couldn't read the characters in that text file. Try saving it "
                "again with UTF-8 encoding, or copy the text into a new .txt file."
            ) from err


def _read_pdf(path: str) -> str:
    from pypdf import PdfReader  # imported lazily so the core stays dependency-free

    reader = PdfReader(path)
    if len(reader.pages) > MAX_PDF_PAGES:
        raise ValueError(
            f"That PDF has {len(reader.pages)} pages — more than the {MAX_PDF_PAGES} this "
            "tool supports. Benefits notices are short; please upload just the notice."
        )
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(pages)


def _read_docx(path: str) -> str:
    from docx import Document  # python-docx, imported lazily

    document = Document(path)
    return "\n".join(p.text for p in document.paragraphs)


def extract_text(path: str) -> str:
    """Return the text content of a .txt/.pdf/.docx file.

    Raises ValueError with a plain-English message for unsupported types, oversized or
    corrupt/password-protected files, or when no text could be read (e.g. a scanned-image
    PDF, which would need OCR we don't do yet).
    """
    ext = os.path.splitext(path)[1].lower()
    readers = {".txt": _read_txt, ".pdf": _read_pdf, ".docx": _read_docx}
    if ext not in readers:
        raise ValueError(
            f"Sorry, '{ext or 'this file type'}' isn't supported. "
            "Please upload a .txt, .pdf, or .docx file."
        )

    if os.path.getsize(path) > MAX_BYTES:
        raise ValueError(
            f"That file is larger than {MAX_BYTES // (1024 * 1024)} MB. Benefits notices "
            "are small documents — please upload just the notice itself."
        )

    try:
        text = readers[ext](path).strip()
    except (ValueError, FileNotFoundError):
        raise  # already friendly / handled by the caller
    except Exception as err:
        # pypdf and python-docx raise their own exception types (corrupt file, password-
        # protected PDF, a renamed non-docx…). Convert them all to one friendly message.
        raise ValueError(
            f"I couldn't open that {ext} file. It may be damaged, password-protected, "
            f"or not really a {ext} file. Try re-saving or re-downloading it. "
            f"({type(err).__name__})"
        ) from err

    if not text:
        raise ValueError(
            "I couldn't read any text from that file. If it's a scanned image or photo, "
            "the text isn't selectable — try a version you can copy text from, or paste "
            "the text into a .txt file."
        )
    return text
