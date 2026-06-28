from pydantic import BaseModel, Field, HttpUrl


class RecommendationRequest(BaseModel):
    preference: str = Field(..., min_length=1, max_length=500, description="User preference")


class RecommendationItem(BaseModel):
    title: str
    url: HttpUrl
    reason: str


class RecommendationItemsPayload(BaseModel):
    items: list[RecommendationItem]


class RecommendationResponse(BaseModel):
    items: list[RecommendationItem]
    knowledge_base_id: str
