"""
ask.py — the "Ask about this question" chat (stage 3).

A person types one short message about the question on their screen. This file:
  1. builds the request (system prompt + that one question's official wording),
  2. calls Claude once,
  3. checks the reply with safety_check.py and swaps in a safe message if it is flagged.

Each message is answered on its own. Nothing is remembered between messages and
nothing is stored. The SSN check has already run in app.py before this is reached.
"""

from pathlib import Path

from safety_check import find_flags

MODEL = "claude-sonnet-5-5"
MAX_MESSAGE_LENGTH = 500  # characters a person may type
PROMPTS = Path(__file__).parent / "prompts"

# Lets the API hand a declined request to another Claude model instead of failing.
FALLBACK_BETA = "server-side-fallback-2026-07-01"

LANGUAGE_NAMES = {"en": "English", "es": "Spanish"}

# Fixed messages. These are written by a person, not by the AI.
NOT_IN_FILE = {
    "en": "Plain Path can't help with that question. Please use the official instructions.",
    "es": "Plain Path no puede ayudar con esa pregunta. Por favor, use las instrucciones "
          "oficiales.",
}
SAFE_REPLY = {
    "en": "Plain Path can't answer that. It can explain what a question means, but it can't "
          "tell you what to answer or whether you will get benefits. Your answers must be "
          "true and in your own words. For help with your own situation, please talk with "
          "Arizona DES or with legal aid.",
    "es": "Plain Path no puede responder eso. Puede explicar lo que significa una pregunta, "
          "pero no puede decirle qué responder ni si recibirá beneficios. Sus respuestas "
          "deben ser verdaderas y en sus propias palabras. Para ayuda con su situación, por "
          "favor hable con Arizona DES o con ayuda legal.",
}
EMPTY_MESSAGE = {
    "en": "Please type a question first.",
    "es": "Por favor, escriba primero una pregunta.",
}
TOO_LONG = {
    "en": f"Please keep your question under {MAX_MESSAGE_LENGTH} characters.",
    "es": f"Por favor, escriba su pregunta en menos de {MAX_MESSAGE_LENGTH} caracteres.",
}
UNAVAILABLE = {
    "en": "The question box is not available right now. Please use the official instructions.",
    "es": "El cuadro de preguntas no está disponible ahora. Por favor, use las instrucciones "
          "oficiales.",
}


def system_prompt() -> str:
    """The main hard rules, followed by the extra rules for this chat box."""
    main = (PROMPTS / "system.md").read_text(encoding="utf-8")
    extra = (PROMPTS / "ask.md").read_text(encoding="utf-8")
    return main + "\n\n" + extra


def build_request(question: dict, message: str, lang: str) -> str:
    """Everything Claude is told about this one message."""
    explanation = question["explanation"][lang]  # None unless a person reviewed it
    reviewed = explanation["text"] if explanation else "(none yet)"
    return f"""<official_wording>
{question["official_text_en"]}
</official_wording>

<reviewed_explanation>
{reviewed}
</reviewed_explanation>

<user_message>
{message}
</user_message>

Reply in {LANGUAGE_NAMES[lang]}."""


def answer(client, question: dict, message: str, lang: str) -> dict:
    """Ask Claude, then check the reply. Returns {"reply": text, "source": "ai" or "fixed"}."""
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=system_prompt(),
        messages=[{"role": "user", "content": build_request(question, message, lang)}],
        output_config={"effort": "low"},  # short, quick replies
        betas=[FALLBACK_BETA],
        fallbacks="default",
    )

    text = "".join(block.text for block in response.content if block.type == "text").strip()

    # Anything other than a normal, complete, unflagged reply becomes the safe message.
    if response.stop_reason != "end_turn" or not text or find_flags(text):
        return {"reply": SAFE_REPLY[lang], "source": "fixed"}
    return {"reply": text, "source": "ai"}
