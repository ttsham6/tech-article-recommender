import { AgentRuntime } from "./components/agent-core";
import { KnowledgeBaseComponent } from "./components/knowledge-base";

const knowledgeBase = new KnowledgeBaseComponent("knowledge-base");

const runtime = new AgentRuntime(
    "runtime",
    {
        knowledgeBaseArn: knowledgeBase.knowledgeBase.arn,
    });

export const agentRuntimeExecutionRoleArn = runtime.executionRole.arn;
export const agentRuntimeArtifactBucketName = runtime.artifactBucket.bucket;
export const agentRuntimeArtifactKey = "strands-runtime.zip";
export const knowledgeBaseArn = knowledgeBase.knowledgeBase.arn;
export const knowledgeBaseId = knowledgeBase.knowledgeBase.id;
export const knowledgeBaseDataSourceId = knowledgeBase.dataSource.dataSourceId;
export const knowledgeBaseSourceBucketName = knowledgeBase.sourceBucket.bucket;
