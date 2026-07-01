from app.config import get_settings
from app.models.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.strands_agent import StrandsRecommendationAgent


class RecommendationService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.agent = StrandsRecommendationAgent()

    def recommend(self, payload: RecommendationRequest) -> RecommendationResponse:
        response = self.agent.recommend(payload.preference)
        return RecommendationResponse(
            items=response.items,
            knowledge_base_id=self.settings.knowledge_base_id,
        )
