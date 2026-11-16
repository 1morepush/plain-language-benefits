"""
ssn_guard.py — blocks messages that look like they contain a Social Security number.

Hard rule: Plain Path must never receive personal data. If a user types something
that looks like an SSN, the message is stopped BEFORE it can reach the AI.

The same pattern is used in the browser (static/ssn_guard.js) so the user gets a
warning right away. The browser check is a courtesy; THIS server check is the real
block, because a browser check can be switched off.
"""

import re

# What counts as "looks like an SSN":
#   123-45-6789      the usual way it is written
#   123 45 6789      spaces, dots, or long dashes instead of hyphens
#   123456789        9 digits in a row
# The pattern is: 3 digits, optional separator, 2 digits, optional separator, 4 digits,
# and NOT part of a longer number (so a 10-digit phone number is not flagged).
#
# It is written with no backslashes on purpose, so the exact same text works in
# both Python and JavaScript. tests/test_ssn_guard.py checks the two copies match.
SSN_PATTERN = "(?<![0-9])[0-9]{3}[-. –—]?[0-9]{2}[-. –—]?[0-9]{4}(?![0-9])"

_SSN_REGEX = re.compile(SSN_PATTERN)

WARNING_EN = (
    "That looks like a Social Security number or another ID number. "
    "Your message was not sent. Please do not share personal information here."
)
WARNING_ES = (
    "Eso parece un número de Seguro Social u otro número de identificación. "
    "Su mensaje no se envió. Por favor, no comparta información personal aquí."
)


def looks_like_ssn(text: str) -> bool:
    """Return True if the text contains something shaped like an SSN."""
    if not text:
        return False
    return _SSN_REGEX.search(text) is not None
