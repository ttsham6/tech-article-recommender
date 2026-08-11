from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    preference: str = Field(..., min_length=1, max_length=200)
