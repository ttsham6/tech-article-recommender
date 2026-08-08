from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import boto3

from app.cli import rss_convertor
from app.config import get_settings

RETENTION_DAYS = 7


def handler(event: dict[str, Any] | None, context: Any) -> dict[str, Any]:
    settings = get_settings()

    feed_url = settings.rss_feed_url
    article_category = settings.article_category
    date_token = datetime.now(timezone.utc).strftime("%Y%m%d")

    working_dir = Path(
        "/tmp") / f"rss-batch-{getattr(context, 'aws_request_id', 'local')}"
    rss_path = working_dir / "feed.xml"
    documents_dir = working_dir / "documents"
    working_dir.mkdir(parents=True, exist_ok=True)

    rss_path = fetch_rss(
        feed_url, rss_path, settings.request_timeout_seconds)

    convert_result = rss_convertor.convert_feed_to_documents(
        rss_path,
        documents_dir,
        article_category,
        url_check_timeout_seconds=settings.request_timeout_seconds,
    )

    article_documents = convert_result.documents

    uploaded_obj_keys = upload_documents_to_s3(
        article_documents, settings.kb_source_bucket, article_category, date_token)

    deleted_obj_keys = delete_expired_documents(
        settings.kb_source_bucket,
        article_category,
        date_token,
    )

    ingestion_job = start_kb_sync(
        settings.knowledge_base_id,
        settings.data_source_id,
        article_category,
    )

    return {
        "feed_url": feed_url,
        "article_category": article_category,
        "bucket": settings.kb_source_bucket,
        "generated_articles": len(article_documents),
        "skipped_invalid_urls": convert_result.skipped_invalid_urls,
        "uploaded_objects": len(uploaded_obj_keys),
        "uploaded_keys": uploaded_obj_keys,
        "deleted_objects": len(deleted_obj_keys),
        "deleted_keys": deleted_obj_keys,
        "ingestion_job": ingestion_job,
    }


def fetch_rss(feed_url: str, output_path: Path, timeout_seconds: int) -> Path:
    """
    RSS feed を取得し、指定されたoutput_path に保存する。"""
    request = Request(
        feed_url,
        headers={
            "User-Agent": "tech-article-recommender-batch/1.0",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
    )

    with urlopen(request, timeout=timeout_seconds) as response:
        output_path.write_bytes(response.read())

    return output_path
def upload_documents_to_s3(
    article_documents: list[rss_convertor.ArticleDocument],
    bucket_name: str,
    article_category: str,
    date_token: str,
) -> list[str]:
    """
    Feed から生成された記事ファイルを S3 にアップロードする。
    """
    settings = get_settings()
    s3 = boto3.client("s3", region_name=settings.aws_region)
    uploaded_keys: list[str] = []

    for document in article_documents:
        for file_obj in [document.article, document.metadata]:
            object_key = f"{article_category}/{date_token}/{file_obj.path.name}"
            s3.upload_file(
                str(file_obj.path),
                bucket_name,
                object_key,
                ExtraArgs={"ContentType": file_obj.content_type},
            )
            uploaded_keys.append(object_key)

    return uploaded_keys


def delete_expired_documents(bucket_name: str, article_category: str, date_token: str) -> list[str]:
    """
    S3 に保存されている記事ファイルのうち、保持期間を過ぎたものを削除する。
    """
    settings = get_settings()
    s3 = boto3.client("s3", region_name=settings.aws_region)
    deleted_keys: list[str] = []

    keep_from = (
        datetime.strptime(date_token, "%Y%m%d").replace(tzinfo=timezone.utc)
        - timedelta(days=RETENTION_DAYS - 1)
    ).strftime("%Y%m%d")

    paginator = s3.get_paginator("list_objects_v2")
    for response in paginator.paginate(
        Bucket=bucket_name,
        Prefix=f"{article_category}/",
    ):
        expired_objects = []

        for obj in response.get("Contents", []):
            key = obj["Key"]
            parts = key.split("/", 2)
            if len(parts) < 3:
                continue

            key_date_token = parts[1]
            if key_date_token < keep_from:
                expired_objects.append({"Key": key})
                deleted_keys.append(key)

        if expired_objects:
            s3.delete_objects(
                Bucket=bucket_name,
                Delete={"Objects": expired_objects},
            )

    return deleted_keys


def start_kb_sync(knowledge_base_id: str, data_source_id: str, article_category: str) -> dict[str, str]:
    settings = get_settings()
    bedrock = boto3.client("bedrock-agent", region_name=settings.aws_region)
    response = bedrock.start_ingestion_job(
        knowledgeBaseId=knowledge_base_id,
        dataSourceId=data_source_id,
        description=f"RSS sync for {article_category}",
    )
    job = response["ingestionJob"]
    return {
        "ingestion_job_id": job["ingestionJobId"],
        "status": job["status"],
    }


if __name__ == "__main__":
    print(json.dumps(handler({}, None), ensure_ascii=False, indent=2))
