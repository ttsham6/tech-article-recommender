# Frontend

LINEミニアプリ向け Vite + React + TypeScript フロントエンド。

## 画面機能

- LIFF 初期化
- LINE ログイン状態 取得
- プロフィール表示
- 推薦ジョブ作成 `POST /recommendations`
- ジョブ完了まで ポーリング `GET /recommendations/{job_id}`
- 記事一覧表示
- LINE 内ブラウザ優先 記事オープン

## 構成

- `index.html` Vite entry
- `src/App.tsx` 画面構成
- `src/hooks/useLiff.ts` LIFF 初期化
- `src/hooks/useRecommendationJob.ts` ジョブ送信 ポーリング
- `src/lib/api.ts` API client
- `src/components/` UI部品
- `src/types.ts` API / LIFF 型定義
- `styles.css` モバイル向けスタイル
- `.env.example` 設定テンプレ
- `tsconfig.json` TypeScript 設定

## セットアップ

```sh
cd frontend
yarn install
cp .env.example .env
```

`@line/liff` は Yarn PnP と相性悪い。`frontend/.yarnrc.yml` で `nodeLinker: node-modules` 指定済み。依存変更後は `yarn install` 再実行 必須。

`.env` 編集。

```dotenv
VITE_LIFF_ID=YOUR_LIFF_ID
VITE_API_BASE_URL=https://your-api-id.execute-api.ap-northeast-1.amazonaws.com
VITE_POLL_INTERVAL_MS=2500
VITE_POLL_TIMEOUT_MS=90000
```

## 開発起動

```sh
cd frontend
yarn dev
```

`http://127.0.0.1:4173` 確認。

## 本番ビルド

```sh
cd frontend
yarn build
```

出力先 `frontend/dist/`。静的配信前提。

## LINE Developers 設定

1. LIFF app 作成
2. Endpoint URL に 配信URL 設定
3. `.env` の `VITE_LIFF_ID` 更新
4. API Gateway URL を `VITE_API_BASE_URL` 設定

## API 仕様反映

- リクエスト

```json
{
  "preference": "Bedrock AgentCore の設計パターン"
}
```

- 受付レスポンス

```json
{
  "job_id": "uuid",
  "status": "pending"
}
```

- 取得レスポンス

```json
{
  "job_id": "uuid",
  "status": "succeeded",
  "result": {
    "items": [
      {
        "title": "article title",
        "url": "https://example.com",
        "reason": "recommend reason"
      }
    ]
  },
  "error_message": null
}
```

## 認証メモ

API側 `Authorization: Bearer ...` 形式のみ検査。フロントは LIFF ID token 優先、無ければ access token 送信。
