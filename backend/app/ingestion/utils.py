import re
import unicodedata

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def normalize_author_name(full_name: str) -> str:
    """"Yann LeCun" -> "yann lecun"; strips accents/punctuation for dedup matching."""
    ascii_name = unicodedata.normalize("NFKD", full_name).encode("ascii", "ignore").decode("ascii")
    collapsed = _NON_ALNUM_RE.sub(" ", ascii_name.lower()).strip()
    return re.sub(r"\s+", " ", collapsed)
