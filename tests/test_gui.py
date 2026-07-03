"""
Offline tests for the GUI's logic — NO API key, network, or gradio required.

gradio is imported lazily inside build_app(), so process(), _remember_key(), and
_preview() are plain functions we can test directly. These cover the review findings:
the "Remember on this computer" feature must survive restarts (.env is loaded at import),
must not destroy other .env variables, must not be world-readable, and every failure in
process() must come back as a friendly message — never an exception.
"""

import os
import stat

import pytest

import src.gui as gui

CANNED = {
    "plain_text": "Your benefits end on 06/30/2026.",
    "action_items": ["Send the form by 06/20/2026"],
    "citations": ["benefits will stop on 06/30/2026"],
    "confidence": "high",
    "escalate": False,
    "disclaimer": "This is a plain-language summary, not legal advice.",
    "prompt_version": "test",
}


@pytest.fixture
def env_file(tmp_path, monkeypatch):
    """Point the GUI's .env at a temp file so tests never touch the real one."""
    path = tmp_path / ".env"
    monkeypatch.setattr(gui, "ENV_PATH", str(path))
    return path


# --- _remember_key ------------------------------------------------------------------

def test_remember_key_preserves_other_env_lines(env_file):
    env_file.write_text("OTHER_SETTING=keepme\nANTHROPIC_API_KEY=old\n", encoding="utf-8")
    gui._remember_key("sk-ant-new")
    body = env_file.read_text(encoding="utf-8")
    assert "OTHER_SETTING=keepme" in body
    assert "ANTHROPIC_API_KEY=sk-ant-new" in body
    assert "old" not in body


def test_remember_key_restricts_permissions(env_file):
    gui._remember_key("sk-ant-secret")
    if os.name == "posix":
        mode = stat.S_IMODE(os.stat(env_file).st_mode)
        assert mode == 0o600  # a stored secret must be owner-only


def test_gui_module_loads_env_on_import():
    # The review's broken-feature finding: the GUI wrote .env but never read it back.
    # The module must call load_dotenv at import so a remembered key works on restart.
    import inspect

    source = inspect.getsource(gui)
    assert "load_dotenv(ENV_PATH)" in source


# --- process() friendly-error boundary ------------------------------------------------

def test_process_no_file_is_friendly():
    status, preview, out = gui.process(None, "TXT", "", False)
    assert "drag in" in status.lower() and out is None


def test_process_no_key_is_friendly(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    p = tmp_path / "n.txt"
    p.write_text("Notice text.", encoding="utf-8")
    status, _, out = gui.process(str(p), "TXT", "", False)
    assert "No API key yet" in status and out is None


def test_process_end_to_end_with_stubbed_translate(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setattr(gui, "translate", lambda text: dict(CANNED))
    p = tmp_path / "notice.txt"
    p.write_text("Your benefits end on 06/30/2026.", encoding="utf-8")

    status, preview, out = gui.process(str(p), "TXT", "", False)
    assert "ready to download" in status
    assert "06/30/2026" in preview
    assert out and out.endswith("notice.plain.txt") and os.path.exists(out)


def test_process_translate_failure_is_a_message_not_an_exception(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    def boom(text):
        raise ConnectionError("network down")

    monkeypatch.setattr(gui, "translate", boom)
    p = tmp_path / "n.txt"
    p.write_text("Notice.", encoding="utf-8")
    status, _, out = gui.process(str(p), "TXT", "", False)
    assert "Something went wrong" in status and out is None


def test_process_writer_failure_keeps_the_preview(monkeypatch, tmp_path):
    # If the output file can't be produced, the translation itself must not be lost.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setattr(gui, "translate", lambda text: dict(CANNED))

    def bad_writer(result, fmt, path):
        raise RuntimeError("no disk")

    monkeypatch.setattr(gui, "write_output", bad_writer)
    p = tmp_path / "n.txt"
    p.write_text("Notice.", encoding="utf-8")
    status, preview, out = gui.process(str(p), "TXT", "", False)
    assert "couldn't create" in status and out is None
    assert "06/30/2026" in preview  # preview still delivered
