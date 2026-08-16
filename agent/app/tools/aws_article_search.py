import re
from functools import lru_cache
from typing import Any

from strands import tool

from app.client.knowledge_base_client import KnowledgeBaseClient
from app.config.exclusion_rules import EXCLUSION_PATTERNS
from app.models.recommendation import RecommendationCandidate
from app.parsers.recommendation_candidate_parser import build_candidates
from app.resolvers.aws_service_filter_resolver import build_service_filter


@lru_cache
def get_knowledge_base_client() -> KnowledgeBaseClient:
    return KnowledgeBaseClient()


@tool(name="search_aws_articles")
def search_aws_articles(
    preference: str,
    number_of_results: int = 40,
) -> list[dict[str, Any]]:
    """
    Search AWS RSS articles, filtering by service metadata when a known AWS service is present.

    Args:
        preference: User preference or search query.
        number_of_results: Maximum number of retrieval results.
    """
    retrieval_filter = build_service_filter(preference)
    retrieval = get_knowledge_base_client().retrieve(
        query=preference,
        number_of_results=number_of_results,
        retrieval_filter=retrieval_filter,
    )
    candidates = build_article_candidates(retrieval.get("results", []))
    return [candidate.model_dump(mode="json") for candidate in candidates]


def build_article_candidates(results: list[dict[str, Any]]) -> list[RecommendationCandidate]:
    candidates = build_candidates(results)
    return apply_exclusion_tags(candidates)


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
