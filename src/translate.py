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


def _strip_json_fences(text: str) -> str:
    """Be forgiving if the model wraps its JSON in ```json ... ``` fences."""
    text = text.strip()
    if text.startswith("```"):
        # drop the first line (``` or ```json) and any trailing fence
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.rstrip().endswith("```"):
            text = text.rstrip()[: -len("```")]
    return text.strip()


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

    raw = _strip_json_fences(response.content[0].text)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as err:
        raise ValueError(
            "Claude did not return valid JSON. This usually means the prompt was "
            f"edited in a way that broke the output format. Raw response:\n{raw}"
        ) from err

    # Record which prompt version produced this so eval reports are comparable.
    result["prompt_version"] = PROMPT_VERSION
    return result
