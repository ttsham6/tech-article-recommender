import * as aws from "@pulumi/aws";
import * as pulumi from "@pulumi/pulumi";

const EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"; // TODO: change model to cohere.embed-multilingual-v3
const DEFAULT_EMBEDDING_DIMENSION = 1024;
const CHUNK_MAX_TOKENS = 512;
const CHUNK_OVERLAP_PERCENTAGE = 20;

export class KnowledgeBaseComponent extends pulumi.ComponentResource {
    public readonly knowledgeBase: aws.bedrock.AgentKnowledgeBase;
    public readonly dataSource: aws.bedrock.AgentDataSource;
    public readonly sourceBucket: aws.s3.Bucket;
    public readonly vectorBucket: aws.s3.VectorsVectorBucket;
    public readonly vectorIndex: aws.s3.VectorsIndex;
    public readonly role: aws.iam.Role;

    constructor(
        name: string,
        args: pulumi.Inputs = {},
        opts?: pulumi.ComponentResourceOptions,
    ) {
        super("tech-article-recommender:bedrock:KnowledgeBase", name, args, opts);

        const region = aws.getRegionOutput({});
        const callerIdentity = aws.getCallerIdentityOutput({});

        const embeddingModelArn = region.region.apply(
            (regionName) => `arn:aws:bedrock:${regionName}::foundation-model/${EMBEDDING_MODEL_ID}`,
        );
        const vectorBucketName = `${pulumi.getStack()}-tech-article-recommender-vectors`;

        this.sourceBucket = new aws.s3.Bucket(`${name}-source-bucket`, {
            bucketPrefix: "tech-article-recommender-kb-source-",
            forceDestroy: true,
        }, { parent: this });

        this.vectorBucket = new aws.s3.VectorsVectorBucket(`${name}-vector-bucket`, {
            vectorBucketName,
            forceDestroy: true,
        }, { parent: this });

        this.vectorIndex = new aws.s3.VectorsIndex(`${name}-vector-index`, {
            indexName: "article-index",
            vectorBucketName: this.vectorBucket.vectorBucketName,
            dataType: "float32",
            dimension: DEFAULT_EMBEDDING_DIMENSION,
            distanceMetric: "cosine",
        }, { parent: this });

        this.role = new aws.iam.Role(`${name}-role`, {
            assumeRolePolicy: pulumi
                .all([region.region, callerIdentity.accountId])
                .apply(([regionName, accountId]) =>
                    JSON.stringify({
                        Version: "2012-10-17",
                        Statement: [
                            {
                                Sid: "AllowBedrockKnowledgeBaseAssumeRole",
                                Effect: "Allow",
                                Principal: {
                                    Service: "bedrock.amazonaws.com",
                                },
                                Action: "sts:AssumeRole",
                                Condition: {
                                    StringEquals: {
                                        "aws:SourceAccount": accountId,
                                    },
                                    ArnLike: {
                                        "AWS:SourceArn": `arn:aws:bedrock:${regionName}:${accountId}:knowledge-base/*`,
                                    },
                                },
                            },
                        ],
                    }),
                ),
        }, { parent: this });

        new aws.iam.RolePolicy(`${name}-role-policy`, {
            role: this.role.id,
            policy: pulumi
                .all([
                    this.sourceBucket.arn,
                    this.vectorBucket.vectorBucketArn,
                    this.vectorIndex.indexArn,
                    embeddingModelArn,
                ])
                .apply(([sourceBucketArn, vectorBucketArn, indexArn, resolvedEmbeddingModelArn]) =>
                    JSON.stringify({
                        Version: "2012-10-17",
                        Statement: [
                            {
                                Sid: "ReadKnowledgeSourceBucket",
                                Effect: "Allow",
                                Action: [
                                    "s3:GetObject",
                                    "s3:ListBucket",
                                ],
                                Resource: [
                                    sourceBucketArn,
                                    `${sourceBucketArn}/*`,
                                ],
                            },
                            {
                                Sid: "InvokeEmbeddingModel",
                                Effect: "Allow",
                                Action: [
                                    "bedrock:InvokeModel",
                                ],
                                Resource: resolvedEmbeddingModelArn,
                            },
                            {
                                Sid: "ManageS3VectorsStore",
                                Effect: "Allow",
                                Action: [
                                    "s3vectors:*",
                                ],
                                Resource: [
                                    vectorBucketArn,
                                    indexArn,
                                ],
                            },
                        ],
                    }),
                ),
        }, { parent: this });

        this.knowledgeBase = new aws.bedrock.AgentKnowledgeBase(`${name}-resource`, {
            name: `${name}-kb`,
            description: "Managed knowledge base for AWS article recommendations",
            roleArn: this.role.arn,
            knowledgeBaseConfiguration: {
                type: "VECTOR",
                vectorKnowledgeBaseConfiguration: {
                    embeddingModelArn,
                },
            },
            storageConfiguration: {
                type: "S3_VECTORS",
                s3VectorsConfiguration: {
                    indexArn: this.vectorIndex.indexArn,
                },
            },
        }, {
            parent: this,
            dependsOn: [this.vectorIndex],
        });

        this.dataSource = new aws.bedrock.AgentDataSource(`${name}-data-source`, {
            knowledgeBaseId: this.knowledgeBase.id,
            name: `${name}-s3-source`,
            description: "Source bucket for article knowledge documents",
            dataDeletionPolicy: "RETAIN",
            dataSourceConfiguration: {
                type: "S3",
                s3Configuration: {
                    bucketArn: this.sourceBucket.arn,
                },
            },
            vectorIngestionConfiguration: {
                chunkingConfiguration: {
                    chunkingStrategy: "FIXED_SIZE",
                    fixedSizeChunkingConfiguration: {
                        maxTokens: CHUNK_MAX_TOKENS,
                        overlapPercentage: CHUNK_OVERLAP_PERCENTAGE,
                    },
                },
            },
        }, {
            parent: this,
            dependsOn: [this.knowledgeBase],
        });

        this.registerOutputs({
            knowledgeBaseId: this.knowledgeBase.id,
            knowledgeBaseArn: this.knowledgeBase.arn,
            dataSourceId: this.dataSource.dataSourceId,
            sourceBucketName: this.sourceBucket.bucket,
            vectorBucketArn: this.vectorBucket.vectorBucketArn,
            vectorIndexArn: this.vectorIndex.indexArn,
            roleArn: this.role.arn,
        });
    }
}
