from pydantic import BaseModel, ConfigDict, HttpUrl


class RecommendationItem(BaseModel):
    title: str
    url: HttpUrl
    reason: str


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    items: list[RecommendationItem]
    knowledge_base_id: str | None = None
