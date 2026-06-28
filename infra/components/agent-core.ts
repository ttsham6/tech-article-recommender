import * as aws from "@pulumi/aws";
import * as pulumi from "@pulumi/pulumi";

const RUNTIME_NAME = "TechArticleRecommender";
const ARTIFACT_KEY = "strands-runtime.zip";

export interface AgentRuntimeArgs {
    knowledgeBaseArn: pulumi.Input<string>;
}

export class AgentRuntime extends pulumi.ComponentResource {
    public readonly executionRole: aws.iam.Role;
    public readonly artifactBucket: aws.s3.Bucket;

    constructor(
        name: string,
        args: AgentRuntimeArgs,
        opts?: pulumi.ComponentResourceOptions,
    ) {
        super("tech-article-recommender:agentcore:Runtime", name, args, opts);

        const region = aws.getRegionOutput({});
        const callerIdentity = aws.getCallerIdentityOutput({});

        this.executionRole = new aws.iam.Role(`${name}-execution-role`, {
            assumeRolePolicy: pulumi
                .all([region.region, callerIdentity.accountId])
                .apply(([regionName, accountId]) =>
                    JSON.stringify({
                        Version: "2012-10-17",
                        Statement: [
                            {
                                Sid: "AllowBedrockAgentCoreAssumeRole",
                                Effect: "Allow",
                                Principal: {
                                    Service: "bedrock-agentcore.amazonaws.com",
                                },
                                Action: "sts:AssumeRole",
                                Condition: {
                                    StringEquals: {
                                        "aws:SourceAccount": accountId,
                                    },
                                    ArnLike: {
                                        "aws:SourceArn": `arn:aws:bedrock-agentcore:${regionName}:${accountId}:*`,
                                    },
                                },
                            },
                        ],
                    }),
                ),
        }, { parent: this });

        new aws.iam.RolePolicy(`${name}-execution-policy`, {
            role: this.executionRole.id,
            policy: pulumi
                .all([region.region, callerIdentity.accountId, args.knowledgeBaseArn])
                .apply(([regionName, accountId, knowledgeBaseArn]) =>
                    JSON.stringify({
                        Version: "2012-10-17",
                        Statement: [
                            {
                                Sid: "BedrockModelInvocation",
                                Effect: "Allow",
                                Action: [
                                    "bedrock:InvokeModel",
                                    "bedrock:InvokeModelWithResponseStream",
                                ],
                                Resource: [
                                    "arn:aws:bedrock:*::foundation-model/*",
                                    "arn:aws:bedrock:*:*:inference-profile/*",
                                    "arn:aws:bedrock:*:*:application-inference-profile/*",
                                ],
                            },
                            {
                                Sid: "KnowledgeBaseRetrieve",
                                Effect: "Allow",
                                Action: [
                                    "bedrock:Retrieve",
                                    "bedrock:GetKnowledgeBase",
                                    "bedrock:ListKnowledgeBases",
                                ],
                                Resource: knowledgeBaseArn,
                            },
                            {
                                Sid: "EcrPublicTokenAccess",
                                Effect: "Allow",
                                Action: ["ecr-public:GetAuthorizationToken"],
                                Resource: "*",
                            },
                            {
                                Sid: "StsForEcrPublicPull",
                                Effect: "Allow",
                                Action: ["sts:GetServiceBearerToken"],
                                Resource: "*",
                            },
                            {
                                Sid: "XRayTracingAccess",
                                Effect: "Allow",
                                Action: [
                                    "xray:PutTraceSegments",
                                    "xray:PutTelemetryRecords",
                                    "xray:GetSamplingRules",
                                    "xray:GetSamplingTargets",
                                ],
                                Resource: "*",
                            },
                            {
                                Sid: "CloudWatchLogsGroup",
                                Effect: "Allow",
                                Action: ["logs:CreateLogGroup", "logs:DescribeLogStreams"],
                                Resource: `arn:aws:logs:${regionName}:${accountId}:log-group:/aws/bedrock-agentcore/runtimes/*`,
                            },
                            {
                                Sid: "CloudWatchLogsDescribeGroups",
                                Effect: "Allow",
                                Action: ["logs:DescribeLogGroups"],
                                Resource: `arn:aws:logs:${regionName}:${accountId}:log-group:*`,
                            },
                            {
                                Sid: "CloudWatchLogsStream",
                                Effect: "Allow",
                                Action: ["logs:CreateLogStream", "logs:PutLogEvents"],
                                Resource: `arn:aws:logs:${regionName}:${accountId}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*`,
                            },
                            {
                                Sid: "CloudWatchMetricsPublish",
                                Effect: "Allow",
                                Action: "cloudwatch:PutMetricData",
                                Resource: "*",
                                Condition: {
                                    StringEquals: {
                                        "cloudwatch:namespace": "bedrock-agentcore",
                                    },
                                },
                            },
                            {
                                Sid: "AgentCoreWorkloadIdentity",
                                Effect: "Allow",
                                Action: [
                                    "bedrock-agentcore:GetWorkloadAccessToken",
                                    "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                                    "bedrock-agentcore:GetWorkloadAccessTokenForUserId",
                                ],
                                Resource: [
                                    `arn:aws:bedrock-agentcore:${regionName}:${accountId}:workload-identity-directory/default`,
                                    `arn:aws:bedrock-agentcore:${regionName}:${accountId}:workload-identity-directory/default/workload-identity/${RUNTIME_NAME}-*`,
                                ],
                            },
                            {
                                Sid: "AgentCoreMemory",
                                Effect: "Allow",
                                Action: [
                                    "bedrock-agentcore:CreateEvent",
                                    "bedrock-agentcore:GetEvent",
                                    "bedrock-agentcore:GetMemory",
                                    "bedrock-agentcore:GetMemoryRecord",
                                    "bedrock-agentcore:ListActors",
                                    "bedrock-agentcore:ListEvents",
                                    "bedrock-agentcore:ListMemoryRecords",
                                    "bedrock-agentcore:ListSessions",
                                    "bedrock-agentcore:DeleteEvent",
                                    "bedrock-agentcore:DeleteMemoryRecord",
                                    "bedrock-agentcore:RetrieveMemoryRecords",
                                ],
                                Resource: `arn:aws:bedrock-agentcore:${regionName}:${accountId}:memory/*`,
                            },
                        ],
                    }),
                ),
        }, { parent: this });

        this.artifactBucket = new aws.s3.Bucket(`${name}-artifact-bucket`, {
            bucketPrefix: "tech-article-runtime-artifact-",
            forceDestroy: true,
        }, { parent: this });

        this.registerOutputs({
            executionRoleArn: this.executionRole.arn,
            artifactBucketName: this.artifactBucket.bucket,
            runtimeName: RUNTIME_NAME,
            artifactKey: ARTIFACT_KEY,
        });
    }
}
