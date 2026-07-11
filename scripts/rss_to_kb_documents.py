#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"
DC_NS = "{http://purl.org/dc/elements/1.1/}"
MAX_SERVICE_LENGTH = 80
MAX_SOURCE_LENGTH = 40


def html_to_text(value: str) -> str:
    text = html.unescape(value)
    text = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(div|section|article|li|tr|h\d|ul|ol|table|pre)\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li\b[^>]*>", "- ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\xa0", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def truncate_text(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 1].rstrip() + "…"


def parse_pub_date(value: str) -> tuple[str, str]:
    if not value:
        return "", ""
    parsed = parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    iso_datetime = parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()
    iso_date = parsed.date().isoformat()
    return iso_date, iso_datetime


def normalize_service(categories: list[str]) -> str:
    return categories[0] if categories else ""


def build_document_text(item: ET.Element) -> str:
    title = (item.findtext("title") or "").strip()
    link = (item.findtext("link") or "").strip()
    author = (item.findtext(f"{DC_NS}creator") or "").strip()
    pub_date = (item.findtext("pubDate") or "").strip()
    guid = (item.findtext("guid") or "").strip()
    categories = [category.text.strip() for category in item.findall("category") if category.text]
    description = html_to_text(item.findtext("description") or "")
    content = html_to_text(item.findtext(f"{CONTENT_NS}encoded") or "")

    lines = [
        f"# {title}",
        "",
        f"- URL: {link}",
        f"- Author: {author}",
        f"- PublishedAt: {pub_date}",
        f"- Categories: {', '.join(categories)}",
        f"- Guid: {guid}",
    ]
    if description:
        lines.extend(["", "## Summary", "", description])
    if content:
        lines.extend(["", "## Content", "", content])
    return "\n".join(lines).strip() + "\n"


def build_metadata(
    item: ET.Element,
    source_label: str,
) -> dict[str, Any]:
    title = (item.findtext("title") or "").strip()
    link = (item.findtext("link") or "").strip()
    categories = [category.text.strip() for category in item.findall("category") if category.text]
    iso_date, _ = parse_pub_date((item.findtext("pubDate") or "").strip())
    source_host = urlparse(link).netloc
    doc_id = hashlib.sha1(f"{title}\n{link}".encode("utf-8")).hexdigest()[:16]

    return {
        "metadataAttributes": {
            "source": truncate_text(source_label, MAX_SOURCE_LENGTH),
            "published_date": iso_date,
            "service": truncate_text(normalize_service(categories), MAX_SERVICE_LENGTH),
            "source_host": source_host,
            "doc_id": doc_id,
        }
    }


def ensure_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}-{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def write_article(
    item: ET.Element,
    output_dir: Path,
    source_label: str,
    index: int,
) -> Path:
    iso_date, _ = parse_pub_date((item.findtext("pubDate") or "").strip())
    date_token = iso_date.replace("-", "") if iso_date else "unknown"
    file_name = f"{date_token}-{index:04d}.md"
    article_path = ensure_unique_path(output_dir / file_name)

    article_path.write_text(build_document_text(item), encoding="utf-8")
    metadata = build_metadata(item, source_label)
    metadata_path = article_path.with_name(article_path.name + ".metadata.json")
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return article_path


def convert_feed(input_path: Path, output_dir: Path, source_label: str) -> list[Path]:
    root = ET.fromstring(input_path.read_text(encoding="utf-8"))
    channel = root.find("channel")
    if channel is None:
        raise ValueError("RSS channel not found")

    output_dir.mkdir(parents=True, exist_ok=True)
    items = channel.findall("item")

    written_files: list[Path] = []
    for index, item in enumerate(items, start=1):
        written_files.append(write_article(item, output_dir, source_label, index))
    return written_files


def default_source_label(input_path: Path) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{input_path.stem}-{stamp}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert RSS XML into KB-ready article documents and metadata sidecar files."
    )
    parser.add_argument("input", type=Path, help="RSS XML file path")
    parser.add_argument("output_dir", type=Path, help="Directory for generated article files")
    parser.add_argument(
        "--source-label",
        default=None,
        help="Metadata source label. Default: <input-stem>-<current-utc-date>",
    )
    args = parser.parse_args()

    source_label = args.source_label or default_source_label(args.input)
    written_files = convert_feed(args.input, args.output_dir, source_label)
    print(f"generated_articles={len(written_files)}")
    for path in written_files:
        print(path)


if __name__ == "__main__":
    main()
