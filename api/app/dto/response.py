from pydantic import BaseModel, ConfigDict, HttpUrl


class RecommendationItem(BaseModel):
    title: str
    url: HttpUrl
    reason: str


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    items: list[RecommendationItem]
    message: str | None = None
    knowledge_base_id: str | None = None
