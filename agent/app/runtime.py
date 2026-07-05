from bedrock_agentcore.runtime import BedrockAgentCoreApp

from app.models.recommendation import RecommendationRequest
from app.services.recommendation_service import RecommendationService

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload, context=None):
    req = RecommendationRequest.model_validate(payload)
    service = RecommendationService()
    res = service.recommend(req)
    return res.model_dump(mode="json")
