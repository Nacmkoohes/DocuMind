
import re

_CHAR_MAP = str.maketrans({
    "ي": "ی",
    "ى": "ی",
    "ك": "ک",
    "ة": "ه",
    "ۀ": "ه",
    "أ": "ا",
    "إ": "ا",
    "ٱ": "ا",
    **{chr(0x06F0 + i): str(i) for i in range(10)},
    **{chr(0x0660 + i): str(i) for i in range(10)},
    "\u200c": " ",
})

_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670]")
_TOKEN = re.compile(r"\w+", re.UNICODE)

STOPWORDS = {
    "a", "an", "the", "and", "or", "but",
    "is", "are", "was", "were", "be", "been",
    "being", "do", "does", "did",
    "what", "which", "who", "when", "where",
    "why", "how", "to", "of", "in", "on",
    "at", "for", "from", "with", "by", "as",
    "it", "this", "that", "these", "those",
    "can", "could", "would", "should",
    "used", "use", "commonly",
}

def normalize(text: str) -> str:
    return _DIACRITICS.sub("", text.translate(_CHAR_MAP))


def tokenize(text: str) -> list[str]:
    tokens = _TOKEN.findall(normalize(text).lower())
    return [token for token in tokens if token not in STOPWORDS]
