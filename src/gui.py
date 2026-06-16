"""
gui.py — a friendly drag-and-drop web app for the Plain Language translator.

For people who don't use a terminal. Launch it with `python -m src.gui` (or the
run_gui scripts). It opens in the browser: paste your API key once, drag in a benefits
notice (.pdf/.docx/.txt), pick an output format, and download the plain-language version.

The heavy lifting is unchanged — this only wires the existing translate()/extract/output
pieces to a UI. Built with Gradio so drag-drop upload and file download come for free.
"""

import os
import tempfile

from .extract import extract_text
from .output import resolve_format, write_output
from .translate import translate

OUTPUT_CHOICES = ["Same as input", "TXT", "DOCX", "PDF"]
ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")


def _remember_key(api_key: str) -> None:
    """Save the key to the git-ignored .env so the user doesn't re-paste it next time."""
    with open(ENV_PATH, "w", encoding="utf-8") as fh:
        fh.write(f"ANTHROPIC_API_KEY={api_key.strip()}\n")


def _preview(result: dict) -> str:
    """A short, readable on-screen summary of the result."""
    lines = [result.get("plain_text", ""), "", "WHAT YOU NEED TO DO:"]
    lines += [f"• {a}" for a in result.get("action_items", []) or ["(none listed)"]]
    if result.get("escalate"):
        lines += ["", "⚠ SEE A PERSON: " + result.get("escalation_reason", "")]
    else:
        lines += ["", "No escalation flagged."]
    lines += ["", result.get("disclaimer", "")]
    return "\n".join(lines)


def process(file_path, output_choice, api_key, remember):
    """Run one notice end to end. Returns (status_message, preview_text, output_file_path)."""
    if not file_path:
        return "Please drag in a .pdf, .docx, or .txt file first.", "", None

    key = (api_key or "").strip()
    if key:
        os.environ["ANTHROPIC_API_KEY"] = key
        if remember:
            _remember_key(key)
    if not os.getenv("ANTHROPIC_API_KEY"):
        return ("No API key yet. Paste your Anthropic API key in the box above "
                "(get one at console.anthropic.com)."), "", None

    try:
        notice_text = extract_text(file_path)
    except ValueError as err:
        return str(err), "", None

    try:
        result = translate(notice_text)
    except (RuntimeError, ValueError) as err:
        return f"Something went wrong: {err}", "", None

    fmt = resolve_format(output_choice, file_path)
    base = os.path.splitext(os.path.basename(file_path))[0]
    out_path = os.path.join(tempfile.mkdtemp(), f"{base}.plain.{fmt}")
    write_output(result, fmt, out_path)

    flag = "⚠ This notice should be reviewed by a person." if result.get("escalate") else "✓ Done."
    return f"{flag} Your {fmt.upper()} is ready to download below.", _preview(result), out_path


def build_app():
    """Construct the Gradio interface (kept in a function so tests can import without launching)."""
    import gradio as gr

    with gr.Blocks(title="Plain Language — Benefits Notice Translator") as app:
        gr.Markdown(
            "# Plain Language\n"
            "Turn a confusing benefits notice into clear, plain language. "
            "Drag in your letter, and download an easy-to-read version.\n\n"
            "*This is a plain-language summary, not legal advice.*"
        )
        with gr.Row():
            api_key = gr.Textbox(
                label="Your Anthropic API key", type="password",
                placeholder="sk-ant-...  (get one at console.anthropic.com)",
            )
            remember = gr.Checkbox(label="Remember on this computer", value=False)
        with gr.Row():
            file_in = gr.File(label="Drag your notice here (.pdf, .docx, .txt)",
                              file_types=[".pdf", ".docx", ".txt"], type="filepath")
            output_choice = gr.Dropdown(OUTPUT_CHOICES, value="Same as input",
                                        label="Output file format")
        go = gr.Button("Translate my notice", variant="primary")
        status = gr.Markdown()
        preview = gr.Textbox(label="Preview", lines=12)
        file_out = gr.File(label="Download your plain-language version")

        go.click(process, inputs=[file_in, output_choice, api_key, remember],
                 outputs=[status, preview, file_out])
    return app


def main() -> None:
    build_app().launch(inbrowser=True)


if __name__ == "__main__":
    main()
