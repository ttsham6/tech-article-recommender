from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

import feedparser
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class DocObject:
    path: Path
    content_type: str


@dataclass(frozen=True)
class ArticleDocument:
    article: DocObject
    metadata: DocObject


def convert_feed_to_documents(input_path: Path, output_dir: Path, source_label: str) -> list[ArticleDocument]:
    """
    RSS を読み込み、各 entry を 1記事ずつファイルへ書き出す。
    """
    feed = feedparser.parse(input_path.read_bytes())
    if getattr(feed, "bozo", False) and not feed.entries:
        raise ValueError(f"RSS parse failed: {feed.bozo_exception}")

    output_dir.mkdir(parents=True, exist_ok=True)
    return [
        write_article(entry, output_dir, source_label, index)
        for index, entry in enumerate(feed.entries, start=1)
    ]


def write_article(entry: feedparser.FeedParserDict, output_dir: Path, source_label: str, index: int) -> ArticleDocument:
    """
    feedparser の 1 entry を markdown 本文と metadata sidecar に変換する。
    """
    pub_date = str(entry.get("published", "")).strip()
    article_path, iso_date = article_output_path(output_dir, pub_date, index)
    title = str(entry.get("title", "")).strip()
    link = str(entry.get("link", "")).strip()
    author = str(entry.get("author", entry.get("dc_creator", ""))).strip()
    guid = str(entry.get("id", entry.get("guid", ""))).strip()
    tags = entry.get("tags") or []

    categories = [
        str(tag.get("term", "")).strip()
        for tag in tags
        if str(tag.get("term", "")).strip()
    ]

    summary = html_to_text(
        str(entry.get("summary", entry.get("description", ""))))

    content_blocks = entry.get("content") or []
    content = html_to_text(
        "\n\n".join(
            str(block.get("value", "")).strip()
            for block in content_blocks
            if str(block.get("value", "")).strip()
        )
    )

    lines = [
        f"# {title}",
        "",
        f"- URL: {link}",
        f"- Author: {author}",
        f"- PublishedAt: {pub_date}",
        f"- Categories: {', '.join(categories)}",
        f"- Guid: {guid}",
    ]
    if summary:
        lines.extend(["", "## Summary", "", summary])
    if content:
        lines.extend(["", "## Content", "", content])

    metadata = {
        "metadataAttributes": {
            "source": source_label,
            "title": title,
            "url": link,
            "published_date": iso_date,
            "service": categories[0] if categories else "",
            "source_host": urlparse(link).netloc,
            "doc_id": hashlib.sha1(f"{title}\n{link}".encode("utf-8")).hexdigest()[:16],
        }
    }

    metadata_path = article_path.with_name(article_path.name + ".metadata.json")
    article_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return ArticleDocument(
        article=DocObject(
            path=article_path,
            content_type="text/markdown; charset=utf-8",
        ),
        metadata=DocObject(
            path=metadata_path,
            content_type="application/json; charset=utf-8",
        ),
    )


def article_output_path(output_dir: Path, pub_date: str, index: int) -> tuple[Path, str]:
    """
    公開日と連番から、衝突回避済みの記事出力パスを作る。
    """
    parsed = parsedate_to_datetime(pub_date)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    iso_date = parsed.date().isoformat()
    date_token = iso_date.replace("-", "") if iso_date else "unknown"
    article_path = unique_path(output_dir / f"{date_token}-{index:04d}.md")
    return article_path, iso_date


def unique_path(path: Path) -> Path:
    """
    同名ファイル衝突を避けた出力先パスを返す。
    例: /path/to/file.md → /path/to/file-2.md, /path/to/file-3.md, ...
    """
    if not path.exists():
        return path

    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def html_to_text(value: str) -> str:
    """
    HTML をプレーンテキストへ変換する。
    """
    if not value.strip():
        return ""

    soup = BeautifulSoup(value, "html.parser")
    for node in soup.select("script, style"):
        node.decompose()

    for br in soup.find_all("br"):
        br.replace_with("\n")

    text = soup.get_text("\n")
    lines = [line.strip() for line in text.replace("\xa0", " ").splitlines()]
    return "\n".join(line for line in lines if line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert RSS XML into KB-ready article documents with feedparser."
    )
    parser.add_argument("input", type=Path, help="RSS XML file path")
    parser.add_argument("output_dir", type=Path,
                        help="Directory for generated article files")
    parser.add_argument(
        "--source-label",
        default=None,
        help="Metadata source label. Default: <input-stem>-<current-utc-date>",
    )
    args = parser.parse_args()

    source_label = args.source_label or f"{args.input.stem}-{datetime.now(timezone.utc):%Y%m%d}"

    written_files = convert_feed_to_documents(
        args.input, args.output_dir, source_label)

    print(f"generated_articles={len(written_files)}")
    for document in written_files:
        print(document.article.path)
