import re

# AWS サービス名の辞書
AWS_SERVICE_DEFINITIONS = {
    "sqs": [
        "SQS",
        "Amazon SQS",
        "Amazon Simple Queue Service",
        "Amazon Simple Queue Service (SQS)",
    ],
    "lambda": [
        "Lambda",
        "AWS Lambda",
    ],
    "bedrock": [
        "Bedrock",
        "Amazon Bedrock",
    ],
    "dynamodb": [
        "DynamoDB",
        "Amazon DynamoDB",
    ],
    "s3": [
        "S3",
        "Amazon S3",
        "Amazon Simple Storage Service",
        "Amazon Simple Storage Service (S3)",
    ],
    "ecs": [
        "ECS",
        "Amazon ECS",
        "Amazon Elastic Container Service",
    ],
    "eks": [
        "EKS",
        "Amazon EKS",
        "Amazon Elastic Kubernetes Service",
    ],
    "fargate": [
        "Fargate",
        "AWS Fargate",
    ],
    "ecr": [
        "ECR",
        "Amazon ECR",
        "Amazon Elastic Container Registry",
    ],
    "ec2": [
        "EC2",
        "Amazon EC2",
        "Amazon Elastic Compute Cloud",
    ],
    "vpc": [
        "VPC",
        "Amazon VPC",
        "Amazon Virtual Private Cloud",
    ],
    "rds": [
        "RDS",
        "Amazon RDS",
        "Amazon Relational Database Service",
    ],
    "aurora": [
        "Aurora",
        "Amazon Aurora",
        "Amazon Aurora Database",
    ],
}

AWS_TOPIC_DEFINITIONS = {
    "containers": {
        "keywords": [
            "container",
            "containers",
            "container service",
            "container services",
            "docker",
            "kubernetes",
            "k8s",
            "コンテナ",
            "コンテナサービス",
            "コンテナ技術",
            "コンテナ実行",
            "コンテナ運用",
            "kubernetes運用",
            "オーケストレーション",
        ],
        "service_keys": ["ecs", "eks", "fargate", "ecr"],
    },
}

ServicePatternSet = tuple[list[str], list[re.Pattern[str]]]
TopicPatternSet = tuple[str, list[str], list[re.Pattern[str]]]


def compile_service_name_pattern(service_name: str) -> re.Pattern[str]:
    escaped_tokens = [
        re.escape(token)
        for token in service_name.split()
    ]
    pattern = r"\s+".join(escaped_tokens)
    return re.compile(
        rf"(?<![A-Za-z0-9]){pattern}(?![A-Za-z0-9])",
        re.IGNORECASE,
    )


COMPILED_AWS_SERVICE_PATTERNS: list[ServicePatternSet] = [
    (
        service_names,
        [compile_service_name_pattern(name) for name in service_names],
    )
    for service_names in (
        list(dict.fromkeys(
            str(service_name).strip()
            for service_name in names
            if str(service_name).strip()
        ))
        for names in AWS_SERVICE_DEFINITIONS.values()
        if isinstance(names, list)
    )
    if service_names
]

COMPILED_AWS_TOPIC_PATTERNS: list[TopicPatternSet] = [
    (
        topic_name,
        list(dict.fromkeys(
            service_name
            for service_key in definition.get("service_keys", [])
            for service_name in AWS_SERVICE_DEFINITIONS.get(service_key, [])
            if isinstance(service_name, str) and service_name.strip()
        )),
        [
            compile_service_name_pattern(keyword)
            for keyword in definition.get("keywords", [])
            if isinstance(keyword, str) and keyword.strip()
        ],
    )
    for topic_name, definition in AWS_TOPIC_DEFINITIONS.items()
    if isinstance(definition, dict)
]
