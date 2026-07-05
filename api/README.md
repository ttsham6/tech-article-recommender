# API

## セットアップ

```sh
cd api
uv sync
cp .env.example .env
```

必要環境変数。
- `AGENT_RUNTIME_ARN`
- `AGENT_RUNTIME_QUALIFIER`
- `JOBS_TABLE_NAME`
- `ASYNC_WORKER_FUNCTION_NAME`

## ローカル起動

```sh
cd api
uv run fastapi dev app/main.py
```

## テスト

```sh
cd api
uv run pytest
```

## Lambda build

```sh
cd api
rm -rf build/package build/api-lambda.zip
mkdir -p build/package
uv pip install \
  --python-platform aarch64-manylinux2014 \
  --python-version 3.13 \
  --target build/package \
  --only-binary=:all: \
  -r pyproject.toml
cp -R app build/package/
cd build/package
zip -r ../api-lambda.zip .
```

## Lambda upload

artifact bucket へ `api-lambda.zip` を配置。

```sh
aws s3 cp build/api-lambda.zip s3://<artifact-bucket>/api-lambda.zip --region ap-northeast-1
```
