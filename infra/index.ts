import { AgentRuntime } from "./components/agent-core";
import { ApiLambda } from "./components/api-lambda";
import { DynamoDb } from "./components/dynamodb";
import { KnowledgeBase } from "./components/knowledge-base";
import { S3 } from "./components/s3";

const AGENT_ARTIFACT_PATH = "dist/strands-runtime.zip";
const API_ARTIFACT_PATH = "dist/api-lambda.zip";

const s3 = new S3("s3");
const dynamoDb = new DynamoDb("dynamodb");

const knowledgeBase = new KnowledgeBase("knowledge-base",
    {
        sourceBucketArn: s3.kbSourceBucket.arn,
        vectorBucketArn: s3.kbVectorBucket.vectorBucketArn,
        vectorIndexArn: s3.kbVectorIndex.indexArn,
    });

const runtime = new AgentRuntime(
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
        agentRuntimeArn: runtime.agentRuntime.agentRuntimeArn,
        agentRuntimeEndpointArn: runtime.endpoint.agentRuntimeEndpointArn,
        agentRuntimeQualifier: "tech_article_recommender_endpoint",
        jobsTableArn: dynamoDb.jobsTable.arn,
        jobsTableName: dynamoDb.jobsTable.name,
    });

export const agentRuntimeExecutionRoleArn = runtime.executionRole.arn;
export const agentRuntimeArtifactKey = "strands-runtime.zip";
export const agentRuntimeArn = runtime.agentRuntime.agentRuntimeArn;
export const agentRuntimeId = runtime.agentRuntime.agentRuntimeId;
export const agentRuntimeEndpointArn = runtime.endpoint.agentRuntimeEndpointArn;
export const artifactBucketName = s3.artifactBucket.bucket;
export const apiLambdaArtifactKey = "api-lambda.zip";
export const apiLambdaFunctionName = apiLambda.function.name;
export const apiEndpointUrl = apiLambda.api.apiEndpoint;
export const jobsTableArn = dynamoDb.jobsTable.arn;
export const jobsTableName = dynamoDb.jobsTable.name;
export const knowledgeBaseArn = knowledgeBase.knowledgeBase.arn;
export const knowledgeBaseId = knowledgeBase.knowledgeBase.id;
export const knowledgeBaseDataSourceId = knowledgeBase.dataSource.dataSourceId;
