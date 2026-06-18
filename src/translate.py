"""
translate.py — the core function that turns a dense benefits notice into plain language.

This is deliberately small. It does three things:
  1. Sends the notice to Claude with the rules from prompts.py.
  2. Parses the JSON response into a normal Python dictionary.
  3. Returns that dictionary so the CLI and the eval harness can both reuse it.

A non-coder only needs to understand the function `translate()` near the bottom.
"""

import json
import os

from anthropic import Anthropic

from .prompts import PROMPT_VERSION, SYSTEM_PROMPT, build_user_message

# --- Configuration you might change (all in one spot) -------------------------
# Accuracy matters more than cost for benefits notices, so we default to a capable
# model. To cut cost, swap to "claude-haiku-4-5" — see docs/RUNBOOK.md.
TRANSLATOR_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1500

# Attached to every result so the reader is never misled about what this is. We set it
# in code (not via the model) so it is always present and always worded the same way.
DISCLAIMER = (
    "This is a plain-language summary to help you understand your notice. "
    "It is not legal advice and does not change the official notice. "
    "When in doubt, contact your caseworker or a local legal aid office."
)


def _extract_json(text: str) -> str:
    """Pull the JSON object out of a model response.

    The prompt asks for bare JSON, but models sometimes wrap it in a ```json fence or add a
    sentence of preamble ("Escalation is required.") before it. Rather than crash the whole
    batch on one chatty reply, we strip fences and, if needed, slice from the first '{' to
    the last '}'. Defense in depth around an instruction the model usually — but not always —
    follows.
    """
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text  # drop ``` / ```json line
        if text.rstrip().endswith("```"):
            text = text.rstrip()[: -len("```")]
        text = text.strip()
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        return text[start : end + 1] if start != -1 and end > start else text


def translate(notice_text: str, client: Anthropic | None = None) -> dict:
    """Translate one benefits notice into plain language.

    Returns a dictionary with these keys:
      plain_text, action_items, citations, confidence, escalate,
      escalation_reason, and prompt_version (added so reports are reproducible).

    Raises a clear error if the API key is missing so the user knows what to fix.
    """
    if client is None:
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your "
                "key, or run `export ANTHROPIC_API_KEY=...`. See docs/RUNBOOK.md."
            )
        client = Anthropic()

    response = client.messages.create(
        model=TRANSLATOR_MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_message(notice_text)}],
    )

    raw = _extract_json(response.content[0].text)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as err:
        raise ValueError(
            "Claude did not return valid JSON. This usually means the prompt was "
            f"edited in a way that broke the output format. Raw response:\n{raw}"
        ) from err

    # Record which prompt version produced this so eval reports are comparable, and
    # always attach the safety disclaimer.
    result["prompt_version"] = PROMPT_VERSION
    result["disclaimer"] = DISCLAIMER
    return result
