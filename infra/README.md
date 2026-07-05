# Infra

AgentCore harness + Bedrock Knowledge Base 配備用 Pulumi TypeScript 構成。

## 作る物

- Harness 実行IAM role
- Gateway 実行IAM role
- Knowledge Base service role
- source S3 bucket
- S3 Vectors bucket / index
- `aws.bedrock.AgentKnowledgeBase`
- `aws.bedrock.AgentDataSource`
- `aws.bedrock.AgentcoreGateway`
- `aws.bedrock.AgentcoreHarness`
- `aws.cloudcontrol.Resource` (`AWS::BedrockAgentCore::GatewayTarget` connector用)
- 出力: `harnessArn` `harnessId` `knowledgeBaseId` `knowledgeBaseSourceBucketName`

## Setup

```bash
cd infra
yarn install
pulumi login
pulumi stack init dev
pulumi config set aws:region ap-northeast-1
pulumi config set harnessName TechArticleRecommender
pulumi config set bedrockModelId openai.gpt-oss-20b-1:0
pulumi config set embeddingModelId amazon.titan-embed-text-v2:0
pulumi preview
pulumi up
```

## Artifact build

`pulumi preview` / `pulumi up` 前に zip artifact を `infra/dist/` へ配置必要。

```bash
./scripts/build_artifacts.sh
cd infra
pulumi preview
pulumi up
```

## Config

- `harnessName` default `TechArticleRecommender`
- `bedrockModelId` default `openai.gpt-oss-20b-1:0`
- `embeddingModelId` default `amazon.titan-embed-text-v2:0`
- `embeddingDimension` default `1024`
- `maxIterations` default `6`
- `maxTokens` default `1200`
- `timeoutSeconds` default `120`
- `retrievalResultCount` default `8`
- `chunkMaxTokens` default `512`
- `chunkOverlapPercentage` default `20`

## Notes

- `infra/dist/strands-runtime.zip` と `infra/dist/api-lambda.zip` を Pulumi が参照
- Harness 方針。自前FastAPI不要
- 生成agent loopは AgentCore managed harness 側
- backend 側は `InvokeHarness` クライアント専用
- Knowledge Base / Data Source / Vector Store も Pulumi 管理
- Harness tool として AgentCore Gateway 経由 `Retrieve` 接続
- Gateway target は `bedrock-knowledge-bases` connector 使用
- `AgentcoreGatewayTarget` native resource は connector target 未対応。ここだけ `aws.cloudcontrol.Resource` 使用
- `pulumi up` 後、`knowledgeBaseSourceBucketName` へ文書配置し、別途 ingestion 実行必要
