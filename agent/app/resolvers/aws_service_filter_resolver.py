from typing import Any

from app.config.aws_service_definitions import COMPILED_AWS_SERVICE_PATTERNS


def build_service_filter(preference: str) -> dict[str, Any] | None:
    for service_names, match_patterns in COMPILED_AWS_SERVICE_PATTERNS:
        if any(pattern.search(preference) for pattern in match_patterns):
            return build_service_equals_filter(service_names)
    return None


def build_service_equals_filter(service_names: list[str]) -> dict[str, Any]:
    filters = [
        {"equals": {"key": "service", "value": service_name}}
        for service_name in service_names
    ]
    if len(filters) == 1:
        return filters[0]
    return {"orAll": filters}
