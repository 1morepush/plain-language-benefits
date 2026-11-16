"""Tests for the keyword check that flags eligibility predictions and suggested answers."""

import pytest

from safety_check import find_flags


@pytest.mark.parametrize(
    "text, kind",
    [
        ("You qualify for benefits.", "eligibility"),
        ("You will probably qualify.", "eligibility"),
        ("You probably won't get benefits.", "eligibility"),
        ("You are not eligible.", "eligibility"),
        ("Don't worry, you should be fine.", "eligibility"),
        ("Your claim will be denied.", "eligibility"),
        ("Usted califica para beneficios.", "eligibility"),
        ("Usted no recibirá beneficios.", "eligibility"),
        ("You should say you were laid off.", "suggested_answer"),
        ("I would put 'lack of work'.", "suggested_answer"),
        ("I'd recommend selecting the second option.", "suggested_answer"),
        ("The best answer is 'laid off'.", "suggested_answer"),
        ("Just say you quit.", "suggested_answer"),
        ("Answer 'No' to this one.", "suggested_answer"),
        ("Debería decir que lo despidieron.", "suggested_answer"),
        ("Le recomiendo marcar la primera opción.", "suggested_answer"),
        ("Responda 'sí' a esta pregunta.", "suggested_answer"),
        ("If you were laid off, you qualify.", "eligibility"),
        ("I can't see your file, but you should say 'laid off'.", "suggested_answer"),
    ],
)
def test_flags_things_plain_path_must_never_say(text, kind):
    assert kind in [flag["kind"] for flag in find_flags(text)]


@pytest.mark.parametrize(
    "text",
    [
        "",
        "A layoff means the job ended because there was no more work.",
        "Being discharged means the employer ended your job.",
        "Plain Path can't tell you whether you qualify. Only Arizona DES decides that.",
        "Plain Path can't tell you what you should say. Your answer must be true.",
        "I'm not able to tell you if you will get benefits.",
        "Your answer must be true and in your own words.",
        "Plain Path no puede decirle si usted califica.",
        "Plain Path no puede decirle qué debería responder.",
        "You will need your last pay stub.",
        "Talk with Arizona DES or legal aid about your situation.",
        "You should answer truthfully.",
        "You must answer in your own words.",
        "You can check with the agency if you are unsure what a term means.",
        "Debe responder con la verdad.",
    ],
)
def test_does_not_flag_explanations_or_refusals(text):
    assert find_flags(text) == []
