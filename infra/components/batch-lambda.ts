import * as aws from "@pulumi/aws";
import * as pulumi from "@pulumi/pulumi";
import { getArtifactHash } from "./artifact";

const FUNCTION_NAME = "tech-article-recommender-rss-batch";

export interface BatchLambdaArgs {
    artifactPath: string;
    kbSourceBucketArn: pulumi.Input<string>;
    kbSourceBucketName: pulumi.Input<string>;
    knowledgeBaseId: pulumi.Input<string>;
    dataSourceId: pulumi.Input<string>;
    articleCategory: pulumi.Input<string>;
    batchRssFeedUrl: pulumi.Input<string>;
    batchScheduleExpression: pulumi.Input<string>;
}

export class BatchLambda extends pulumi.ComponentResource {

    constructor(
        name: string,
        args: BatchLambdaArgs,
        opts?: pulumi.ComponentResourceOptions,
    ) {
        super("tech-article-recommender:lambda:BatchLambda", name, args, opts);

        const region = aws.getRegionOutput({});
        const callerIdentity = aws.getCallerIdentityOutput({});
        const artifactHash = getArtifactHash(args.artifactPath);

        const role = new aws.iam.Role("batch-role", {
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
                    name: "batch-policy",
                    policy: pulumi
                        .all([
                            region.region,
                            callerIdentity.accountId,
                            args.kbSourceBucketArn,
                        ])
                        .apply(([regionName, accountId, kbSourceBucketArn]) =>
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
                                        Sid: "WriteKnowledgeBaseSourceBucket",
                                        Effect: "Allow",
                                        Action: [
                                            "s3:ListBucket",
                                            "s3:PutObject",
                                        ],
                                        Resource: [
                                            kbSourceBucketArn,
                                            `${kbSourceBucketArn}/*`,
                                        ],
                                    },
                                    {
                                        Sid: "StartKnowledgeBaseIngestion",
                                        Effect: "Allow",
                                        Action: [
                                            "bedrock:StartIngestionJob",
                                        ],
                                        Resource: "*",
                                    },
                                ],
                            }),
                        ),
                },
            ],
        });

        // Lambda Function
        const lambdaFunction = new aws.lambda.Function("batch-function", {
            name: FUNCTION_NAME,
            role: role.arn,
            runtime: aws.lambda.Runtime.Python3d13,
            handler: "app.main.handler",
            architectures: ["arm64"],
            timeout: 180,
            memorySize: 512,
            code: new pulumi.asset.FileArchive(args.artifactPath),
            sourceCodeHash: artifactHash,
            environment: {
                variables: {
                    KB_SOURCE_BUCKET: args.kbSourceBucketName,
                    KNOWLEDGE_BASE_ID: args.knowledgeBaseId,
                    DATA_SOURCE_ID: args.dataSourceId,
                    ARTICLE_CATEGORY: args.articleCategory,
                    RSS_FEED_URL: args.batchRssFeedUrl,
                },
            },
        });

        // Schedule Rule
        const scheduleRule = new aws.cloudwatch.EventRule("batch-schedule", {
            scheduleExpression: args.batchScheduleExpression,
            description: "Scheduled RSS batch trigger",
        });

        new aws.cloudwatch.EventTarget("batch-schedule-target", {
            rule: scheduleRule.name,
            arn: lambdaFunction.arn,
        });

        new aws.lambda.Permission("batch-schedule-permission", {
            action: "lambda:InvokeFunction",
            function: lambdaFunction.name,
            principal: "events.amazonaws.com",
            sourceArn: scheduleRule.arn,
        });



    }
}
