from strands import Agent
from strands.models import BedrockModel

from app.config.runtime_settings import get_settings
from app.models.recommendation import (
    RecommendationCandidate,
    RecommendationItem,
    RecommendationItemsPayload,
    RecommendationSelectionPayload,
)
from app.tools.aws_article_search import search_aws_articles

MAX_RECOMMENDATIONS = 5

SYSTEM_PROMPT = """
あなたは AWS 技術記事の推薦エージェント。
RSSフィード由来の記事を最大5件選ぶ。
候補取得には必ず `search_aws_articles` tool を使う。
候補が5件未満なら、ある分だけ返す。
tool が返していない記事、タイトル、doc_id、URLを作らない。
選定では次の優先順位を守る。
1. ユーザー嗜好に含まれる主要トピック、AWSサービス名、機能名、ユースケースに直接対応する記事を最優先する。
2. title や summary に具体サービス名、機能名、実装観点、設計観点、ベストプラクティスが明示される記事を優先する。
3. 同程度に関連する候補が複数ある場合、話題を広く浅く並べた roundup、weekly roundup、news、announcements、what's new、release notes より、単一テーマを深掘りした記事を優先する。
4. roundup や総まとめ記事を選ぶのは、他候補より明確にユーザー嗜好へ適合する場合だけに限定する。
5. ユーザー嗜好と直接関係しない記事は、候補数が足りなくても無理に選ばない。
各 reason では、記事のテーマ・扱う機能・得られる知見を踏まえて、なぜその記事がユーザー嗜好に合うかを具体的に説明する。
reason はタイトルの言い換えや「関連性が高い」だけで終わらせない。
reason は1-2文、日本語。
構造化出力以外は返さない。
""".strip()

SELECTION_PROMPT_TEMPLATE = """
次のユーザー嗜好に対して、RSSフィード由来の記事を最大5件選んでください。

ユーザー嗜好: {preference}

選定手順:
1. 最初に `search_aws_articles` tool を使い、`preference` にユーザー嗜好をそのまま渡して候補を取得する。
2. tool が返した候補について、ユーザー嗜好と直接一致する AWS サービス名、機能名、課題、ユースケースを確認する。
3. summary から具体性を確認する。実装、設計、検証、改善、導入、運用の知見がある候補を優先する。
4. `exclusion_tags` が付いた候補は原則選ばない。具体記事が不足し、なおかつユーザー嗜好への適合が明確に高い場合だけ例外的に選ぶ。
5. 直接一致する具体記事があるなら、総まとめ記事で枠を使わない。
6. 適合度が低い候補は選ばない。最大5件であり、5件必須ではない。

各 reason では、tool が返した候補の title や summary に含まれる具体要素を使って説明してください。
reason には、どの AWS サービス名、機能名、課題、ユースケースが一致したかを必ず含めてください。
""".strip()


class StrandsRecommendationAgent:
    def __init__(self) -> None:
        settings = get_settings()
        self.agent = Agent(
            model=BedrockModel(model_id=settings.model_id),
            system_prompt=SYSTEM_PROMPT,
            tools=[search_aws_articles],
            structured_output_model=RecommendationSelectionPayload,
        )

    def recommend(self, preference: str) -> RecommendationItemsPayload:
        selection = self._select_recommendations(preference)
        if selection is None:
            return self._no_results_response(preference)

        candidates = self._find_candidates(preference)
        if not candidates:
            return self._no_results_response(preference)

        return self._assemble_recommendation_items(preference, candidates, selection)

    def _select_recommendations(
        self, preference: str
    ) -> RecommendationSelectionPayload | None:
        """
        ユーザーの好みに基づいて、候補記事を取得し選定する。
        """
        result = self.agent(
            SELECTION_PROMPT_TEMPLATE.format(
                preference=preference,
            )
        )

        if result.structured_output is None:
            raise ValueError(
                "Strands agent did not return structured output")

        if isinstance(result.structured_output, RecommendationSelectionPayload):
            selection = result.structured_output
        else:
            selection = RecommendationSelectionPayload.model_validate(
                result.structured_output)

        return selection

    def _find_candidates(self, preference: str) -> list[RecommendationCandidate]:
        candidate_payloads = search_aws_articles(
            preference=preference,
            number_of_results=40,
        )
        return [
            RecommendationCandidate.model_validate(candidate_payload)
            for candidate_payload in candidate_payloads
        ]

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
