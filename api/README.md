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
- `SELF_ASYNC_WORKER_FUNCTION_NAME`

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
rm -rf build/dist build/lib tech_article_recommender_api.egg-info
mkdir -p build/package
uv build --wheel --out-dir build/dist
uv pip install \
  --python-platform aarch64-manylinux2014 \
  --python-version 3.13 \
  --target build/package \
  --only-binary=:all: \
  build/dist/*.whl
cd build/package
zip -r ../api-lambda.zip .
```

`build/lib` と `tech_article_recommender_api.egg-info` が残ると旧 schema が wheel に混入する。schema 変更時は必ず削除。

## Lambda upload

`infra/dist/api-lambda.zip` へ配置。

```sh
cp build/api-lambda.zip ../infra/dist/api-lambda.zip
```
