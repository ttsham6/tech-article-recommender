import * as aws from "@pulumi/aws";
import * as pulumi from "@pulumi/pulumi";
import { resolveArtifactPath } from "./artifact";

const RUNTIME_NAME = "TechArticleRecommender";
const ARTIFACT_KEY = "strands-runtime.zip";
const MODEL_ID = "amazon.nova-lite-v1:0";
const ENDPOINT_NAME = "tech_article_recommender_endpoint";

export interface AgentRuntimeArgs {
    artifactPath: string;
    knowledgeBaseArn: pulumi.Input<string>;
    knowledgeBaseId: pulumi.Input<string>;
    sourceBucketName: pulumi.Input<string>;
}

export class AgentRuntime extends pulumi.ComponentResource {
    public readonly executionRole: aws.iam.Role;
    public readonly agentRuntime: aws.bedrock.AgentcoreAgentRuntime;
    public readonly endpoint: aws.bedrock.AgentcoreAgentRuntimeEndpoint;

    constructor(
        name: string,
        args: AgentRuntimeArgs,
        opts?: pulumi.ComponentResourceOptions,
    ) {
        super("tech-article-recommender:agentcore:Runtime", name, args, opts);

        const region = aws.getRegionOutput({});
        const callerIdentity = aws.getCallerIdentityOutput({});
        const artifactPath = resolveArtifactPath(args.artifactPath);

        // IAM role
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
            inlinePolicies: [
                {
                    name: `${name}-execution-policy`,
                    policy: pulumi
                        .all([region.region, callerIdentity.accountId, args.knowledgeBaseArn])
                        .apply(([regionName, accountId, knowledgeBaseArn]) =>
                            JSON.stringify({
                                Version: "2012-10-17",
                                Statement: [
                                    // knowledge base
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
                                    //workload identity and memory
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
                                    // ecr-public and xray
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
                                    // logging
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

                                ],
                            }),
                        ),
                }
            ]
        }, { parent: this });

        const artifact = new aws.s3.BucketObject(`${name}-artifact`, {
            bucket: args.sourceBucketName,
            key: ARTIFACT_KEY,
            source: new pulumi.asset.FileAsset(artifactPath),
            contentType: "application/zip",
        }, { parent: this });

        // Agent runtime
        this.agentRuntime = new aws.bedrock.AgentcoreAgentRuntime(`${name}-resource`, {
            agentRuntimeName: RUNTIME_NAME,
            description: "Strands recommendation agent runtime",
            roleArn: this.executionRole.arn,
            agentRuntimeArtifact: {
                codeConfiguration: {
                    entryPoints: ["main.py"],
                    runtime: "PYTHON_3_13",
                    code: {
                        s3: {
                            bucket: args.sourceBucketName,
                            prefix: artifact.key,
                        },
                    },
                },
            },
            environmentVariables: {
                AWS_REGION: region.region,
                BEDROCK_MODEL_ID: MODEL_ID,
                BEDROCK_KNOWLEDGE_BASE_ID: args.knowledgeBaseId,
            },
            networkConfiguration: {
                networkMode: "PUBLIC",
            },
        }, { parent: this, dependsOn: [artifact] });

        // Endpoint
        this.endpoint = new aws.bedrock.AgentcoreAgentRuntimeEndpoint(`${name}-endpoint`, {
            agentRuntimeId: this.agentRuntime.agentRuntimeId,
            agentRuntimeVersion: this.agentRuntime.agentRuntimeVersion,
            name: ENDPOINT_NAME,
            description: "Public endpoint for the Strands recommendation runtime",
        }, { parent: this });

        // Outputs
        this.registerOutputs({
            executionRoleArn: this.executionRole.arn,
            runtimeName: RUNTIME_NAME,
            artifactKey: ARTIFACT_KEY,
            agentRuntimeArn: this.agentRuntime.agentRuntimeArn,
            agentRuntimeId: this.agentRuntime.agentRuntimeId,
            endpointArn: this.endpoint.agentRuntimeEndpointArn,
        });
    }
}
