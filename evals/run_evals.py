"""
run_evals.py — run the translator over every golden case and score it.

This is what turns "I built a tool" into "I built a tool I can prove works." It:
  1. reads the golden cases from dataset.jsonl,
  2. translates each notice,
  3. scores it with the judges in judges.py,
  4. prints a summary table, and
  5. writes a timestamped Markdown report into evals/results/.

Run from the project root:
    python evals/run_evals.py
"""

import datetime as dt
import json
import os
import sys

from anthropic import Anthropic
from dotenv import load_dotenv

# Make `import src...` / `import evals...` work no matter where it is run from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evals.judges import (  # noqa: E402
    MAX_GRADE_LEVEL,
    citation_grounding,
    escalation_correct,
    fact_coverage,
    faithfulness_judge,
    forbidden_facts,
    reading_grade,
)
from src.translate import translate  # noqa: E402

load_dotenv()

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(HERE, "dataset.jsonl")
RESULTS_DIR = os.path.join(HERE, "results")
ROOT = os.path.dirname(HERE)


def load_cases() -> list[dict]:
    with open(DATASET, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def score_case(case: dict, client: Anthropic) -> dict:
    """Translate one notice and run every judge on the result."""
    with open(os.path.join(ROOT, case["doc"]), "r", encoding="utf-8") as fh:
        source = fh.read()

    result = translate(source, client=client)

    grade = reading_grade(result.get("plain_text", ""))
    coverage = fact_coverage(result, case["must_include_facts"])
    forbidden = forbidden_facts(result, case.get("forbidden_facts", []))
    citations = citation_grounding(result, source)
    escalation = escalation_correct(result, case["expected_escalate"])
    faithfulness = faithfulness_judge(source, result, client=client)

    passed = (
        grade <= MAX_GRADE_LEVEL
        and coverage["passed"]
        and forbidden["passed"]
        and citations["passed"]
        and escalation["passed"]
        and faithfulness["passed"]
    )
    return {
        "id": case["id"],
        "prompt_version": result.get("prompt_version", "?"),
        "reading_grade": grade,
        "coverage": coverage,
        "forbidden": forbidden,
        "citations": citations,
        "escalation": escalation,
        "faithfulness": faithfulness,
        "passed": passed,
    }


def run_cases(cases: list[dict], client: Anthropic, scores: list[dict]) -> list[dict]:
    """Score every case, appending into `scores` as we go.

    One case hitting a transient API error (rate limit, overload) must not lose the whole
    batch: the failure is recorded as a stub row and the run continues. Appending into the
    caller's list means even a hard interrupt keeps the completed results.
    """
    for case in cases:
        print(f"  • {case['id']} ...", end=" ", flush=True)
        try:
            scores.append(score_case(case, client))
            print("done")
        except Exception as err:
            scores.append(
                {"id": case["id"], "error": f"{type(err).__name__}: {err}", "passed": False}
            )
            print(f"FAILED to run ({type(err).__name__}) — continuing with the next case")
    return scores


def render_report(scores: list[dict]) -> str:
    """Build a human-readable Markdown report from the scored cases."""
    total = len(scores)
    passed = sum(1 for s in scores if s["passed"])
    version = next(
        (s["prompt_version"] for s in scores if "prompt_version" in s), "?"
    )
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Eval Report — Plain Language Benefits Translator",
        "",
        f"- **Run:** {stamp}",
        f"- **Prompt version:** {version}",
        f"- **Target reading grade:** ≤ {MAX_GRADE_LEVEL}",
        f"- **Overall:** {passed}/{total} cases passed",
        "",
        "| Case | Pass | Reading grade | Facts kept | No bad facts | Citations | "
        "Escalation | Faithfulness |",
        "|------|------|---------------|------------|--------------|-----------|"
        "------------|--------------|",
    ]
    for s in scores:
        if s.get("error"):
            lines.append(f"| {s['id']} | ❌ | — | — | — | — | — | — |")
            continue
        cov, esc, faith = s["coverage"], s["escalation"], s["faithfulness"]
        cit = s["citations"]
        lines.append(
            f"| {s['id']} | {'✅' if s['passed'] else '❌'} "
            f"| {s['reading_grade']} "
            f"| {cov['covered']}/{cov['total']} "
            f"| {'✅' if s['forbidden']['passed'] else '❌'} "
            f"| {cit['total'] - len(cit['ungrounded'])}/{cit['total']} "
            f"| exp {esc['expected']} / got {esc['actual']} "
            f"| {faith.get('score', '?')}/5 |"
        )

    # Detail any failures so a non-coder can see exactly what to fix.
    failures = [s for s in scores if not s["passed"]]
    if failures:
        lines += ["", "## Failures — what to look at", ""]
        for s in failures:
            lines.append(f"### {s['id']}")
            if s.get("error"):
                lines.append(f"- Case did not complete (API/runtime error): {s['error']}")
                lines.append("")
                continue
            if s["reading_grade"] > MAX_GRADE_LEVEL:
                lines.append(f"- Reading grade {s['reading_grade']} is above target.")
            if not s["coverage"]["passed"]:
                lines.append(f"- Missing required facts: {s['coverage']['missing']}")
            if not s["forbidden"]["passed"]:
                lines.append(f"- Invented (forbidden) facts appeared: {s['forbidden']['found']}")
            if not s["citations"]["passed"]:
                lines.append(f"- Citations not found in source: {s['citations']['ungrounded']}")
            if not s["escalation"]["passed"]:
                lines.append(
                    f"- Escalation wrong: expected {s['escalation']['expected']}, "
                    f"got {s['escalation']['actual']}."
                )
            if not s["faithfulness"]["passed"]:
                lines.append(f"- Faithfulness: {s['faithfulness'].get('explanation', '')}")
            lines.append("")
    return "\n".join(lines)


def main() -> int:
    if not os.getenv("ANTHROPIC_API_KEY"):
        print(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key.\n"
            "(You can still read a saved example at evals/results/sample-report.md,\n"
            " or run the offline demo: python -m src.cli --demo)"
        )
        return 1

    client = Anthropic()
    cases = load_cases()
    print(f"Running {len(cases)} golden cases...\n")

    scores: list[dict] = []
    try:
        run_cases(cases, client, scores)
    finally:
        # Even if the run is interrupted, completed results are money already spent —
        # write whatever we have so it is never lost.
        if scores:
            report = render_report(scores)
            os.makedirs(RESULTS_DIR, exist_ok=True)
            out_path = os.path.join(
                RESULTS_DIR, dt.datetime.now().strftime("report-%Y%m%d-%H%M%S.md")
            )
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(report)
            passed = sum(1 for s in scores if s["passed"])
            print(f"\n{passed}/{len(scores)} passed. Report written to {out_path}\n")
            print(report)

    return 0 if scores and all(s["passed"] for s in scores) else 1


if __name__ == "__main__":
    sys.exit(main())
