"""Parse physical device specs from UniFi store technicalSpecification values."""

from __future__ import annotations

import re
from typing import Any


def parse_dimensions(raw: str) -> dict[str, float] | None:
    """Parse dimensions string into mm values.

    Handles ``442 x 285 x 44 mm`` and diameter ``⌀206 x 46 mm``.
    """
    if not raw:
        return None
    diameter = re.search(r"[⌀∅]\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm", raw)
    if diameter:
        return {"diameter": float(diameter.group(1)), "height": float(diameter.group(2))}
    wxdxh = re.search(r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm", raw)
    if wxdxh:
        return {
            "width": float(wxdxh.group(1)),
            "depth": float(wxdxh.group(2)),
            "height": float(wxdxh.group(3)),
        }
    return None


def parse_weight(raw: str) -> float | None:
    """Parse weight string to kg."""
    if not raw:
        return None
    kg = re.search(r"(\d+(?:\.\d+)?)\s*kg", raw, re.IGNORECASE)
    if kg:
        return round(float(kg.group(1)), 3)
    grams = re.search(r"(\d+(?:\.\d+)?)\s*g\b", raw)
    if grams:
        return round(float(grams.group(1)) / 1000, 3)
    return None


def parse_max_power(raw: str) -> float | None:
    """Parse power consumption to max watts."""
    if not raw:
        return None
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*W\b", raw)
    if not matches:
        return None
    return max(float(m) for m in matches)


def parse_rack_height(raw: str) -> int | None:
    """Extract rack unit height from form-factor string."""
    if not raw:
        return None
    match = re.search(r"(\d+)\s*U\b", raw)
    return int(match.group(1)) if match else None


def _clean_form_factor(raw: str) -> str | None:
    """Clean form factor / mounting value."""
    if not raw:
        return None
    return re.sub(r"\s*\n\(.*\)$", "", raw).strip() or None


def _find_feature_value(features: list[dict[str, Any]], slug: str) -> str:
    """Find the first non-empty value for a feature slug."""
    for feature in features:
        if feature.get("feature", {}).get("slug") == slug:
            return feature.get("value", "")
    return ""


def extract_specs(product: dict[str, Any]) -> dict[str, Any]:
    """Extract and parse physical specs from a product detail response."""
    tech = product.get("technicalSpecification")
    if not tech:
        return {}
    features: list[dict[str, Any]] = []
    for section in tech.get("sections", []):
        features.extend(section.get("features", []))
    return _build_specs(features)


_SLUG_PARSERS: dict[str, tuple[str, Any]] = {
    "dimensions": ("dimensions_mm", parse_dimensions),
    "weight": ("weight_kg", parse_weight),
    "maxdot-power-consumption": ("max_power_w", parse_max_power),
}


def _build_specs(features: list[dict[str, Any]]) -> dict[str, Any]:
    """Build specs dict from a flat list of features."""
    specs: dict[str, Any] = {}
    for slug, (key, parser) in _SLUG_PARSERS.items():
        result = parser(_find_feature_value(features, slug))
        if result is not None:
            specs[key] = result
    _apply_form_factor(specs, features)
    return specs


def _apply_form_factor(specs: dict[str, Any], features: list[dict[str, Any]]) -> None:
    form = _clean_form_factor(_find_feature_value(features, "form-factor"))
    if not form:
        form = _clean_form_factor(_find_feature_value(features, "mounting"))
    if form:
        specs["form_factor"] = form
    rack_u = parse_rack_height(form or "")
    if rack_u is not None:
        specs["rack_height_u"] = rack_u
