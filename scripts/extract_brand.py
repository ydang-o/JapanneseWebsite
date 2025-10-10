"""Extract brand items from a saved Mercari HTML snippet.

Usage example:
    python scripts/extract_brand.py chanel.html \
        web/frontend/src/data/brands/chanel.json --limit 40

The script parses list data within ``li[data-testid="item-cell"]`` nodes,
captures title, price, image and link information, and writes a JSON array
compatible with the frontend fallback datasets.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def extract_items(html: str, *, base_url: str | None, limit: int | None) -> list[dict]:
    """Parse raw HTML and return a list of product dictionaries."""

    soup = BeautifulSoup(html, "lxml")
    results: list[dict] = []

    def _class_contains(target: str) -> callable:
        return lambda value: bool(value and target in value.split())

    nodes: Iterable = soup.find_all("li", attrs={"data-testid": "item-cell"})

    for node in nodes:
        link = node.find("a", attrs={"data-testid": "thumbnail-link"})
        if not link:
            continue

        href = link.get("href") or ""
        full_href = urljoin(base_url, href) if base_url else href

        thumb = link.find("div", class_=_class_contains("merItemThumbnail"))
        item_id = thumb.get("id") if thumb and thumb.get("id") else None
        if not item_id and href:
            candidate = href.strip("/").split("/")[-1]
            if candidate:
                item_id = candidate

        img = link.find("img")
        image_src = img.get("src") if img else ""
        image_alt = img.get("alt") if img else ""

        title_tag = link.find(attrs={"data-testid": "thumbnail-item-name"})
        title = clean_text(title_tag.get_text(" ", strip=True)) if title_tag else ""

        price_span = link.find("span", class_=lambda val: bool(val and "number__" in val))
        price_text_raw = clean_text(price_span.get_text(" ", strip=True)) if price_span else ""
        price_value = None
        if price_text_raw:
            digits = re.sub(r"[^0-9]", "", price_text_raw)
            if digits:
                price_value = int(digits)

        if not any([title, price_text_raw, image_src]):
            continue

        item: dict = {
            "id": item_id or title or image_src,
            "title": title or clean_text(image_alt) or "商品",
            "href": full_href or href,
        }

        if price_value is not None:
            item["price"] = price_value
            item["priceText"] = f"¥{price_value:,}"
        elif price_text_raw:
            item["priceText"] = price_text_raw

        if image_src:
            item["image"] = {"src": image_src}
            if image_alt:
                item["image"]["alt"] = clean_text(image_alt)

        results.append(item)
        if limit and len(results) >= limit:
            break

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract brand dataset from HTML")
    parser.add_argument("html_path", type=Path, help="Input HTML file path")
    parser.add_argument("output_path", type=Path, help="Destination JSON file path")
    parser.add_argument("--base-url", default="https://jp.mercari.com", help="Base URL used to normalise item links")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of items to keep")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation")

    args = parser.parse_args()

    html = args.html_path.read_text(encoding="utf-8")
    items = extract_items(html, base_url=args.base_url, limit=args.limit)

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(
        json.dumps(items, ensure_ascii=False, indent=args.indent),
        encoding="utf-8",
    )

    print(f"Extracted {len(items)} items -> {args.output_path}")


if __name__ == "__main__":
    main()

