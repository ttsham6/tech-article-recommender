import json
import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, status

from app.client.job_store_client import JobStoreClient
from app.config import get_settings
from app.dependencies.auth import verify_authorization
from app.dto.job import RecommendationJobAcceptedResponse, RecommendationJobResponse
from app.dto.request import RecommendationRequest

router = APIRouter(tags=["recommendations"])


@router.post(
    "/recommendations",
    response_model=RecommendationJobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def recommend(
    request: RecommendationRequest,
    _: None = Depends(verify_authorization),
) -> RecommendationJobAcceptedResponse:
    job_id = str(uuid.uuid4())
    request_payload = request.model_dump(mode="json")

    # job 保存
    job_store_client = JobStoreClient()
    job_store_client.create_job(job_id=job_id, request_payload=request_payload)

    try:
        invoke_self_async_recommendation_worker(
            job_id=job_id,
            request_payload=request_payload,
        )
    except (BotoCoreError, ClientError) as exc:
        job_store_client.mark_failed(job_id, str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to start recommendation job",
        ) from exc

    return RecommendationJobAcceptedResponse(job_id=job_id, status="pending")


@router.get("/recommendations/{job_id}", response_model=RecommendationJobResponse)
async def get_recommendation_job(
    job_id: str,
    _: None = Depends(verify_authorization),
) -> RecommendationJobResponse:
    job_store = JobStoreClient()
    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation job not found",
        )
    return job


def invoke_self_async_recommendation_worker(
    job_id: str,
    request_payload: dict,
) -> None:
    """
    自身の Lambda 関数を非同期で呼び出して、レコメンドジョブを処理する
    """
    settings = get_settings()
    worker_event = {
        "jobType": "recommendation",
        "jobId": job_id,
        "request": request_payload,
    }
    boto3.client("lambda", region_name=settings.aws_region).invoke(
        FunctionName=settings.self_async_worker_function_name,
        InvocationType="Event",
        Payload=json.dumps(worker_event).encode("utf-8"),
    )
