from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast

import boto3

from app.config import get_settings
from app.dto.job import RecommendationJobResponse

PENDING_TTL = timedelta(hours=1)
SUCCEEDED_TTL = timedelta(days=1)
FAILED_TTL = timedelta(days=3)


class JobStoreClient:
    def __init__(self) -> None:
        self.settings = get_settings()

        dynamodb_resource = cast(
            Any,
            boto3.resource(
                "dynamodb",
                region_name=self.settings.aws_region,
            ),
        )
        self.table = dynamodb_resource.Table(self.settings.jobs_table_name)

    def create_job(self, *, job_id: str, request_payload: dict[str, Any]) -> None:
        now = datetime.now(UTC)
        self.table.put_item(
            Item={
                "jobId": job_id,
                "status": "pending",
                "requestPayload": request_payload,
                "createdAt": now.isoformat(),
                "updatedAt": now.isoformat(),
                "expiresAt": self._to_epoch(now + PENDING_TTL),
            }
        )

    def mark_running(self, job_id: str) -> None:
        now = datetime.now(UTC).isoformat()
        self.table.update_item(
            Key={"jobId": job_id},
            UpdateExpression="SET #status = :status, updatedAt = :updated_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "running",
                ":updated_at": now,
            },
        )

    def mark_succeeded(self, job_id: str, result: dict[str, Any]) -> None:
        now = datetime.now(UTC)
        self.table.update_item(
            Key={"jobId": job_id},
            UpdateExpression=(
                "SET #status = :status, #result = :result, updatedAt = :updated_at, "
                "expiresAt = :expires_at REMOVE errorMessage"
            ),
            ExpressionAttributeNames={
                "#status": "status",
                "#result": "result",
            },
            ExpressionAttributeValues={
                ":status": "succeeded",
                ":result": result,
                ":updated_at": now.isoformat(),
                ":expires_at": self._to_epoch(now + SUCCEEDED_TTL),
            },
        )

    def mark_failed(self, job_id: str, error_message: str) -> None:
        now = datetime.now(UTC)
        self.table.update_item(
            Key={"jobId": job_id},
            UpdateExpression=(
                "SET #status = :status, errorMessage = :error_message, updatedAt = :updated_at, "
                "expiresAt = :expires_at"
            ),
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "failed",
                ":error_message": error_message,
                ":updated_at": now.isoformat(),
                ":expires_at": self._to_epoch(now + FAILED_TTL),
            },
        )

    def get_job(self, job_id: str) -> RecommendationJobResponse | None:
        response = self.table.get_item(Key={"jobId": job_id})
        item = response.get("Item")
        if item is None:
            return None

        return RecommendationJobResponse(
            job_id=item["jobId"],
            status=item["status"],
            result=item.get("result"),
            error_message=item.get("errorMessage"),
        )

    @staticmethod
    def _to_epoch(value: datetime) -> int:
        return int(value.timestamp())
