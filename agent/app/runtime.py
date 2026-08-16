from bedrock_agentcore.runtime import BedrockAgentCoreApp

from app.agents.recommendation_agent import StrandsRecommendationAgent
from app.models.recommendation import RecommendationRequest, RecommendationResponse

app = BedrockAgentCoreApp()
agent = StrandsRecommendationAgent()


def recommend(payload: RecommendationRequest) -> RecommendationResponse:
    try:
        response = agent.recommend(payload.preference)
    except Exception:
        response = agent._no_results_response(payload.preference)
    return RecommendationResponse(
        items=response.items,
        message=response.message,
    )


@app.entrypoint
def invoke(payload, context=None):
    req = RecommendationRequest.model_validate(payload)
    res = recommend(req)
    return res.model_dump(mode="json")
