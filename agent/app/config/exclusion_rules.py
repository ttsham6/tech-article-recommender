import re

# 除外ルール。専門性が低い記事や、ニュース・告知系の記事を除外するためのルールを定義する。
EXCLUSION_RULES = (
    ("roundup", [
        "roundup",
        "weekly roundup",
        "recap",
        "digest",
        "what's new",
        "whats new",
        "release note",
        "release notes",
    ]),
    ("announcement", [
        "news",
        "announcement",
        "announcing",
        "announcements",
    ]),
)


def _to_pattern(words: list[str]) -> str:
    escaped_words = [re.escape(word).replace("\\ ", r"\s+") for word in words]
    return rf"\b({'|'.join(escaped_words)})\b"


EXCLUSION_PATTERNS = tuple(
    (tag, re.compile(_to_pattern(words), re.IGNORECASE))
    for tag, words in EXCLUSION_RULES
)
