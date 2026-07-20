from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    aws_region: str = Field(default="ap-northeast-1", alias="AWS_REGION")
    kb_source_bucket: str = Field(default="", alias="KB_SOURCE_BUCKET")
    knowledge_base_id: str = Field(default="", alias="KNOWLEDGE_BASE_ID")
    data_source_id: str = Field(default="", alias="DATA_SOURCE_ID")
    article_category: str = Field(default="", alias="ARTICLE_CATEGORY")
    rss_feed_url: str = Field(default="", alias="RSS_FEED_URL")
    request_timeout_seconds: int = Field(default=30, alias="REQUEST_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
