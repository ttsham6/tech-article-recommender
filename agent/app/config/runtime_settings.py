from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    aws_region: str = "ap-northeast-1"
    model_id: str = Field(default="amazon.nova-lite-v1:0",
                          alias="BEDROCK_MODEL_ID")
    knowledge_base_id: str = Field(
        default="", alias="BEDROCK_KNOWLEDGE_BASE_ID")

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
