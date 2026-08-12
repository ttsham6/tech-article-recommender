import logging

from app.client.agent_runtime_client import AgentRuntimeClient
from app.client.job_store_client import JobStoreClient
from app.dto.request import RecommendationRequest

logger = logging.getLogger(__name__)


def handle_recommendation_job(event: dict) -> None:
    """
    Agnet Runtime を呼び出してレコメンド処理を行う
    """
    job_id = event["jobId"]
    request_payload = event["request"]

    job_store = JobStoreClient()
    agent_runtime_client = AgentRuntimeClient()

    try:
        job_store.mark_running(job_id)
        request = RecommendationRequest.model_validate(request_payload)
        result = agent_runtime_client.recommend(request)
        job_store.mark_succeeded(job_id, result.model_dump(mode="json"))
    except Exception as exc:
        logger.exception("Failed to process recommendation job",
                         extra={"jobId": job_id})
        job_store.mark_failed(job_id, str(exc))
        raise
