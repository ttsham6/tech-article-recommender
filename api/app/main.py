from typing import Any

from fastapi import FastAPI
from mangum import Mangum

from app.router.health import router as health_router
from app.router.recommendations import router as recommendations_router
from app.worker import handle_recommendation_job

app = FastAPI(title="Tech Article Recommender API")
app.include_router(health_router)
app.include_router(recommendations_router)

http_handler = Mangum(app)


def handler(event: dict[str, Any], context: Any) -> Any:
    if event.get("jobType") == "recommendation":
        # Self-invoked async worker event
        return handle_recommendation_job_event(event)
    else:
        # HTTP request from API Gateway
        return handle_http_event(event, context)


def handle_http_event(event: dict[str, Any], context: Any) -> Any:
    return http_handler(event, context)


def handle_recommendation_job_event(event: dict[str, Any]) -> dict[str, str]:
    handle_recommendation_job(event)
    return {"status": "accepted"}
