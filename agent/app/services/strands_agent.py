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

TITLE_LINE_PATTERN = re.compile(r"^#\s+(?P<title>.+)$", re.MULTILINE)
SUMMARY_SECTION_PATTERN = re.compile(
    r"^##\s+Summary\s*(?P<summary>.*?)(?:\n##\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)
MAX_RECOMMENDATIONS = 5


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
            query=preference, number_of_results=20)
        candidates = self._build_candidates(retrieval.get("results", []))
        if not candidates:
            return self._no_results_response(preference)

        candidate_prompt = "\n".join(
            self._format_candidate_prompt(candidate)
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
                raise ValueError(
                    "Strands agent did not return structured output")

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
            if len(items) >= MAX_RECOMMENDATIONS:
                break

        for candidate in candidates:
            if len(items) >= MAX_RECOMMENDATIONS:
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

        return RecommendationItemsPayload(items=items[:MAX_RECOMMENDATIONS])

    def _build_candidates(self, results: list[dict[str, Any]]) -> list[RecommendationCandidate]:
        candidates_by_doc_id: dict[str, RecommendationCandidate] = {}
        for result in results:
            metadata = result.get("metadata") or {}
            text = result.get("text", "")
            if not self._is_rss_candidate(metadata):
                continue

            doc_id = self._first_non_empty(metadata.get("doc_id"))
            title = self._first_non_empty(
                metadata.get("title"), self._extract_title(text))
            url = self._first_non_empty(metadata.get("url"))

            if not doc_id or not title or not url or doc_id in candidates_by_doc_id:
                continue

            candidates_by_doc_id[doc_id] = RecommendationCandidate(
                doc_id=doc_id,
                title=title,
                url=cast(HttpUrl, url),
                summary=self._extract_summary(text),
            )

        return list(candidates_by_doc_id.values())

    @staticmethod
    def _is_rss_candidate(metadata: dict[str, Any]) -> bool:
        return all(
            isinstance(metadata.get(key), str) and metadata.get(key).strip()
            for key in ("source", "doc_id", "url")
        )

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
    def _extract_summary(text: str) -> str | None:
        match = SUMMARY_SECTION_PATTERN.search(text)
        if not match:
            return None
        summary = re.sub(r"\s+", " ", match.group("summary")).strip()
        if not summary:
            return None
        return summary[:400]

    @staticmethod
    def _first_non_empty(*values: Any) -> str | None:
        for value in values:
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _format_candidate_prompt(candidate: RecommendationCandidate) -> str:
        lines = [
            f"- doc_id: {candidate.doc_id}",
            f"  title: {candidate.title}",
            f"  url: {candidate.url}",
        ]
        if candidate.summary:
            lines.append(f"  summary: {candidate.summary}")
        return "\n".join(lines)

    def _fallback_from_candidates(
        self, preference: str, candidates: list[RecommendationCandidate]
    ) -> RecommendationItemsPayload:
        return RecommendationItemsPayload(
            items=[
                RecommendationItem(
                    title=candidate.title,
                    url=candidate.url,
                    reason=self._fallback_reason(preference, candidate.title),
                )
                for candidate in candidates[:MAX_RECOMMENDATIONS]
            ],
        )

    def _no_results_response(self, preference: str) -> RecommendationItemsPayload:
        return RecommendationItemsPayload(
            items=[],
            message="AWSの記事では一致する記事が見つかりませんでした。検索語を変えて再度お試しください。",
        )

    @staticmethod
    def _fallback_reason(preference: str, title: str) -> str:
        return f"「{preference}」との関連性が高いRSS記事として「{title}」を選定。"
