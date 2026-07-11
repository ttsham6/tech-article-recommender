# Scripts

## RSS to KB documents

`rss_to_kb_documents.py` は RSS XML 1本を Knowledge Base 向け `1記事1ファイル` へ変換。

出力:
- `YYYY-MM-DD-article-slug.md`
- `YYYY-MM-DD-article-slug.md.metadata.json`

例:

```bash
python3 scripts/rss_to_kb_documents.py \
  data/awsfeed_20260705.xml \
  data/aws-news-blog \
  --source-label aws-news-blog
```

metadata は短い filterable 属性だけを入れる。本文は `.md` 側へ置く。
