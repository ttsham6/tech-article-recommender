from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import boto3

from app.cli import rss_convertor
from app.config import get_settings


def handler(event: dict[str, Any] | None, context: Any) -> dict[str, Any]:
    settings = get_settings()

    feed_url = settings.rss_feed_url
    article_category = settings.article_category

    working_dir = Path(
        "/tmp") / f"rss-batch-{getattr(context, 'aws_request_id', 'local')}"
    rss_path = working_dir / "feed.xml"
    documents_dir = working_dir / "documents"
    working_dir.mkdir(parents=True, exist_ok=True)

    rss_path = fetch_rss(
        feed_url, rss_path, settings.request_timeout_seconds)

    article_documents = rss_convertor.convert_feed_to_documents(
        rss_path, documents_dir, article_category)

    uploaded_obj_keys = upload_documents_to_s3(
        article_documents, settings.kb_source_bucket, article_category)

    return {
        "feed_url": feed_url,
        "article_category": article_category,
        "bucket": settings.kb_source_bucket,
        "generated_articles": len(article_documents),
        "uploaded_objects": len(uploaded_obj_keys),
        "uploaded_keys": uploaded_obj_keys,
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
) -> list[str]:
    """
    Feed から生成された記事ファイルを S3 にアップロードする。
    """
    settings = get_settings()
    s3 = boto3.client("s3", region_name=settings.aws_region)
    uploaded_keys: list[str] = []

    date_token = datetime.now(timezone.utc).strftime("%Y%m%d")

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


if __name__ == "__main__":
    print(json.dumps(handler({}, None), ensure_ascii=False, indent=2))
