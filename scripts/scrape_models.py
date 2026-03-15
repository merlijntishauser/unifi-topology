#!/usr/bin/env python3
"""Scrape UniFi product model names from the official Ubiquiti store.

Fetches product data from store.ui.com and writes a JSON lookup file to
``src/unifi_topology/assets/models.json``.  This file maps device model
codes (as returned by the UniFi controller API) to their friendly product
names and store URLs.

Usage::

    python scripts/scrape_models.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

STORE_BASE = "https://store.ui.com"
STORE_HOME = f"{STORE_BASE}/us/en"
OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent / "src" / "unifi_topology" / "assets" / "models.json"
)

CATEGORIES = [
    "all-cloud-gateways",
    "all-switching",
    "all-wifi",
    "all-integrations",
    "all-advanced-hosting",
]


def _extract_build_id(session: requests.Session) -> str:
    """Extract the Next.js build ID from the store homepage."""
    resp = session.get(STORE_HOME, timeout=30)
    resp.raise_for_status()
    match = re.search(r'"buildId"\s*:\s*"([^"]+)"', resp.text)
    if not match:
        raise RuntimeError("Could not extract Next.js buildId from store homepage")
    return match.group(1)


def _fetch_category(
    session: requests.Session, build_id: str, category: str
) -> list[dict[str, Any]]:
    """Fetch all products in a store category."""
    url = f"{STORE_BASE}/_next/data/{build_id}/us/en/category/{category}.json"
    params = {"store": "us", "language": "en", "category": category}
    resp = session.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return _extract_products(data)


def _extract_products(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Walk the category JSON to find product entries."""
    products: list[dict[str, Any]] = []
    page_props = data.get("pageProps", {})

    for section in page_props.get("subCategories", []):
        for product in section.get("products", []):
            products.append(product)

    return products


def _product_url(slug: str) -> str:
    return f"{STORE_HOME}/products/{slug}"


def _build_model_entry(product: dict[str, Any]) -> tuple[str, dict[str, str]]:
    """Return (model_code, {name, url}) for a product."""
    sku = product.get("name", product.get("displaySku", ""))
    title = product.get("title", product.get("shortTitle", sku))
    slug = product.get("slug", "")
    return sku, {"name": title, "url": _product_url(slug)}


def scrape() -> dict[str, Any]:
    """Scrape all UniFi product models from the official store."""
    session = requests.Session()
    session.headers["User-Agent"] = "unifi-topology-model-scraper/1.0"

    print(f"Fetching build ID from {STORE_HOME} ...")
    build_id = _extract_build_id(session)
    print(f"Build ID: {build_id}")

    models: dict[str, dict[str, str]] = {}
    for category in CATEGORIES:
        print(f"Fetching category: {category} ...")
        products = _fetch_category(session, build_id, category)
        for product in products:
            sku, entry = _build_model_entry(product)
            if sku and sku not in models:
                models[sku] = entry
        print(f"  Found {len(products)} products ({len(models)} total unique)")

    return {
        "_meta": {
            "source": STORE_BASE,
            "scraped_at": datetime.now(UTC).isoformat(),
            "description": "UniFi device model codes to friendly names, scraped from the official Ubiquiti store.",
        },
        "models": dict(sorted(models.items())),
    }


def main() -> None:
    data = scrape()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"\nWrote {len(data['models'])} models to {OUTPUT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
