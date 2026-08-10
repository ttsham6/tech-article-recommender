import re
from typing import Any, cast

from pydantic import HttpUrl
from strands import Agent
from strands.models import BedrockModel

from app.config import get_settings
from app.models.recommendation import (
    RecommendationCandidate,
    RecommendationItem,
    RecommendationItemsPayload,
    RecommendationSelectionPayload,
)
from app.services.knowledge_base_client import KnowledgeBaseClient
from app.services.prompt_loader import load_recommendation_prompts

URL_LINE_PATTERN = re.compile(r"(?:^|[\s(])(?P<url>https?://[^\s)>\]]+)", re.MULTILINE)
TITLE_LINE_PATTERN = re.compile(r"^#\s+(?P<title>.+)$", re.MULTILINE)


class StrandsRecommendationAgent:
    def __init__(self) -> None:
        settings = get_settings()
        prompts = load_recommendation_prompts()
        self.knowledge_base_client = KnowledgeBaseClient()
        self.selection_prompt_template = prompts.selection_prompt_template
        self.agent = Agent(
            model=BedrockModel(model_id=settings.model_id),
            system_prompt=prompts.system_prompt,
            structured_output_model=RecommendationSelectionPayload,
        )

    def recommend(self, preference: str) -> RecommendationItemsPayload:
        retrieval = self.knowledge_base_client.retrieve(
            query=preference, number_of_results=12)
        candidates = self._build_candidates(retrieval.get("results", []))
        if not candidates:
            return self._fallback_response(preference)

        if len(candidates) <= 3:
            return self._merge_with_fallback_items(
                preference=preference,
                items=[
                    RecommendationItem(
                        title=candidate.title,
                        url=candidate.url,
                        reason=self._fallback_reason(preference, candidate.title),
                    )
                    for candidate in candidates
                ],
            )

        candidate_prompt = "\n".join(
            f"- doc_id: {candidate.doc_id}\n  title: {candidate.title}\n  url: {candidate.url}"
            for candidate in candidates
        )
        try:
            result = self.agent(
                self.selection_prompt_template.format(
                    preference=preference,
                    candidates=candidate_prompt,
                )
            )
        except Exception:
            return self._fallback_from_candidates(preference, candidates)

        try:
            if result.structured_output is None:
                raise ValueError("Strands agent did not return structured output")

            if isinstance(result.structured_output, RecommendationSelectionPayload):
                selection = result.structured_output
            else:
                selection = RecommendationSelectionPayload.model_validate(
                    result.structured_output)
        except Exception:
            return self._fallback_from_candidates(preference, candidates)

        candidate_map = {
            candidate.doc_id: candidate for candidate in candidates}
        items: list[RecommendationItem] = []
        used_doc_ids: set[str] = set()
        for picked in selection.items:
            candidate = candidate_map.get(picked.doc_id)
            if candidate is None or picked.doc_id in used_doc_ids:
                continue
            used_doc_ids.add(picked.doc_id)
            items.append(
                RecommendationItem(
                    title=candidate.title,
                    url=candidate.url,
                    reason=picked.reason,
                )
            )

        for candidate in candidates:
            if len(items) >= 3:
                break
            if candidate.doc_id in used_doc_ids:
                continue
            items.append(
                RecommendationItem(
                    title=candidate.title,
                    url=candidate.url,
                    reason=self._fallback_reason(preference, candidate.title),
                )
            )

        return RecommendationItemsPayload(items=items[:3])

    def _build_candidates(self, results: list[dict[str, Any]]) -> list[RecommendationCandidate]:
        candidates_by_doc_id: dict[str, RecommendationCandidate] = {}
        for result in results:
            metadata = result.get("metadata") or {}
            text = result.get("text", "")

            doc_id = self._first_non_empty(metadata.get("doc_id"))
            title = self._first_non_empty(
                metadata.get("title"), self._extract_title(text))
            url = self._first_non_empty(
                metadata.get("url"), self._extract_url(text))

            if not doc_id or not title or not url or doc_id in candidates_by_doc_id:
                continue

            candidates_by_doc_id[doc_id] = RecommendationCandidate(
                doc_id=doc_id,
                title=title,
                url=cast(HttpUrl, url),
            )

        return list(candidates_by_doc_id.values())

    @staticmethod
    def _extract_url(text: str) -> str | None:
        match = URL_LINE_PATTERN.search(text)
        if not match:
            return None
        return match.group("url").strip().rstrip(".,);]")

    @staticmethod
    def _extract_title(text: str) -> str | None:
        match = TITLE_LINE_PATTERN.search(text)
        if match:
            return match.group("title").strip()

        for line in text.splitlines():
            stripped = line.strip().lstrip("-#* ").strip()
            if stripped and not stripped.startswith("URL:") and not stripped.startswith("http"):
                return stripped[:200]
        return None

    @staticmethod
    def _first_non_empty(*values: Any) -> str | None:
        for value in values:
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _fallback_from_candidates(
        self, preference: str, candidates: list[RecommendationCandidate]
    ) -> RecommendationItemsPayload:
        return self._merge_with_fallback_items(
            preference=preference,
            items=[
                RecommendationItem(
                    title=candidate.title,
                    url=candidate.url,
                    reason=self._fallback_reason(preference, candidate.title),
                )
                for candidate in candidates[:3]
            ],
        )

    def _fallback_response(self, preference: str) -> RecommendationItemsPayload:
        if "lambda" in preference.lower():
            items = [
                RecommendationItem(
                    title="AWS Lambda Developer Guide",
                    url=cast(HttpUrl, "https://docs.aws.amazon.com/lambda/latest/dg/welcome.html"),
                    reason=self._fallback_reason(preference, "AWS Lambda Developer Guide"),
                ),
                RecommendationItem(
                    title="AWS Lambda Best Practices",
                    url=cast(HttpUrl, "https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html"),
                    reason=self._fallback_reason(preference, "AWS Lambda Best Practices"),
                ),
                RecommendationItem(
                    title="AWS Architecture Center",
                    url=cast(HttpUrl, "https://aws.amazon.com/architecture/"),
                    reason=self._fallback_reason(preference, "AWS Architecture Center"),
                ),
            ]
        elif "bedrock" in preference.lower() or "agent" in preference.lower():
            items = [
                RecommendationItem(
                    title="Amazon Bedrock User Guide",
                    url=cast(HttpUrl, "https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html"),
                    reason=self._fallback_reason(preference, "Amazon Bedrock User Guide"),
                ),
                RecommendationItem(
                    title="Amazon Bedrock Agents",
                    url=cast(HttpUrl, "https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html"),
                    reason=self._fallback_reason(preference, "Amazon Bedrock Agents"),
                ),
                RecommendationItem(
                    title="AWS Architecture Center",
                    url=cast(HttpUrl, "https://aws.amazon.com/architecture/"),
                    reason=self._fallback_reason(preference, "AWS Architecture Center"),
                ),
            ]
        else:
            items = [
                RecommendationItem(
                    title="AWS Architecture Center",
                    url=cast(HttpUrl, "https://aws.amazon.com/architecture/"),
                    reason=self._fallback_reason(preference, "AWS Architecture Center"),
                ),
                RecommendationItem(
                    title="AWS Well-Architected Framework",
                    url=cast(HttpUrl, "https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html"),
                    reason=self._fallback_reason(preference, "AWS Well-Architected Framework"),
                ),
                RecommendationItem(
                    title="Amazon Bedrock User Guide",
                    url=cast(HttpUrl, "https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html"),
                    reason=self._fallback_reason(preference, "Amazon Bedrock User Guide"),
                ),
            ]

        return RecommendationItemsPayload(items=items)

    def _merge_with_fallback_items(
        self,
        preference: str,
        items: list[RecommendationItem],
    ) -> RecommendationItemsPayload:
        merged_items = list(items)
        used_urls = {str(item.url) for item in merged_items}

        for fallback_item in self._fallback_response(preference).items:
            if len(merged_items) >= 3:
                break
            if str(fallback_item.url) in used_urls:
                continue
            merged_items.append(fallback_item)
            used_urls.add(str(fallback_item.url))

        return RecommendationItemsPayload(items=merged_items[:3])

    @staticmethod
    def _fallback_reason(preference: str, title: str) -> str:
        return f"'{preference}' に近い AWS 技術情報として安定参照しやすい記事: {title}"
