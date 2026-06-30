from typing import Any

import boto3

from app.config import get_settings


class KnowledgeBaseClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.knowledge_base_id:
            raise ValueError("BEDROCK_KNOWLEDGE_BASE_ID is not set")
        self.client = boto3.client("bedrock-agent-runtime", region_name=self.settings.aws_region)

    def retrieve(self, query: str, number_of_results: int = 8) -> dict[str, Any]:
        response = self.client.retrieve(
            knowledgeBaseId=self.settings.knowledge_base_id,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": number_of_results,
                }
            },
        )
        return {
            "results": [self._serialize_result(item) for item in response.get("retrievalResults", [])],
        }

    @staticmethod
    def _serialize_result(item: dict[str, Any]) -> dict[str, Any]:
        location = item.get("location", {})
        content = item.get("content", {})

        return {
            "text": content.get("text", ""),
            "score": item.get("score"),
            "metadata": item.get("metadata", {}),
            "location": location,
        }
