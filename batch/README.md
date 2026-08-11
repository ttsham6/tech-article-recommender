# Batch

## セットアップ

```sh
cd batch
uv sync
cp .env.sample .env
```

環境変数は `.env.sample` 参照。
S3 upload 後、`KNOWLEDGE_BASE_ID` と `DATA_SOURCE_ID` を使って ingestion job を開始する。

## ローカル実行

`uv run` で Lambda handler を直接呼ぶ。

```sh
cd batch
PYTHONPATH=.. uv run python -c 'from app.main import handler; print(handler({}, None))'
```

RSS各記事URL は KB投入前に到達確認する。`HEAD` 実行、失敗時 `GET` fallback。`404` `410` 接続失敗 URL は除外。
metadata 契約は `source` `doc_id` `url` 必須。`url` は `http/https` 必須。不正 metadata は投入前に除外。

## Lambda build

```sh
cd batch
rm -rf build/package build/rss-batch.zip
mkdir -p build/package
uv build --wheel --out-dir build/dist
uv pip install \
  --python-platform aarch64-manylinux2014 \
  --python-version 3.13 \
  --target build/package \
  build/dist/*.whl
cd build/package
zip -r ../rss-batch.zip .
```

## Lambda upload

`infra/dist/rss-batch.zip` へ配置。

```sh
cp build/rss-batch.zip ../infra/dist/rss-batch.zip
```
