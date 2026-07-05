import json

import boto3

from app.config import get_settings
from app.dto.request import RecommendationRequest
from app.dto.response import RecommendationResponse


class AgentRuntimeClient:
    """
    AI Agent Client

    Bedrock Agent を呼び出すクライアントクラス
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = boto3.client(
            "bedrock-agentcore", region_name=self.settings.aws_region
        )

    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        response = self.client.invoke_agent_runtime(
            agentRuntimeArn=self.settings.agent_runtime_arn,
            qualifier=self.settings.agent_runtime_qualifier,
            contentType="application/json",
            accept="application/json",
            payload=request.model_dump_json().encode("utf-8"),
        )

        body = response["response"].read().decode("utf-8")
        return RecommendationResponse.model_validate(json.loads(body))
