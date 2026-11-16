"""Tests for review gating and the shape of the data files."""

from app import app
from content import LANGUAGES, build_content, gated_explanation, load_json


def test_unreviewed_explanation_is_hidden():
    entry = {"explanation_en": "draft", "reviewed_en": False}
    assert gated_explanation(entry, "en") is None


def test_only_exact_true_counts_as_reviewed():
    for not_true in ("true", "yes", 1, None):
        assert gated_explanation({"explanation_en": "x", "reviewed_en": not_true}, "en") is None


def test_languages_are_approved_separately():
    entry = {
        "explanation_en": "checked",
        "explanation_es": "sin revisar",
        "reviewed_en": True,
        "reviewed_es": False,
    }
    assert gated_explanation(entry, "en")["text"] == "checked"
    assert gated_explanation(entry, "es") is None


def test_missing_explanation_is_hidden():
    assert gated_explanation(None, "en") is None


def test_api_never_sends_unreviewed_text():
    """Check the real data files: no unreviewed draft may appear anywhere in the API reply."""
    reply = app.test_client().get("/api/content").get_data(as_text=True)
    for entry in load_json("explanations.json").values():
        for lang in LANGUAGES:
            draft = entry.get(f"explanation_{lang}")
            if draft and entry.get(f"reviewed_{lang}") is not True:
                assert draft not in reply


def test_data_files_fit_together():
    content = build_content()
    section_ids = {s["id"] for s in content["sections"]}
    intake_keys = {i["key"] for i in content["intake"]}

    assert 3 <= len(content["intake"]) <= 5
    for q in content["questions"]:
        assert q["section"] in section_ids, f"{q['id']} points at a missing section"
        assert q["official_text_en"], f"{q['id']} has no official English text"
        assert q["source"], f"{q['id']} has no source"
    ids = [q["id"] for q in content["questions"]]
    assert len(ids) == len(set(ids)), "two questions share an id"

    # Every "show_if" must name a real intake question.
    for item in content["sections"] + content["checklist"]:
        if "show_if" in item:
            assert item["show_if"] in intake_keys


def test_intake_asks_for_no_personal_data():
    """Intake questions are yes/no only, so each one must be phrased as a question."""
    for item in load_json("intake.json"):
        assert item["text_en"].endswith("?") and item["text_es"].endswith("?")


def test_page_carries_the_disclaimer():
    page = app.test_client().get("/").get_data(as_text=True)
    assert "student prototype, not legal advice and not affiliated with Arizona DES" in page


def test_reviewed_explanation_is_hidden_when_official_wording_changes():
    entry = {"explanation_en": "about the old wording", "reviewed_en": True, "written_for": "Old?"}
    assert gated_explanation(entry, "en", "Old?")["text"] == "about the old wording"
    assert gated_explanation(entry, "en", "New wording?") is None
