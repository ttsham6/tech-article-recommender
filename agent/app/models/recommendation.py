from pydantic import BaseModel, Field, HttpUrl


class RecommendationRequest(BaseModel):
    preference: str = Field(..., min_length=1,
                            max_length=500, description="User preference")


class RecommendationItem(BaseModel):
    title: str
    url: HttpUrl
    reason: str


class RecommendationItemsPayload(BaseModel):
    items: list[RecommendationItem]


class RecommendationCandidate(BaseModel):
    doc_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    url: HttpUrl


class RecommendationSelectionItem(BaseModel):
    doc_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class RecommendationSelectionPayload(BaseModel):
    items: list[RecommendationSelectionItem]


class RecommendationResponse(BaseModel):
    items: list[RecommendationItem]
