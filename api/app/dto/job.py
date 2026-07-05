from typing import Literal

from pydantic import BaseModel

from app.dto.response import RecommendationResponse

JobStatus = Literal["pending", "running", "succeeded", "failed"]


class RecommendationJobAcceptedResponse(BaseModel):
    job_id: str
    status: Literal["pending"]


class RecommendationJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: RecommendationResponse | None = None
    error_message: str | None = None
