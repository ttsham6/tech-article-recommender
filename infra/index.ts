import { AgentRuntime } from "./components/agent-core";
import { ApiLambda } from "./components/api-lambda";
import { BatchLambda } from "./components/batch-lambda";
import { DynamoDb } from "./components/dynamodb";
import { KnowledgeBase } from "./components/knowledge-base";
import { S3 } from "./components/s3";

const AGENT_ARTIFACT_PATH = "../agent/build/strands-runtime.zip";
const API_ARTIFACT_PATH = "../api/build/api-lambda.zip";
const BATCH_ARTIFACT_PATH = "../batch/build/rss-batch.zip";

const s3 = new S3("s3");
const dynamoDb = new DynamoDb("dynamodb");

const knowledgeBase = new KnowledgeBase("knowledge-base",
    {
        sourceBucketArn: s3.kbSourceBucket.arn,
        vectorBucketArn: s3.kbVectorBucket.vectorBucketArn,
        vectorIndexArn: s3.kbVectorIndex.indexArn,
    });

const agentCoreRuntime = new AgentRuntime(
    "runtime",
    {
        artifactPath: AGENT_ARTIFACT_PATH,
        knowledgeBaseArn: knowledgeBase.knowledgeBase.arn,
        knowledgeBaseId: knowledgeBase.knowledgeBase.id,
        sourceBucketName: s3.artifactBucket.bucket,
    });

const apiLambda = new ApiLambda(
    "api",
    {
        artifactPath: API_ARTIFACT_PATH,
        agentRuntimeArn: agentCoreRuntime.agentRuntime.agentRuntimeArn,
        agentRuntimeEndpointArn: agentCoreRuntime.endpoint.agentRuntimeEndpointArn,
        agentRuntimeQualifier: "tech_article_recommender_endpoint",
        jobsTableArn: dynamoDb.jobsTable.arn,
        jobsTableName: dynamoDb.jobsTable.name,
    });

const batchLambda = new BatchLambda(
    "batch",
    {
        artifactPath: BATCH_ARTIFACT_PATH,
        kbSourceBucketArn: s3.kbSourceBucket.arn,
        kbSourceBucketName: s3.kbSourceBucket.bucket,
        knowledgeBaseId: knowledgeBase.knowledgeBase.id,
        dataSourceId: knowledgeBase.dataSource.dataSourceId,
        articleCategory: "aws",
        batchRssFeedUrl: "https://aws.amazon.com/jp/blogs/aws/feed/",
        batchScheduleExpression: "cron(0 15 * * ? *)",
    }
);
