from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


PROMPTS_FILE = Path(__file__).resolve().parent.parent / "prompts" / "recommendation.yaml"


class RecommendationPrompts(BaseModel):
    system_prompt: str = Field(..., min_length=1)
    selection_prompt_template: str = Field(..., min_length=1)


@lru_cache
def load_recommendation_prompts() -> RecommendationPrompts:
    with PROMPTS_FILE.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return RecommendationPrompts.model_validate(data)
