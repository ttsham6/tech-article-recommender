import { AgentRuntime } from "./components/agent-core";
import { KnowledgeBase } from "./components/knowledge-base";
import { S3 } from "./components/s3";

const s3 = new S3("s3");

const knowledgeBase = new KnowledgeBase("knowledge-base",
    {
        sourceBucketArn: s3.kbSourceBucket.arn,
        vectorBucketArn: s3.kbVectorBucket.vectorBucketArn,
        vectorIndexArn: s3.kbVectorIndex.indexArn,
    });

const runtime = new AgentRuntime(
    "runtime",
    {
        knowledgeBaseArn: knowledgeBase.knowledgeBase.arn,
        knowledgeBaseId: knowledgeBase.knowledgeBase.id,
        sourceBucketName: s3.artifactBucket.bucket,
    });

export const agentRuntimeExecutionRoleArn = runtime.executionRole.arn;
export const agentRuntimeArtifactKey = "strands-runtime.zip";
export const agentRuntimeArn = runtime.agentRuntime.agentRuntimeArn;
export const agentRuntimeId = runtime.agentRuntime.agentRuntimeId;
export const agentRuntimeEndpointArn = runtime.endpoint.agentRuntimeEndpointArn;
export const knowledgeBaseArn = knowledgeBase.knowledgeBase.arn;
export const knowledgeBaseId = knowledgeBase.knowledgeBase.id;
export const knowledgeBaseDataSourceId = knowledgeBase.dataSource.dataSourceId;
