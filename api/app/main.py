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
        handle_recommendation_job(event)
        return {"status": "accepted"}
    return http_handler(event, context)
