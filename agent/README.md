# AI Agent

## セットアップ

```sh
cd agent
uv sync
```

## build 手順

```sh
cd agent
rm -rf build/package build/strands-runtime.zip
mkdir -p build/package
uv build --wheel --out-dir build/dist
uv pip install \
  --python-platform aarch64-manylinux2014 \
  --python-version 3.13 \
  --target build/package \
  --only-binary=:all: \
  build/dist/*.whl
cp main.py build/package/
cd build/package
zip -r ../strands-runtime.zip .
```

## ローカル実行

```sh
uv run recommend-articles "Bedrock agents の設計パターン"
```

## AWS 上のruntime を実行

```sh
PAYLOAD_B64=$(printf '%s' '{"preference":"Bedrock AgentCore"}' | base64)

aws bedrock-agentcore invoke-agent-runtime \
  --region ap-northeast-1 \
  --agent-runtime-arn "${AGENT_RUNTIME_ARN}" \
  --qualifier tech_article_recommender_endpoint \
  --content-type application/json \
  --accept application/json \
  --payload "$PAYLOAD_B64" \
  ./response.json
```

## deploy メモ

AgentCore Runtime artifact key は `strands-runtime.zip` の sha256 先頭12桁から自動生成。
zip 内容が変わったときだけ S3 key も変わる。

```sh
cd infra
pulumi up
```
