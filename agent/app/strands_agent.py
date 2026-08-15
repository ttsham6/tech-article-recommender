from strands import Agent
from strands.models import BedrockModel

from app.client.knowledge_base_client import KnowledgeBaseClient
from app.config import get_settings
from app.exclusion_rules import apply_exclusion_tags
from app.models.recommendation import (
    RecommendationCandidate,
    RecommendationItem,
    RecommendationItemsPayload,
    RecommendationSelectionPayload,
)
from app.parsers.recommendation_candidate_parser import build_candidates
from app.prompts.recommendation_prompt import (
    format_candidate_prompt,
    load_recommendation_prompts,
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
        candidates = self._find_candidates(preference)
        if not candidates:
            return self._no_results_response(preference)

        selection = self._select_recommendations(preference, candidates)
        if selection is None:
            return self._no_results_response(preference)

        return self._assemble_recommendation_items(preference, candidates, selection)

    def _find_candidates(self, preference: str) -> list[RecommendationCandidate]:
        retrieval = self.knowledge_base_client.retrieve(
            query=preference, number_of_results=40)
        candidates = build_candidates(retrieval.get("results", []))
        return apply_exclusion_tags(candidates)

    def _select_recommendations(
        self, preference: str, candidates: list[RecommendationCandidate]
    ) -> RecommendationSelectionPayload | None:
        """
        ユーザーの好みに基づいて、候補記事の中から最適な記事を選定する。
        """
        candidate_prompt = "\n".join(
            format_candidate_prompt(candidate)
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
            return None

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
            return None

        return selection

    def _assemble_recommendation_items(
        self,
        preference: str,
        candidates: list[RecommendationCandidate],
        selection: RecommendationSelectionPayload,
    ) -> RecommendationItemsPayload:
        """
        選定された記事の情報を整形し、最終的な記事リストを作成する。
        """
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

        if not items:
            return self._no_results_response(preference)

        return RecommendationItemsPayload(items=items[:MAX_RECOMMENDATIONS])

    def _no_results_response(self, preference: str) -> RecommendationItemsPayload:
        return RecommendationItemsPayload(
            items=[],
            message="AWSの記事では一致する記事が見つかりませんでした。検索語を変えて再度お試しください。",
        )
