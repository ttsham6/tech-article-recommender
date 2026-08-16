from dataclasses import dataclass
from typing import Any

from app.config.aws_service_definitions import (
    COMPILED_AWS_SERVICE_PATTERNS,
    COMPILED_AWS_TOPIC_PATTERNS,
)


@dataclass(frozen=True)
class ArticleSearchContext:
    query: str
    retrieval_filter: dict[str, Any] | None = None


def build_service_filter(preference: str) -> dict[str, Any] | None:
    return resolve_article_search_context(preference).retrieval_filter


def resolve_article_search_context(preference: str) -> ArticleSearchContext:
    matched_service_names = resolve_service_names(preference)
    if matched_service_names:
        return ArticleSearchContext(
            query=preference,
            retrieval_filter=build_service_equals_filter(matched_service_names),
        )

    matched_topic_service_names = resolve_topic_service_names(preference)
    if matched_topic_service_names:
        return ArticleSearchContext(
            query=expand_query(preference, matched_topic_service_names),
            retrieval_filter=build_service_equals_filter(matched_topic_service_names),
        )

    return ArticleSearchContext(query=preference)


def resolve_service_names(preference: str) -> list[str]:
    for service_names, match_patterns in COMPILED_AWS_SERVICE_PATTERNS:
        if any(pattern.search(preference) for pattern in match_patterns):
            return service_names
    return []


def resolve_topic_service_names(preference: str) -> list[str]:
    matched_service_names: list[str] = []

    for _, service_names, match_patterns in COMPILED_AWS_TOPIC_PATTERNS:
        if any(pattern.search(preference) for pattern in match_patterns):
            matched_service_names.extend(service_names)

    return list(dict.fromkeys(
        service_name.strip()
        for service_name in matched_service_names
        if service_name.strip()
    ))


def expand_query(preference: str, service_names: list[str]) -> str:
    normalized_preference = preference.casefold()
    supplemental_terms = [
        service_name
        for service_name in service_names
        if service_name.casefold() not in normalized_preference
    ]
    if not supplemental_terms:
        return preference
    return f"{preference} {' '.join(supplemental_terms)}"


def build_service_equals_filter(service_names: list[str]) -> dict[str, Any]:
    filter_values = list(dict.fromkeys(
        value
        for service_name in service_names
        for value in (service_name, service_name.lower())
        if value.strip()
    ))
    filters = [
        {"equals": {"key": "service", "value": service_name}}
        for service_name in filter_values
    ]
    if len(filters) == 1:
        return filters[0]
    return {"orAll": filters}
