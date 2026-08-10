import * as aws from "@pulumi/aws";
import * as pulumi from "@pulumi/pulumi";
import { resolveArtifactPath } from "./artifact";

const FUNCTION_NAME = "tech-article-recommender-api";

export interface ApiLambdaArgs {
    artifactPath: string;
    agentRuntimeArn: pulumi.Input<string>;
    agentRuntimeEndpointArn: pulumi.Input<string>;
    agentRuntimeQualifier: pulumi.Input<string>;
    jobsTableArn: pulumi.Input<string>;
    jobsTableName: pulumi.Input<string>;
}

export class ApiLambda extends pulumi.ComponentResource {
    public readonly role: aws.iam.Role;
    public readonly function: aws.lambda.Function;
    public readonly api: aws.apigatewayv2.Api;
    public readonly stage: aws.apigatewayv2.Stage;

    constructor(
        name: string,
        args: ApiLambdaArgs,
        opts?: pulumi.ComponentResourceOptions,
    ) {
        super("tech-article-recommender:lambda:ApiLambda", name, args, opts);

        const region = aws.getRegionOutput({});
        const callerIdentity = aws.getCallerIdentityOutput({});
        const artifactPath = resolveArtifactPath(args.artifactPath);

        // IAM Role
        this.role = new aws.iam.Role(`${name}-role`, {
            assumeRolePolicy: JSON.stringify({
                Version: "2012-10-17",
                Statement: [
                    {
                        Effect: "Allow",
                        Principal: { Service: "lambda.amazonaws.com" },
                        Action: "sts:AssumeRole",
                    },
                ],
            }),
            inlinePolicies: [
                {
                    name: `${name}-policy`,
                    policy: pulumi
                        .all([
                            region.region,
                            callerIdentity.accountId,
                            args.agentRuntimeArn,
                            args.agentRuntimeEndpointArn,
                            args.jobsTableArn,
                        ])
                        .apply(([regionName, accountId, agentRuntimeArn, agentRuntimeEndpointArn, jobsTableArn]) =>
                            JSON.stringify({
                                Version: "2012-10-17",
                                Statement: [
                                    {
                                        Sid: "CloudWatchLogs",
                                        Effect: "Allow",
                                        Action: [
                                            "logs:CreateLogGroup",
                                            "logs:CreateLogStream",
                                            "logs:PutLogEvents",
                                        ],
                                        Resource: [
                                            `arn:aws:logs:${regionName}:${accountId}:log-group:/aws/lambda/${FUNCTION_NAME}:*`,
                                            `arn:aws:logs:${regionName}:${accountId}:log-group:/aws/lambda/${FUNCTION_NAME}`,
                                        ],
                                    },
                                    {
                                        Sid: "InvokeAgentRuntime",
                                        Effect: "Allow",
                                        Action: [
                                            "bedrock-agentcore:InvokeAgentRuntime",
                                        ],
                                        Resource: [
                                            agentRuntimeArn,
                                            agentRuntimeEndpointArn,
                                        ],
                                    },
                                    {
                                        Sid: "InvokeSelfAsyncWorker",
                                        Effect: "Allow",
                                        Action: [
                                            "lambda:InvokeFunction",
                                        ],
                                        Resource: [
                                            `arn:aws:lambda:${regionName}:${accountId}:function:${FUNCTION_NAME}`,
                                        ],
                                    },
                                    {
                                        Sid: "JobsTableAccess",
                                        Effect: "Allow",
                                        Action: [
                                            "dynamodb:GetItem",
                                            "dynamodb:PutItem",
                                            "dynamodb:UpdateItem",
                                        ],
                                        Resource: [
                                            jobsTableArn,
                                        ],
                                    },
                                ],
                            }),
                        ),
                }
            ]
        }, { parent: this });

        // Lambda Function
        this.function = new aws.lambda.Function(`${name}-function`, {
            name: FUNCTION_NAME,
            role: this.role.arn,
            runtime: aws.lambda.Runtime.Python3d13,
            handler: "app.main.handler",
            architectures: ["arm64"],
            timeout: 180,
            memorySize: 512,
            code: new pulumi.asset.FileArchive(artifactPath),
            environment: {
                variables: {
                    AGENT_RUNTIME_ARN: args.agentRuntimeArn,
                    AGENT_RUNTIME_QUALIFIER: args.agentRuntimeQualifier,
                    JOBS_TABLE_NAME: args.jobsTableName,
                    ASYNC_WORKER_FUNCTION_NAME: FUNCTION_NAME,
                },
            },
        }, { parent: this });

        // API Gateway
        this.api = new aws.apigatewayv2.Api(`${name}-http-api`, {
            protocolType: "HTTP",
            corsConfiguration: {
                allowHeaders: ["authorization", "content-type"],
                allowMethods: ["GET", "POST", "OPTIONS"],
                allowOrigins: ["*"],
            },
        }, { parent: this });

        const integration = new aws.apigatewayv2.Integration(`${name}-integration`, {
            apiId: this.api.id,
            integrationType: "AWS_PROXY",
            integrationUri: this.function.arn,
            integrationMethod: "POST",
            payloadFormatVersion: "2.0",
        }, { parent: this.api });

        new aws.apigatewayv2.Route(`${name}-health-route`, {
            apiId: this.api.id,
            routeKey: "GET /health",
            target: pulumi.interpolate`integrations/${integration.id}`,
        }, { parent: this.api });

        new aws.apigatewayv2.Route(`${name}-recommendations-route`, {
            apiId: this.api.id,
            routeKey: "POST /recommendations",
            target: pulumi.interpolate`integrations/${integration.id}`,
        }, { parent: this.api });

        new aws.apigatewayv2.Route(`${name}-recommendations-get-route`, {
            apiId: this.api.id,
            routeKey: "GET /recommendations/{job_id}",
            target: pulumi.interpolate`integrations/${integration.id}`,
        }, { parent: this.api });

        this.stage = new aws.apigatewayv2.Stage(`${name}-stage`, {
            apiId: this.api.id,
            name: "$default",
            autoDeploy: true,
        }, { parent: this.api });

        new aws.lambda.Permission(`${name}-invoke-permission`, {
            action: "lambda:InvokeFunction",
            function: this.function.name,
            principal: "apigateway.amazonaws.com",
            sourceArn: pulumi.interpolate`${this.api.executionArn}/*/*`,
        }, { parent: this.function });

        this.registerOutputs({
            functionName: this.function.name,
            apiEndpoint: this.api.apiEndpoint,
        });
    }
}
