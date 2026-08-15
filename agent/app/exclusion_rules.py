import re
from typing import ClassVar

from app.models.recommendation import RecommendationCandidate


class ExclusionRules:
    ROUNDUP_WORDS: ClassVar[list[str]] = [
        "roundup",
        "weekly roundup",
        "recap",
        "digest",
        "what's new",
        "whats new",
        "release note",
        "release notes",
    ]
    ANNOUNCEMENT_WORDS: ClassVar[list[str]] = [
        "news",
        "announcement",
        "announcing",
        "announcements",
    ]
    TAG_TO_WORDS: ClassVar[tuple[tuple[str, list[str]], ...]] = (
        ("roundup", ROUNDUP_WORDS),
        ("announcement", ANNOUNCEMENT_WORDS),
    )

    @classmethod
    def compiled_patterns(cls) -> tuple[tuple[str, re.Pattern[str]], ...]:
        return tuple(
            (tag, re.compile(cls._to_pattern(words), re.IGNORECASE))
            for tag, words in cls.TAG_TO_WORDS
        )

    @staticmethod
    def _to_pattern(words: list[str]) -> str:
        escaped_words = [re.escape(word).replace(
            "\\ ", r"\s+") for word in words]
        return rf"\b({'|'.join(escaped_words)})\b"


EXCLUSION_PATTERNS = ExclusionRules.compiled_patterns()


def apply_exclusion_tags(
    candidates: list[RecommendationCandidate],
) -> list[RecommendationCandidate]:
    tagged_candidates: list[RecommendationCandidate] = []

    for candidate in candidates:
        text = " ".join(part for part in (
            candidate.title, candidate.summary) if part)
        exclusion_tags = [
            tag for tag, pattern in EXCLUSION_PATTERNS if pattern.search(text)
        ]
        tagged_candidates.append(
            candidate.model_copy(update={"exclusion_tags": exclusion_tags})
        )

    filtered_candidates = [
        candidate for candidate in tagged_candidates if not candidate.exclusion_tags
    ]
    return filtered_candidates or tagged_candidates
