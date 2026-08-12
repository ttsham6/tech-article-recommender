import re
from typing import Any, cast

from pydantic import HttpUrl

from app.models.recommendation import RecommendationCandidate

TITLE_LINE_PATTERN = re.compile(r"^#\s+(?P<title>.+)$", re.MULTILINE)
SUMMARY_SECTION_PATTERN = re.compile(
    r"^##\s+Summary\s*(?P<summary>.*?)(?:\n##\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)


def build_candidates(results: list[dict[str, Any]]) -> list[RecommendationCandidate]:
    candidates_by_doc_id: dict[str, RecommendationCandidate] = {}

    for result in results:
        metadata = result.get("metadata") or {}
        text = result.get("text", "")
        if not is_rss_candidate(metadata):
            continue

        doc_id = first_non_empty(metadata.get("doc_id"))
        title = first_non_empty(
            metadata.get("title"), extract_title(text))
        url = first_non_empty(metadata.get("url"))

        if not doc_id or not title or not url or doc_id in candidates_by_doc_id:
            continue

        candidates_by_doc_id[doc_id] = RecommendationCandidate(
            doc_id=doc_id,
            title=title,
            url=cast(HttpUrl, url),
            summary=extract_summary(text),
        )

    return list(candidates_by_doc_id.values())


def is_rss_candidate(metadata: dict[str, Any]) -> bool:
    return all(
        isinstance(metadata.get(key), str) and cast(
            str, metadata.get(key)).strip()
        for key in ("source", "doc_id", "url")
    )


def extract_title(text: str) -> str | None:
    match = TITLE_LINE_PATTERN.search(text)
    if match:
        return match.group("title").strip()

    for line in text.splitlines():
        stripped = line.strip().lstrip("-#* ").strip()
        if stripped and not stripped.startswith("URL:") and not stripped.startswith("http"):
            return stripped[:200]
    return None


def extract_summary(text: str) -> str | None:
    match = SUMMARY_SECTION_PATTERN.search(text)
    if not match:
        return None
    summary = re.sub(r"\s+", " ", match.group("summary")).strip()
    if not summary:
        return None
    return summary[:400]


def first_non_empty(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
