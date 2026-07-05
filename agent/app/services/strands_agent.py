from strands import Agent
from strands.models import BedrockModel
from strands.tools.decorator import tool

from app.config import get_settings
from app.models.recommendation import RecommendationItemsPayload
from app.services.knowledge_base_client import KnowledgeBaseClient


class RecommendationTools:
    def __init__(self) -> None:
        self.knowledge_base_client = KnowledgeBaseClient()

    @tool
    def retrieve_kb(self, query: str, number_of_results: int = 8) -> dict:
        """
        Retrieve relevant context from the Bedrock knowledge base.

        Args:
            query: Search query for the knowledge base.
            number_of_results: Maximum number of chunks to retrieve.
        """
        return self.knowledge_base_client.retrieve(query=query, number_of_results=number_of_results)


class StrandsRecommendationAgent:
    def __init__(self) -> None:
        settings = get_settings()
        self.tools = RecommendationTools()
        self.agent = Agent(
            model=BedrockModel(model_id=settings.model_id),
            system_prompt=(
                "You recommend exactly 3 AWS-related technical articles.\n"
                "Use the retrieve_kb tool before answering whenever you need source context.\n"
                "Prefer AWS official blog, AWS documentation, or high-signal engineering writeups.\n"
                "Every URL must be directly usable.\n"
                "Every reason must explain why the article matches the user preference.\n"
                "Return only the structured output."
            ),
            tools=[self.tools.retrieve_kb],
            structured_output_model=RecommendationItemsPayload,
        )

    def recommend(self, preference: str) -> RecommendationItemsPayload:
        result = self.agent(
            (
                "Recommend exactly 3 AWS-related technical articles for this user preference.\n"
                f"User preference: {preference}"
            )
        )

        if result.structured_output is None:
            raise ValueError("Strands agent did not return structured output")

        if isinstance(result.structured_output, RecommendationItemsPayload):
            return result.structured_output

        return RecommendationItemsPayload.model_validate(result.structured_output)
