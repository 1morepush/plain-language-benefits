"""
app.py — the Plain Path web server (Flask).

Run it with:   python app.py      then open http://127.0.0.1:5000

What the server does:
  GET  /             the single web page (static/index.html)
  GET  /api/content  the questions, intake, checklist, and help links as JSON
  POST /api/ask      placeholder for the stage 3 "Ask about this question" chat

Safety jobs done here:
  * Every incoming request is checked for SSN-shaped text and rejected if found.
  * Unreviewed explanations are filtered out in content.py before they leave the server.
  * The server never stores or logs what a user sends.
"""

from flask import Flask, jsonify, request

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
    response = jsonify(build_content())
    # Always fetch fresh data, so a newly reviewed explanation shows up right away.
    response.headers["Cache-Control"] = "no-store"
    return response


@app.post("/api/ask")
def api_ask():
    """The follow-up chat arrives in stage 3. Until then this only proves the SSN block."""
    return jsonify({"error": "not_available", "message_en": "Coming in stage 3."}), 501


if __name__ == "__main__":
    # 127.0.0.1 = only this computer can reach the site. debug stays off on purpose.
    app.run(host="127.0.0.1", port=5000, debug=False)
