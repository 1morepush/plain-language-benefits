"""
app.py — the Plain Path web server (Flask).

Run it with:   python app.py      then open http://127.0.0.1:5000

What the server does:
  GET  /             the single web page (static/index.html)
  GET  /api/content  the questions, intake, checklist, and help links as JSON
  POST /api/ask      the "Ask about this question" chat (one message in, one reply out)

Safety jobs done here:
  * Every incoming request is checked for SSN-shaped text and rejected if found.
  * Unreviewed explanations are filtered out in content.py before they leave the server.
  * The server never stores or logs what a user sends.
"""

import os

import anthropic
from flask import Flask, jsonify, request

import ask
from content import build_content
from ssn_guard import WARNING_EN, WARNING_ES, looks_like_ssn

app = Flask(__name__, static_folder="static", static_url_path="/static")

# Nobody needs to send this app more than a short message. Reject anything bigger.
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # 16 KB


@app.before_request
def block_ssn():
    """Stop any request that carries something shaped like an SSN.

    This runs before every route, so a future route cannot forget the check.
    The text is checked in memory only. It is never saved or printed.
    """
    body = request.get_data(as_text=True)
    query = request.query_string.decode("utf-8", errors="replace")
    if looks_like_ssn(body) or looks_like_ssn(query):
        return (
            jsonify({"error": "ssn_blocked", "message_en": WARNING_EN, "message_es": WARNING_ES}),
            400,
        )
    return None


@app.after_request
def add_security_headers(response):
    """Tell the browser to load scripts and styles only from this site."""
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/content")
def api_content():
    content = build_content()
    # The page only shows the "Ask about this question" box when the chat can work.
    content["chat_enabled"] = get_claude() is not None
    response = jsonify(content)
    # Always fetch fresh data, so a newly reviewed explanation shows up right away.
    response.headers["Cache-Control"] = "no-store"
    return response


def get_claude():
    """Return the Claude client, or None if no API key is set.

    The key is read from the ANTHROPIC_API_KEY environment variable and stays on the
    server. It is never sent to the browser. (Tests put a fake client in app.config.)
    """
    if "CLAUDE_CLIENT" not in app.config:
        has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
        # Give up after 30 seconds so a person is never left waiting for long.
        client = anthropic.Anthropic(timeout=30.0, max_retries=1) if has_key else None
        app.config["CLAUDE_CLIENT"] = client
    return app.config["CLAUDE_CLIENT"]


@app.post("/api/ask")
def api_ask():
    """Answer one follow-up message about one question. Nothing is stored or logged."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}
    lang = "es" if data.get("lang") == "es" else "en"
    message = str(data.get("message") or "").strip()

    if not message:
        return jsonify({"error": "empty", "message": ask.EMPTY_MESSAGE[lang]}), 400
    if len(message) > ask.MAX_MESSAGE_LENGTH:
        return jsonify({"error": "too_long", "message": ask.TOO_LONG[lang]}), 400

    # Only questions from the data file can be discussed. Anything else gets a fixed
    # reply and never reaches the AI.
    questions = {q["id"]: q for q in build_content()["questions"]}
    question = questions.get(data.get("question_id"))
    if question is None:
        return jsonify({"reply": ask.NOT_IN_FILE[lang], "source": "fixed"})

    client = get_claude()
    if client is None:
        return jsonify({"error": "unavailable", "message": ask.UNAVAILABLE[lang]}), 503

    try:
        return jsonify(ask.answer(client, question, message, lang))
    except anthropic.APIError:
        # Covers a bad key, a timeout, rate limits, and network trouble.
        return jsonify({"error": "unavailable", "message": ask.UNAVAILABLE[lang]}), 503


if __name__ == "__main__":
    # 127.0.0.1 = only this computer can reach the site. debug stays off on purpose.
    app.run(host="127.0.0.1", port=5000, debug=False)
