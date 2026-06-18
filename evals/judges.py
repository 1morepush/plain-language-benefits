"""
judges.py — the scoring functions for the eval harness.

Each "judge" answers one question about a translation. We keep them separate so a
report can show WHICH dimension failed, not just a single pass/fail. The judges:

  1. reading_grade()       — how hard is the text to read?              (local, no API)
  2. fact_coverage()       — did required facts/deadlines survive?      (local, no API)
  3. forbidden_facts()     — did it invent a plausible-but-wrong fact?  (local, no API)
  4. citation_grounding()  — is every citation a real quote from source?(local, no API)
  5. escalation_correct()  — did it flag a human when it should?        (local, no API)
  6. faithfulness_judge()  — did it invent anything not in the source?  (LLM judge)

Five of the six need no API at all, which keeps the harness fast and cheap and means
most regressions are caught for free.
"""

import json
import re

import textstat
from anthropic import Anthropic

# A separate, capable model double-checks faithfulness. Using an independent judge
# ("LLM-as-judge") is standard practice: the thing being graded should not grade itself.
JUDGE_MODEL = "claude-sonnet-4-6"

# Target reading level. Public-health plain-language guidance commonly aims for grade
# 6-8. We allow up to 8.0 before flagging.
MAX_GRADE_LEVEL = 8.0


# --- small shared helpers -----------------------------------------------------

def _as_bool(value) -> bool:
    """Coerce a model-supplied value to a real boolean.

    The model is asked for a JSON boolean, but if it ever returns the *string*
    "false", plain bool("false") would be True — a subtle, dangerous bug for a
    field that decides whether a human gets involved. This handles both.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1"}
    return bool(value)


def _normalize(text: str) -> str:
    """Lowercase, straighten quotes, and collapse all whitespace to single spaces.

    Used so that a quote which is verbatim except for line breaks or curly quotes
    still matches the source text.
    """
    text = text.lower().replace("“", '"').replace("”", '"').replace("’", "'")
    return re.sub(r"\s+", " ", text).strip()


def _visible_text(result: dict) -> str:
    """Everything the reader actually sees: plain text + action items + citations."""
    return (
        result.get("plain_text", "")
        + " "
        + " ".join(result.get("action_items", []) or [])
        + " "
        + " ".join(result.get("citations", []) or [])
    )


# --- the judges ---------------------------------------------------------------

def reading_grade(plain_text: str) -> float:
    """Flesch-Kincaid grade level of the rewritten text. Lower = easier to read."""
    if not plain_text.strip():
        return 99.0
    return round(textstat.flesch_kincaid_grade(plain_text), 1)


def fact_coverage(result: dict, must_include_facts: list[str]) -> dict:
    """Check that each required fact appears somewhere in the visible output.

    Missing a deadline or dollar amount is the most dangerous failure mode, so this
    is strict: missing even one required fact fails the case.
    """
    haystack = _visible_text(result).lower()
    missing = [fact for fact in must_include_facts if fact.lower() not in haystack]
    return {
        "covered": len(must_include_facts) - len(missing),
        "total": len(must_include_facts),
        "missing": missing,
        "passed": len(missing) == 0,
    }


def forbidden_facts(result: dict, forbidden: list[str]) -> dict:
    """Catch invented facts: fail if any plausible-but-WRONG fact appears in the output.

    Each golden case lists a few facts that look right but are not in the source (e.g.
    a transposed dollar amount). If the tool ever states one, it hallucinated.
    """
    forbidden = forbidden or []
    haystack = _visible_text(result).lower()
    found = [bad for bad in forbidden if bad.lower() in haystack]
    return {"checked": len(forbidden), "found": found, "passed": len(found) == 0}


def citation_grounding(result: dict, source_text: str) -> dict:
    """Verify every citation is really a quote from the source (not paraphrased/invented).

    This is what makes "every claim is auditable" true rather than aspirational. A quote
    may be truncated with an ellipsis; each non-trivial segment must appear in the source.
    """
    source_norm = _normalize(source_text)
    citations = result.get("citations", []) or []
    ungrounded = []
    for raw in citations:
        quote = _normalize(raw).strip('"').strip()
        # Split on ellipsis and on spaced separators (" / ", " | ") that models use to join
        # two real source fragments into one quote. (Spaced, so dates like 08/01/2026 stay
        # intact.) Each non-trivial fragment must still appear in the source.
        segments = [
            s.strip()
            for s in re.split(r"\.\.\.|…|\s+/\s+|\s+\|\s+", quote)
            if len(s.strip()) >= 12
        ]
        segments = segments or [quote]  # short quote: check it whole
        if not all(seg in source_norm for seg in segments):
            ungrounded.append(raw)
    return {"total": len(citations), "ungrounded": ungrounded, "passed": len(ungrounded) == 0}


def escalation_correct(result: dict, expected_escalate: bool) -> dict:
    """Did the tool's escalate flag match the golden label for this notice?"""
    actual = _as_bool(result.get("escalate", False))
    return {"expected": expected_escalate, "actual": actual, "passed": actual == expected_escalate}


def faithfulness_judge(
    source_text: str, result: dict, client: Anthropic | None = None
) -> dict:
    """Ask an independent model whether the rewrite invented anything.

    Returns {"score": 1-5, "passed": bool, "explanation": str}. A score of 5 means
    every claim in the rewrite is supported by the source; lower means hallucination.
    A malformed judge reply fails the case loudly instead of crashing the whole run.
    """
    if client is None:
        client = Anthropic()

    judge_prompt = f"""You are auditing a plain-language rewrite of an official benefits \
notice for FAITHFULNESS. Compare the rewrite to the source. Did the rewrite state any \
fact (especially a date, dollar amount, phone number, or deadline) that is NOT supported \
by the source, or change the meaning of any requirement?

IMPORTANT: the rewrite intentionally includes two safety additions — a recommendation to \
contact a caseworker or local legal aid, and a "this is not legal advice" disclaimer. These \
are deliberate and are NOT claims about the notice; do NOT count them as unfaithful. Judge \
ONLY whether the facts about the notice (dates, amounts, names, deadlines, and what it \
requires) are accurate and unchanged.

SOURCE NOTICE:
{source_text}

PLAIN-LANGUAGE REWRITE:
{result.get("plain_text", "")}

Score 1-5 where 5 = every claim is fully supported by the source and no meaning changed, \
and 1 = contains invented or contradicted facts. Respond with ONLY JSON:
{{"score": <1-5>, "explanation": "<one sentence>"}}"""

    response = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": judge_prompt}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        verdict = json.loads(text)
    except json.JSONDecodeError:
        # Don't crash the whole eval run on one bad judge reply — fail this case clearly.
        return {"score": 0, "passed": False, "explanation": "judge returned non-JSON"}
    verdict["passed"] = verdict.get("score", 0) >= 4
    return verdict
