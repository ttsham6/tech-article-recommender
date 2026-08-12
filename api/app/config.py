from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    aws_region: str = Field(default="ap-northeast-1", alias="AWS_REGION")
    agent_runtime_arn: str = Field(default="", alias="AGENT_RUNTIME_ARN")
    agent_runtime_qualifier: str = Field(default="tech_article_recommender_endpoint", alias="AGENT_RUNTIME_QUALIFIER")
    jobs_table_name: str = Field(default="", alias="JOBS_TABLE_NAME")
    self_async_worker_function_name: str = Field(default="", alias="SELF_ASYNC_WORKER_FUNCTION_NAME")

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
