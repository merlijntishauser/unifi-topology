#!/usr/bin/env python3
"""Scrape UniFi product model names from official Ubiquiti sources.

Fetches product data from the official Ubiquiti store (store.ui.com) and
firmware platform codes from the firmware update API (fw-update.ubnt.com),
then writes a unified JSON lookup file to
``src/unifi_topology/assets/models.json``.

The output maps both store product SKUs (e.g. ``U6-Mesh``) and firmware
platform codes (e.g. ``U6M``) to friendly product names, store URLs,
documentation links, and firmware changelog URLs.

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
FIRMWARE_API = "https://fw-update.ubnt.com/api/firmware-latest"
OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "unifi_topology"
    / "assets"
    / "models.json"
)

STORE_CATEGORIES = [
    "all-cloud-gateways",
    "all-switching",
    "all-wifi",
    "all-integrations",
    "all-advanced-hosting",
]

# ── Firmware platform code → store product SKU ──────────────────────
# The UniFi controller API returns internal firmware platform codes in
# its ``model`` field, but the store uses product-line SKUs.  This table
# maps platform codes that cannot be derived algorithmically to their
# corresponding store SKUs.
#
# Sources:
#   - firmware platforms: fw-update.ubnt.com/api/firmware-latest
#   - store products:     store.ui.com
#
PLATFORM_TO_SKU: dict[str, str] = {
    # ── Access Points ───────────────────────────────────────────────
    "BZ2": "UAP",
    "BZ2LR": "UAP-LR",
    "U2HSR": "UAP-Outdoor+",
    "U2IW": "UAP-IW",
    "U2Lv2": "UAP-LR",
    "U2O": "UAP-Outdoor",
    "U2Sv2": "UAP",
    "U5O": "UAP-Outdoor5",
    "U6ENT": "U6-Enterprise",
    "U6ENTIW": "U6-Enterprise-IW",
    "U6EXT": "U6-Extender",
    "U6IW": "U6-IW",
    "U6M": "U6-Mesh",
    "U6MP": "U6-Mesh-Pro",
    "U7EDU": "U7-Lite",
    "U7HD": "UAP-HD",
    "U7IW": "U7-IW",
    "U7IWP": "U7-Pro-Wall",
    "U7LR": "U7-LR",
    "U7LT": "U6+",
    "U7MP": "U7-Pro-Max",
    "U7MSH": "U7-Mesh",
    "U7NHD": "UAP-nanoHD",
    "U7P": "U6-Pro",
    "U7PG2": "U7-Pro-XG",
    "U7PIW": "U7-Pro-XG-Wall",
    "U7PRO": "U7-Pro",
    "U7PROMAX": "U7-Pro-XGS",
    "U7SHD": "UAP-SHD",
    "U7UKU": "UK-Ultra",
    "UAP6MP": "U6-Mesh-Pro",
    "UAPL6": "U6+",
    "UAE6": "E7",
    "UAIW6": "U7-IW",
    "UAL6": "U7-Pro",
    "UALR6": "U7-LR",
    "UALR6v2": "U7-LR",
    "UALRPL6": "U7-Pro-XGS",
    "UAM6": "U7-Mesh",
    "UHDIW": "UAP-IW-HD",
    "UKPW": "UK-Ultra",
    "UFLHD": "UAP-FlexHD",
    "UWB-XG": "UWB-XG",
    # ── Cloud Gateways / Dream Machines ─────────────────────────────
    "UDM": "UDM",
    "UDMPRO": "UDM-Pro",
    "UDMB": "UDM-SE",
    "UDMA69B": "UDM-Pro-Max",
    "UGW3": "USG",
    "UGW4": "USG-Pro-4",
    "UGWXG": "USG-XG-8",
    "UDW": "UDW",
    "UX": "UX",
    "UXBSDM": "UX7",
    "UXG": "UCG-Ultra",
    "UXGA6AA": "UCG-Industrial",
    "UXGB": "UCG-Max",
    "UXGENT": "UXG-Enterprise",
    "UXGPRO": "UXG-Pro-US",
    "UXGPROV2": "UXG-Pro-US",
    # ── Switches ────────────────────────────────────────────────────
    "US8": "USW-8",
    "US8P60": "USW-8-PoE",
    "US8P150": "USW-8-150W",
    "US16P150": "USW-16-POE",
    "US24": "USW-24",
    "US24P250": "USW-24-POE",
    "US24P500": "USW-24-500W",
    "US24PL2": "USW-24-PoE",
    "US24PRO": "USW-Pro-24",
    "US24PRO2": "USW-Pro-24-POE",
    "US48": "USW-48",
    "US48P500": "USW-48-POE",
    "US48P750": "USW-48-750W",
    "US48PL2": "USW-48-PoE",
    "US48PRO": "USW-Pro-48",
    "US48PRO2": "USW-Pro-48-POE",
    "US624P": "USW-Enterprise-24-PoE",
    "US648P": "USW-Enterprise-48-PoE",
    "US68P": "USW-Enterprise-8-PoE",
    "US6XG150": "USW-Pro-Aggregation",
    "USC8": "USW-Ultra-60W",
    "USC8P450": "USW-Ultra-210W",
    "USF5P": "USW-Flex",
    "USFXG": "USW-Pro-XG-Aggregation",
    "USL8LP": "USW-Lite-8-PoE",
    "USL16LP": "USW-Lite-16-PoE",
    "USL8A": "USW-Lite-8-PoE",
    "USL8MP": "USW-Pro-8-PoE",
    "USLP8P": "USW-Pro-8-PoE",
    "USMINI": "USW-Flex-Mini",
    "USMINI2": "USW-Flex-Mini",
    "USMULT": "USW-WAN",
    "USAGGPRO": "USW-Aggregation",
    "USXG": "USW-Pro-XG-Aggregation",
    "S216150": "US-16-150W",
    "S224250": "US-24-250W",
    "S224500": "US-24-500W",
    "S248500": "US-48-500W",
    "S248750": "US-48-750W",
    "S28150": "US-8-150W",
    # Switch Pro Max / XG / HD series (firmware-only codes)
    "USL16P": "USW-Pro-Max-16-PoE",
    "USL16PB": "USW-Pro-Max-16-PoE",
    "USL24P": "USW-Pro-Max-24-PoE",
    "USL24PB": "USW-Pro-Max-24-PoE",
    "USL48P": "USW-Pro-Max-48-PoE",
    "USL48PB": "USW-Pro-Max-48-PoE",
    "USL24": "USW-Pro-Max-24",
    "USL24B": "USW-Pro-Max-24",
    "USL48": "USW-Pro-Max-48",
    "USL48B": "USW-Pro-Max-48",
    "USL16LPB": "USW-Pro-Max-16",
    "USPM16": "USW-Pro-Max-16",
    "USPM16P": "USW-Pro-Max-16-PoE",
    "USPM24": "USW-Pro-Max-24",
    "USPM24P": "USW-Pro-Max-24-PoE",
    "USPM48": "USW-Pro-Max-48",
    "USPM48P": "USW-Pro-Max-48-PoE",
    "USM8P": "USW-Pro-8-PoE",
    "USM8P60": "USW-Pro-8-PoE",
    "USM8P210": "USW-Ultra-210W",
    # ── Controllers ─────────────────────────────────────────────────
    "UCK": "UCK",
    "UCKG2": "UCK-G2",
    "UCKP": "UCK-G2-Plus",
    "UCI": "UCI",
    "UCXG": "CK-Enterprise",
    # ── Power / PDU ─────────────────────────────────────────────────
    "USPPDUHD": "USP-PDU-HD",
    "USPPDUP": "USP-PDU-Pro",
    "USPRPS": "USP-RPS",
    "USPRPSP": "USP-RPS",
    "UP1": "USP-Plug",
    "UP6": "USP-Strip",
    # ── LTE / Mobile ───────────────────────────────────────────────
    "ULTE": "U-LTE",
    "ULTEPUS": "U-LTE-Backup Pro",
    "ULTEPEU": "U-LTE",
    # ── Building Bridges ────────────────────────────────────────────
    "UBB": "UBB",
    "UBBXG": "UBB-XG",
    "UDB": "UDB-Pro",
    "UDBE802": "UDB-Pro-Sector",
    # ── Misc / accessories ──────────────────────────────────────────
    "UACCMPOEAF": "U-PoE-AF",
}


# ── Store scraping ──────────────────────────────────────────────────


def _extract_build_id(session: requests.Session) -> str:
    resp = session.get(STORE_HOME, timeout=30)
    resp.raise_for_status()
    match = re.search(r'"buildId"\s*:\s*"([^"]+)"', resp.text)
    if not match:
        raise RuntimeError("Could not extract Next.js buildId from store homepage")
    return match.group(1)


def _fetch_category(
    session: requests.Session, build_id: str, category: str
) -> list[dict[str, Any]]:
    url = f"{STORE_BASE}/_next/data/{build_id}/us/en/category/{category}.json"
    params = {"store": "us", "language": "en", "category": category}
    resp = session.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    products: list[dict[str, Any]] = []
    for section in data.get("pageProps", {}).get("subCategories", []):
        products.extend(section.get("products", []))
    return products


def _fetch_product_detail(
    session: requests.Session, build_id: str, slug: str, category: str
) -> dict[str, Any] | None:
    url = (
        f"{STORE_BASE}/_next/data/{build_id}/us/en"
        f"/category/{category}/products/{slug}.json"
    )
    params = {
        "store": "us",
        "language": "en",
        "category": category,
        "product": slug,
    }
    try:
        resp = session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        products = (
            data.get("pageProps", {}).get("collection", {}).get("products", [])
        )
        return products[0] if products else None
    except (requests.RequestException, IndexError, KeyError):
        return None


def _extract_documents(product: dict[str, Any]) -> dict[str, str]:
    docs: dict[str, str] = {}
    for doc in product.get("documents", []):
        url = doc.get("url", "")
        doc_type = doc.get("type", "")
        if doc_type == "Datasheet" and url:
            docs["datasheet"] = url
        elif doc_type == "InstallationGuide" and url:
            docs["guide"] = url
    return docs


def _product_url(slug: str) -> str:
    return f"{STORE_HOME}/products/{slug}"


# ── Firmware API ────────────────────────────────────────────────────


def _fetch_firmware_platforms(
    session: requests.Session,
) -> dict[str, str]:
    """Return {platform_code: changelog_url} from the firmware API."""
    resp = session.get(
        FIRMWARE_API,
        params={
            "filter": [
                "eq~~product~~unifi-firmware",
                "eq~~channel~~release",
            ],
        },
        timeout=30,
    )
    resp.raise_for_status()
    platforms: dict[str, str] = {}
    for entry in resp.json().get("_embedded", {}).get("firmware", []):
        plat = entry.get("platform", "")
        changelog = ""
        for link in entry.get("_links", {}).get("upload", []):
            if link.get("name") == "changelog":
                changelog = link.get("href", "")
        if plat:
            platforms[plat] = changelog
    return platforms


# ── Merge logic ─────────────────────────────────────────────────────


ModelEntry = dict[str, Any]


def _add_product(
    models: dict[str, ModelEntry],
    slug_to_category: dict[str, str],
    product: dict[str, Any],
    category: str,
) -> None:
    sku = product.get("name", product.get("displaySku", ""))
    title = product.get("title", product.get("shortTitle", sku))
    slug = product.get("slug", "")
    if not sku or sku in models:
        return
    models[sku] = {"name": title, "url": _product_url(slug)}
    slug_to_category[slug] = category


def _enrich_with_docs(
    models: dict[str, ModelEntry],
    slug_to_category: dict[str, str],
    session: requests.Session,
    build_id: str,
) -> None:
    print(f"  Fetching document links for {len(models)} products ...")
    for entry in models.values():
        slug = entry["url"].rsplit("/", 1)[-1]
        category = slug_to_category.get(slug, STORE_CATEGORIES[0])
        detail = _fetch_product_detail(session, build_id, slug, category)
        if not detail:
            continue
        docs = _extract_documents(detail)
        if docs:
            entry["docs"] = docs


def _build_store_models(
    session: requests.Session, build_id: str
) -> dict[str, ModelEntry]:
    """Fetch all store products and build {sku: entry} map."""
    models: dict[str, ModelEntry] = {}
    slug_to_category: dict[str, str] = {}

    for category in STORE_CATEGORIES:
        print(f"  Store category: {category} ...")
        products = _fetch_category(session, build_id, category)
        for product in products:
            _add_product(models, slug_to_category, product, category)
        print(f"    {len(products)} products ({len(models)} total)")

    _enrich_with_docs(models, slug_to_category, session, build_id)
    return models


def _find_store_entry(
    models: dict[str, ModelEntry], platform: str
) -> ModelEntry | None:
    """Find existing store entry for a firmware platform code."""
    if platform in models:
        return models[platform]
    sku = PLATFORM_TO_SKU.get(platform)
    if sku and sku in models:
        return models[sku]
    lower = platform.lower()
    return next((v for k, v in models.items() if k.lower() == lower), None)


def _add_firmware_entry(
    models: dict[str, ModelEntry], platform: str, changelog_url: str
) -> bool:
    """Add a firmware platform entry, linking to store data if available."""
    store = _find_store_entry(models, platform)
    if store is None:
        return False
    if platform in models:
        if changelog_url:
            store.setdefault("firmware_changelog", changelog_url)
    else:
        entry = dict(store)
        if changelog_url:
            entry["firmware_changelog"] = changelog_url
        models[platform] = entry
    return True


def _add_unmatched_platform(
    models: dict[str, ModelEntry], platform: str, changelog_url: str
) -> None:
    # Use the alias SKU as a friendlier name if available
    name = PLATFORM_TO_SKU.get(platform, platform)
    entry: ModelEntry = {"name": name}
    if changelog_url:
        entry["firmware_changelog"] = changelog_url
    models[platform] = entry


def _merge_firmware(
    models: dict[str, ModelEntry],
    platforms: dict[str, str],
) -> None:
    """Add firmware platform codes as additional keys into models dict."""
    unmatched: list[str] = []
    for platform, changelog_url in sorted(platforms.items()):
        if not _add_firmware_entry(models, platform, changelog_url):
            _add_unmatched_platform(models, platform, changelog_url)
            unmatched.append(platform)

    matched = len(platforms) - len(unmatched)
    _print_firmware_stats(matched, unmatched)


def _print_firmware_stats(matched: int, unmatched: list[str]) -> None:
    print(f"  Firmware: {matched} matched, {len(unmatched)} unmatched")
    if unmatched:
        print(f"  Unmatched platforms: {', '.join(unmatched[:20])}")
        if len(unmatched) > 20:
            print(f"    ... and {len(unmatched) - 20} more")


# ── Main ────────────────────────────────────────────────────────────


def scrape() -> dict[str, Any]:
    """Scrape UniFi product models from official Ubiquiti sources."""
    session = requests.Session()
    session.headers["User-Agent"] = "unifi-topology-model-scraper/1.0"

    print("1. Fetching store data ...")
    build_id = _extract_build_id(session)
    print(f"  Build ID: {build_id}")
    models = _build_store_models(session, build_id)

    print("2. Fetching firmware platforms ...")
    platforms = _fetch_firmware_platforms(session)
    print(f"  {len(platforms)} firmware platforms")
    _merge_firmware(models, platforms)

    return {
        "_meta": {
            "source": f"{STORE_BASE}, {FIRMWARE_API}",
            "scraped_at": datetime.now(UTC).isoformat(),
            "description": (
                "UniFi device model codes to friendly names. "
                "Scraped from the official Ubiquiti store and firmware API."
            ),
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
