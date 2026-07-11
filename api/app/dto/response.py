from pydantic import BaseModel, HttpUrl


class RecommendationItem(BaseModel):
    title: str
    url: HttpUrl
    reason: str


class RecommendationResponse(BaseModel):
    items: list[RecommendationItem]
