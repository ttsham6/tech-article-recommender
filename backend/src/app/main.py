import argparse
import json

from app.models.recommendation import RecommendationRequest
from app.services.recommendation_service import RecommendationService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Strands recommendation agent")
    parser.add_argument("preference", help="User preference for article recommendation")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    payload = RecommendationRequest(preference=args.preference)
    service = RecommendationService()
    response = service.recommend(payload)
    print(json.dumps(response.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
