import re
import unicodedata

# LaTeX accent command → Unicode combining mark.
ACCENTS = {
    "`": "\u0300",
    "'": "\u0301",
    "^": "\u0302",
    "~": "\u0303",
    "=": "\u0304",
    "u": "\u0306",
    ".": "\u0307",
    '"': "\u0308",
    "r": "\u030a",
    "H": "\u030b",
    "v": "\u030c",
    "c": "\u0327",
    "k": "\u0328",
}
LETTERS = {
    "aa": "å", "AA": "Å", "ae": "æ", "AE": "Æ", "oe": "œ", "OE": "Œ", "ss": "ß",
    "o": "ø", "O": "Ø", "l": "ł", "L": "Ł", "i": "ı", "j": "ȷ",
    "dh": "ð", "DH": "Ð", "dj": "đ", "DJ": "Đ",
}  # fmt: skip

# A control word eats the spaces after it: "Stra\ss e" is "Straße".
LETTER = re.compile(r"\\(" + "|".join(sorted(LETTERS, key=len, reverse=True)) + r")(?![a-zA-Z])\s*")
# "\'e", "\'{e}", "\c{s}", "\v C"; runs after LETTER, so "\'\i" is already "\'ı".
ACCENT = re.compile(
    r"\\([`'^~=.\"]|[uvHckr](?![a-zA-Z]))"  # the command
    r"\s*(?:\{\s*([a-zA-Zıȷ])\s*\}|([a-zA-Zıȷ]))"  # its letter, braced or not
)


def _accent(m: re.Match) -> str:
    base = (m[2] or m[3]).replace("ı", "i").replace("ȷ", "j")  # an accent replaces the dot
    return base + ACCENTS[m[1]]


def latex_to_unicode(text: str) -> str:
    """Turn LaTeX accent commands in author names into Unicode: "{\\O}ystein" → "Øystein"."""
    if "\\" not in text and "{" not in text:
        return text
    # "\&" is an escaped ampersand; "\ " is a control space whose accent the feed already lost.
    text = text.replace("\\&", "&").replace("\\ ", "")
    text = LETTER.sub(lambda m: LETTERS[m[1]], text)
    text = ACCENT.sub(_accent, text)
    return unicodedata.normalize("NFC", text.replace("{", "").replace("}", ""))
