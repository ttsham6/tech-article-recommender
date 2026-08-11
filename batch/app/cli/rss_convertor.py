from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

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


@dataclass(frozen=True)
class ConvertFeedResult:
    documents: list[ArticleDocument]
    skipped_invalid_urls: int
    skipped_invalid_metadata: int


def convert_feed_to_documents(
    input_path: Path,
    output_dir: Path,
    source_label: str,
    url_check_timeout_seconds: int = 30,
) -> ConvertFeedResult:
    """
    RSS を読み込み、各 entry を 1記事ずつファイルへ書き出す。
    """
    feed = feedparser.parse(input_path.read_bytes())
    if getattr(feed, "bozo", False) and not feed.entries:
        raise ValueError(f"RSS parse failed: {feed.bozo_exception}")

    output_dir.mkdir(parents=True, exist_ok=True)
    documents: list[ArticleDocument] = []
    skipped_invalid_urls = 0
    skipped_invalid_metadata = 0

    for index, entry in enumerate(feed.entries, start=1):
        document, skip_reason = write_article(
            entry,
            output_dir,
            source_label,
            index,
            url_check_timeout_seconds=url_check_timeout_seconds,
        )
        if document is None:
            if skip_reason == "invalid_url":
                skipped_invalid_urls += 1
            else:
                skipped_invalid_metadata += 1
            continue
        documents.append(document)

    return ConvertFeedResult(
        documents=documents,
        skipped_invalid_urls=skipped_invalid_urls,
        skipped_invalid_metadata=skipped_invalid_metadata,
    )


def write_article(
    entry: feedparser.FeedParserDict,
    output_dir: Path,
    source_label: str,
    index: int,
    url_check_timeout_seconds: int = 30,
) -> tuple[ArticleDocument | None, str | None]:
    """
    feedparser の 1 entry を markdown 本文と metadata sidecar に変換する。
    """
    pub_date = str(entry.get("published", "")).strip()
    article_path, iso_date = article_output_path(output_dir, pub_date, index)
    title = str(entry.get("title", "")).strip()
    link = str(entry.get("link", "")).strip()

    if not is_supported_http_url(link):
        return None, "invalid_url"

    if not is_reachable_url(link, timeout_seconds=url_check_timeout_seconds):
        return None, "invalid_url"

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

    metadata_attributes = {
        "source": source_label,
        "title": title,
        "url": link,
        "published_date": iso_date,
        "service": categories[0] if categories else "",
        "source_host": urlparse(link).netloc,
        "doc_id": hashlib.sha1(f"{title}\n{link}".encode("utf-8")).hexdigest()[:16],
    }
    if not validate_metadata_attributes(metadata_attributes):
        return None, "invalid_metadata"

    metadata = {
        "metadataAttributes": metadata_attributes
    }

    metadata_path = article_path.with_name(
        article_path.name + ".metadata.json")
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
    ), None


def validate_metadata_attributes(metadata_attributes: dict[str, str]) -> bool:
    required_keys = ("source", "doc_id", "url")
    if not all(metadata_attributes.get(key, "").strip() for key in required_keys):
        return False
    return is_supported_http_url(metadata_attributes["url"])


def is_supported_http_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_reachable_url(url: str, timeout_seconds: int) -> bool:
    """
    KB投入前に記事URL疎通確認。HEAD失敗時 GET fallback。
    """
    for method in ("HEAD", "GET"):
        request = Request(
            url,
            method=method,
            headers={
                "User-Agent": "tech-article-recommender-batch/1.0",
                "Accept": "text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8",
            },
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                status_code = getattr(response, "status", None) or response.getcode()
                if 200 <= status_code < 400:
                    return True
        except HTTPError as error:
            if error.code in {404, 410}:
                return False
            if method == "GET":
                return False
        except URLError:
            if method == "GET":
                return False

    return False


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

    result = convert_feed_to_documents(
        args.input, args.output_dir, source_label)

    print(f"generated_articles={len(result.documents)}")
    print(f"skipped_invalid_urls={result.skipped_invalid_urls}")
    print(f"skipped_invalid_metadata={result.skipped_invalid_metadata}")
    for document in result.documents:
        print(document.article.path)
