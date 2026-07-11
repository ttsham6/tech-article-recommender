from app.models.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.strands_agent import StrandsRecommendationAgent


class RecommendationService:
    def __init__(self) -> None:
        self.agent = StrandsRecommendationAgent()

    def recommend(self, payload: RecommendationRequest) -> RecommendationResponse:
        response = self.agent.recommend(payload.preference)
        return RecommendationResponse(
            items=response.items,
        )
