from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from app.models.recommendation import RecommendationCandidate

PROMPTS_FILE = Path(__file__).resolve().parent / "recommendation.yaml"


class RecommendationPrompts(BaseModel):
    system_prompt: str = Field(..., min_length=1)
    selection_prompt_template: str = Field(..., min_length=1)


@lru_cache
def load_recommendation_prompts() -> RecommendationPrompts:
    with PROMPTS_FILE.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return RecommendationPrompts.model_validate(data)


def format_candidate_prompt(candidate: RecommendationCandidate) -> str:
    lines = [
        f"- doc_id: {candidate.doc_id}",
        f"  title: {candidate.title}",
        f"  url: {candidate.url}",
    ]
    if candidate.summary:
        lines.append(f"  summary: {candidate.summary}")
    return "\n".join(lines)
