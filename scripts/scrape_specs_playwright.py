#!/usr/bin/env python3
"""Scrape specs from Ubiquiti store product pages using Playwright.

Fills in specs for products where the JSON API returns no technicalSpecification.
Outputs a specs_overrides.json that model_lookup.py merges at load time.

Usage::

    pip install playwright
    playwright install chromium
    python scripts/scrape_specs_playwright.py
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

MODELS_PATH = (
    Path(__file__).resolve().parent.parent / "src" / "unifi_topology" / "assets" / "models.json"
)
OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "unifi_topology"
    / "assets"
    / "specs_overrides.json"
)
STORE_BASE = "https://store.ui.com/us/en/products"


def _models_needing_specs() -> dict[str, str]:
    """Return {slug: representative_sku} for products with URL but no specs."""
    data = json.loads(MODELS_PATH.read_text())
    models = data["models"]
    slug_to_sku: dict[str, str] = {}
    for sku, entry in models.items():
        url = entry.get("url", "")
        if not url or entry.get("specs"):
            continue
        slug = url.rsplit("/", 1)[-1]
        if slug not in slug_to_sku:
            slug_to_sku[slug] = sku
    return slug_to_sku


def _parse_dimensions(raw: str) -> dict[str, float] | None:
    diameter = re.search(r"[⌀∅]\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm", raw)
    if diameter:
        return {"diameter": float(diameter.group(1)), "height": float(diameter.group(2))}
    wxdxh = re.search(r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm", raw)
    if wxdxh:
        a, b, c = float(wxdxh.group(1)), float(wxdxh.group(2)), float(wxdxh.group(3))
        # Store renders W x H x D for rack devices but our convention is W x D x H
        # (height = smallest dimension). If middle < last, swap to normalize.
        if b < c:
            return {"width": a, "depth": c, "height": b}
        return {"width": a, "depth": b, "height": c}
    return None


def _parse_weight(raw: str) -> float | None:
    kg = re.search(r"(\d+(?:\.\d+)?)\s*kg", raw, re.IGNORECASE)
    if kg:
        return round(float(kg.group(1)), 3)
    grams = re.findall(r"(\d+(?:\.\d+)?)\s*g\b", raw)
    if grams:
        return round(max(float(g) for g in grams) / 1000, 3)
    return None


def _parse_max_power(raw: str) -> float | None:
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*W\b", raw)
    if not matches:
        return None
    return max(float(m) for m in matches)


def _parse_rack_height(raw: str) -> int | None:
    match = re.search(r"(\d+)\s*U\b", raw)
    return int(match.group(1)) if match else None


def _clean_form_factor(raw: str) -> str | None:
    if not raw:
        return None
    return re.sub(r"\s*\n\(.*\)$", "", raw).strip() or None


def _extract_spec_value(page: Page, label: str) -> str | None:
    """Find a spec value by its label text on the page."""
    try:
        rows = page.query_selector_all("[class*='technicalSpecifications'] [class*='row']")
        if not rows:
            rows = page.query_selector_all("[class*='spec'] [class*='row']")
        for row in rows:
            text = row.inner_text()
            if label.lower() in text.lower():
                parts = text.split("\n")
                if len(parts) >= 2:
                    return parts[-1].strip()
    except Exception:  # noqa: BLE001 -- page structure varies; skip on any DOM error
        return None
    return None


def _extract_specs_from_snapshot(page: Page) -> dict[str, Any]:
    """Extract specs by evaluating JS to find spec key-value pairs."""
    try:
        result = page.evaluate("""() => {
            const specs = {};
            // Find all elements that look like spec rows (label + value pairs)
            const allElements = document.querySelectorAll('div, span, td, li');
            const labels = ['Dimensions', 'Weight', 'Max. Power Consumption',
                          'Form Factor', 'Mounting', 'Max Power Consumption'];
            for (const el of allElements) {
                const text = el.textContent?.trim() || '';
                for (const label of labels) {
                    if (text === label) {
                        // Get the next sibling or parent's next child
                        const parent = el.parentElement;
                        if (parent) {
                            const children = Array.from(parent.children);
                            const idx = children.indexOf(el);
                            if (idx >= 0 && idx + 1 < children.length) {
                                const value = children[idx + 1].textContent?.trim();
                                if (value) specs[label] = value;
                            }
                        }
                    }
                }
            }
            return specs;
        }""")
        return result or {}
    except Exception:
        return {}


def _scrape_product_specs(page: Page, slug: str) -> dict[str, Any]:
    """Navigate to a product page and extract specs."""
    url = f"{STORE_BASE}/{slug}"
    print(f"  Fetching {slug} ...", end=" ", flush=True)

    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
    except Exception:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
        except Exception as exc:
            print(f"FAILED ({exc})")
            return {}

    # Click "Technical" tab if present
    try:
        tech_btn = page.get_by_role("button", name="Technical")
        if tech_btn.is_visible(timeout=5000):
            tech_btn.click()
            time.sleep(1)
    except Exception:  # noqa: BLE001 -- tab may not exist on all product pages
        pass  # proceed without the Technical tab; specs may still be visible

    raw_specs = _extract_specs_from_snapshot(page)
    if not raw_specs:
        print("no specs found")
        return {}

    specs: dict[str, Any] = {}

    dim_raw = raw_specs.get("Dimensions", "")
    dims = _parse_dimensions(dim_raw)
    if dims:
        specs["dimensions_mm"] = dims

    weight_raw = raw_specs.get("Weight", "")
    weight = _parse_weight(weight_raw)
    if weight is not None:
        specs["weight_kg"] = weight

    power_raw = raw_specs.get("Max. Power Consumption") or raw_specs.get(
        "Max Power Consumption", ""
    )
    power = _parse_max_power(power_raw)
    if power is not None:
        specs["max_power_w"] = power

    form_raw = raw_specs.get("Form Factor") or raw_specs.get("Mounting", "")
    form = _clean_form_factor(form_raw)
    if form:
        specs["form_factor"] = form
    rack_u = _parse_rack_height(form or "")
    if rack_u is not None:
        specs["rack_height_u"] = rack_u

    print(f"OK ({len(specs)} fields)")
    return specs


def main() -> None:
    slug_to_sku = _models_needing_specs()
    print(f"Found {len(slug_to_sku)} unique product pages to scrape\n")

    overrides: dict[str, dict[str, Any]] = {}

    # Load existing overrides if present
    if OUTPUT_PATH.exists():
        existing = json.loads(OUTPUT_PATH.read_text())
        overrides = existing.get("specs", {})
        print(f"Loaded {len(overrides)} existing overrides\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = context.new_page()

        for slug, sku in sorted(slug_to_sku.items()):
            if slug in overrides and overrides[slug]:
                print(f"  Skipping {slug} (already has overrides)")
                continue
            specs = _scrape_product_specs(page, slug)
            if specs:
                overrides[slug] = specs

        browser.close()

    # Map SKUs to specs via their slug
    data = json.loads(MODELS_PATH.read_text())
    models = data["models"]
    sku_specs: dict[str, dict[str, Any]] = {}
    for sku, entry in models.items():
        url = entry.get("url", "")
        if not url or entry.get("specs"):
            continue
        slug = url.rsplit("/", 1)[-1]
        if slug in overrides:
            sku_specs[sku] = overrides[slug]

    output = {
        "_meta": {
            "description": (
                "Manual specs overrides for models where the store JSON API "
                "does not provide technicalSpecification data. Keyed by product slug."
            ),
        },
        "specs": dict(sorted(overrides.items())),
    }
    OUTPUT_PATH.write_text(json.dumps(output, indent=2) + "\n")
    print(f"\nWrote {len(overrides)} overrides to {OUTPUT_PATH}")
    print(f"Covers {len(sku_specs)} model entries in models.json")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)
