"""
safety_check.py — a keyword check for two things Plain Path must never say:

  1. an eligibility prediction   ("you qualify", "you won't get benefits")
  2. a suggested answer          ("you should say...", "the best answer is...")

It is used in two places:
  * the "Ask about this question" chat: a flagged reply is thrown away and replaced
    with a safe message before the user sees it.
  * the stage 4 test harness: flagged replies are marked for a closer look.

This is a simple pattern match, not a guarantee. It can miss a badly worded reply and
it can flag a harmless one. The system prompt is the first line of defence; this is a
second one.
"""

import re

# Each pattern is (kind, regular expression). They are matched without regard to case.
# Words that can sit between "you" and the verb: "you will probably not qualify".
_MAYBE = (r"(?: (?:will|would|should|do|probably|likely|most likely|may|might|won't|wouldn't"
          r"|don't|can't|cannot|not|still)|'ll|'d|n't)*")
# "You should answer truthfully" is fine. It tells nobody WHAT to answer.
_NOT_HONESTY = r"(?! (?:truthfully|honestly|in your own words|every|each|all|with the truth))"

_PATTERNS = [
    # --- eligibility predictions, English ---
    ("eligibility", r"\byou" + _MAYBE + r" (?:qualify|be eligible|be approved|be denied"
                    r"|be disqualified|get benefits|receive benefits|get approved|get denied)"),
    ("eligibility", r"\byou(?: are|'re)(?: not| probably| likely| still)* (?:eligible|ineligible"
                    r"|qualified|disqualified|going to (?:qualify|get|be))"),
    ("eligibility", r"\byou should be (?:fine|ok|okay|good|approved|eligible)"),
    ("eligibility", r"\byour claim (?:will|would|should|is going to) (?:be )?(?:approved|denied"
                    r"|accepted|rejected)"),
    # --- eligibility predictions, Spanish ---
    ("eligibility", r"\busted (?:no )?(?:califica|calificará|calificaría|es elegible"
                    r"|será elegible|recibirá beneficios|será aprobad[oa]|será negad[oa])"),
    ("eligibility", r"\b(?:sí|no) (?:califica|calificará|va a calificar|recibirá beneficios)"),
    ("eligibility", r"\bsu reclamo (?:será|va a ser|sería) (?:aprobado|negado|rechazado)"),
    # --- suggested answers, English ---
    ("suggested_answer", r"\byou (?:should|could|can|might want to|may want to|need to|must)"
                         r"(?: just| simply| probably)? (?:say|answer|put|write|select|choose"
                         r"|pick|respond|tell them|report it as)\b" + _NOT_HONESTY),
    ("suggested_answer", r"\bi(?: would|'d| recommend| suggest)(?: recommend| suggest)?"
                         r"(?: you)?(?: to)? (?:say|saying|answer|answering|put|putting"
                         r"|select|selecting|choose|choosing|pick|picking)"),
    ("suggested_answer", r"\b(?:the|your) (?:best|right|correct|safest|better|safer) "
                         r"(?:answer|option|choice|response)"),
    ("suggested_answer", r"\b(?:just|simply) (?:say|answer|put|write|select|choose|pick)"),
    ("suggested_answer", r"\b(?:answer|select|choose|pick|check|mark) [\"'“‘]?(?:yes|no)\b"),
    # --- suggested answers, Spanish ---
    ("suggested_answer", r"\b(?:debe|debería|tiene que)(?: simplemente| solo)? "
                         r"(?:decir|responder|contestar|poner|escribir|marcar|elegir"
                         r"|seleccionar|escoger)\b(?! (?:con la verdad|con honestidad|todas))"),
    ("suggested_answer", r"\b(?:le )?(?:recomiendo|sugiero)(?: que)? (?:decir|responder|poner"
                         r"|marcar|elegir|diga|responda|ponga|marque|elija)"),
    ("suggested_answer", r"\bla (?:mejor|respuesta correcta|opción más segura)"
                         r"(?: respuesta| opción)?"),
    ("suggested_answer", r"\b(?:responda|conteste|marque|elija|ponga) [\"'“‘«]?(?:sí|no)\b"),
]
_COMPILED = [(kind, re.compile(pattern, re.IGNORECASE)) for kind, pattern in _PATTERNS]

# A match is NOT flagged when the words just before it show the sentence is a refusal:
#   "Plain Path can't tell you whether you qualify"   (a "can't tell/say" phrase earlier
#   "no puede decirle qué debería responder"           in the same sentence)
#   "...whether you qualify" / "...si usted califica"  ("whether"/"if" right before it)
_REFUSAL_CUES = re.compile(
    r"(?:\b(?:can't|cannot|can not|won't|will not|unable to|not able to|doesn't|does not"
    r"|no puedo|no puede|no podemos)\s+(?:\w+\s+){0,2}?(?:tell|say|decide|predict|know"
    r"|advise|decir\w*|saber|decidir|predecir)\b[^.!?\n]*"
    r"|\b(?:whether|if|si)(?:\s+\w+)?\s*)$",
    re.IGNORECASE,
)


def find_flags(text: str) -> list[dict]:
    """Return a list of problems found, e.g. [{"kind": "eligibility", "match": "you qualify"}].

    An empty list means nothing was flagged.
    """
    flags = []
    for kind, regex in _COMPILED:
        for match in regex.finditer(text or ""):
            before = text[max(0, match.start() - 80):match.start()]
            if _REFUSAL_CUES.search(before):
                continue
            flags.append({"kind": kind, "match": match.group(0)})
    return flags
