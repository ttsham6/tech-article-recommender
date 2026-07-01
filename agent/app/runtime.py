from bedrock_agentcore.runtime import BedrockAgentCoreApp

from app.models.recommendation import RecommendationRequest
from app.services.recommendation_service import RecommendationService

app = BedrockAgentCoreApp()
service = RecommendationService()


@app.entrypoint
def invoke(payload, context=None):
    req = RecommendationRequest.model_validate(payload)
    res = service.recommend(req)
    return res.model_dump(mode="json")
