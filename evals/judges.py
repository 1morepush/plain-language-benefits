"""
judges.py — the scoring functions for the eval harness.

Each "judge" answers one question about a translation. We keep them separate so a
report can show WHICH dimension failed, not just a single pass/fail. The four judges:

  1. reading_grade()      — how hard is the text to read?            (local, no API)
  2. fact_coverage()      — did required facts/deadlines survive?    (local, no API)
  3. escalation_correct() — did the tool flag a human when it should?(local, no API)
  4. faithfulness_judge() — did the tool invent anything not in the source? (LLM judge)

Three of the four need no API at all, which keeps the harness fast and cheap and means
most regressions are caught for free.
"""

import json

import textstat
from anthropic import Anthropic

# A separate, capable model double-checks faithfulness. Using an independent judge
# ("LLM-as-judge") is standard practice: the thing being graded should not grade itself.
JUDGE_MODEL = "claude-sonnet-4-6"

# Target reading level. Public-health plain-language guidance commonly aims for grade
# 6-8. We allow up to 8.0 before flagging.
MAX_GRADE_LEVEL = 8.0


def reading_grade(plain_text: str) -> float:
    """Flesch-Kincaid grade level of the rewritten text. Lower = easier to read."""
    if not plain_text.strip():
        return 99.0
    return round(textstat.flesch_kincaid_grade(plain_text), 1)


def fact_coverage(result: dict, must_include_facts: list[str]) -> dict:
    """Check that each required fact appears somewhere in the visible output.

    We search the plain text + action items + citations (case-insensitive). Missing a
    deadline or dollar amount is the most dangerous failure mode, so this is strict.
    """
    haystack = (
        result.get("plain_text", "")
        + " "
        + " ".join(result.get("action_items", []) or [])
        + " "
        + " ".join(result.get("citations", []) or [])
    ).lower()

    missing = [fact for fact in must_include_facts if fact.lower() not in haystack]
    covered = len(must_include_facts) - len(missing)
    return {
        "covered": covered,
        "total": len(must_include_facts),
        "missing": missing,
        "passed": len(missing) == 0,
    }


def escalation_correct(result: dict, expected_escalate: bool) -> dict:
    """Did the tool's escalate flag match the golden label for this notice?"""
    actual = bool(result.get("escalate", False))
    return {"expected": expected_escalate, "actual": actual, "passed": actual == expected_escalate}


def faithfulness_judge(
    source_text: str, result: dict, client: Anthropic | None = None
) -> dict:
    """Ask an independent model whether the rewrite invented anything.

    Returns {"score": 1-5, "passed": bool, "explanation": str}. A score of 5 means
    every claim in the rewrite is supported by the source; lower means hallucination.
    """
    if client is None:
        client = Anthropic()

    judge_prompt = f"""You are auditing a plain-language rewrite of an official benefits \
notice for FAITHFULNESS. Compare the rewrite to the source. Did the rewrite state any \
fact (especially a date, dollar amount, phone number, or deadline) that is NOT supported \
by the source, or change the meaning of any requirement?

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
    verdict = json.loads(text)
    verdict["passed"] = verdict.get("score", 0) >= 4
    return verdict
