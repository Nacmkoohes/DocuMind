
import re

# map each char to its normalized
_CHAR_MAP = str.maketrans({
    "ي": "ی",
    "ى": "ی",
    "ك": "ک",
    "ة": "ه",
    "ۀ": "ه",
    "أ": "ا",
    "إ": "ا",
    "ٱ": "ا",
    #normalize numbers ex: ۱۲۳-> 123
    #persian
    **{chr(0x06F0 + i): str(i) for i in range(10)},
    #arabic
    **{chr(0x0660 + i): str(i) for i in range(10)},

    #Zero Width Non-Joiner
    "\u200c": " ",
})
#pattern of arabic vowels
_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670]")

#pattern that finds words
_TOKEN = re.compile(r"\w+", re.UNICODE)


def normalize(text: str) -> str:
    return _DIACRITICS.sub("", text.translate(_CHAR_MAP))


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(normalize(text).lower())
