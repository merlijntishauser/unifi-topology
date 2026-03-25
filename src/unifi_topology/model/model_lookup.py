"""Look up friendly product names for UniFi model codes.

Uses the bundled ``assets/models.json`` file (scraped from the official
Ubiquiti store and firmware API) to resolve model codes to human-readable
names, store URLs, documentation links, and firmware changelogs.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
_MODELS_PATH = _ASSETS_DIR / "models.json"
_OVERRIDES_PATH = _ASSETS_DIR / "specs_overrides.json"
_cache: dict[str, dict[str, Any]] | None = None


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _apply_spec_overrides(
    models: dict[str, dict[str, Any]],
    overrides: dict[str, dict[str, Any]],
) -> None:
    """Merge spec overrides into models that lack specs (by URL slug)."""
    for entry in models.values():
        if entry.get("specs"):
            continue
        url = entry.get("url", "")
        if not url:
            continue
        slug = url.rsplit("/", 1)[-1]
        specs = overrides.get(slug)
        if specs:
            entry["specs"] = specs


def _load_models() -> dict[str, dict[str, Any]]:
    """Load the model lookup table (cached after first call)."""
    global _cache  # noqa: PLW0603
    if _cache is not None:
        return _cache
    data = _load_json(_MODELS_PATH)
    models = data.get("models", {})
    if not models:
        logger.debug("Could not load model lookup table from %s", _MODELS_PATH)
    overrides = _load_json(_OVERRIDES_PATH).get("specs", {})
    if overrides:
        _apply_spec_overrides(models, overrides)
    _cache = models
    return _cache  # type: ignore[return-value]  # narrowing lost after global assignment


def _find_entry(model: str) -> dict[str, Any] | None:
    """Find the model entry, trying exact then case-insensitive match."""
    models = _load_models()
    entry = models.get(model)
    if entry is not None:
        return entry
    lower = model.lower()
    for key, value in models.items():
        if key.lower() == lower:
            return value
    return None


def lookup_model_name(model: str) -> str:
    """Return the friendly product name for a UniFi model code.

    Accepts both store SKUs (``U6-Mesh``) and firmware platform codes
    (``U6M``).  Returns an empty string if no match is found.
    """
    entry = _find_entry(model)
    return entry["name"] if entry else ""


def lookup_model_url(model: str) -> str:
    """Return the store product URL for a UniFi model code.

    Returns an empty string if no match is found.
    """
    entry = _find_entry(model)
    return entry.get("url", "") if entry else ""


def lookup_model_docs(model: str) -> dict[str, str]:
    """Return documentation links for a UniFi model code.

    Returns a dict with keys like ``datasheet`` and ``guide``,
    or an empty dict if no documentation is available.
    """
    entry = _find_entry(model)
    return entry.get("docs", {}) if entry else {}


def lookup_model_specs(model: str) -> dict[str, Any]:
    """Return physical device specs for a UniFi model code.

    Returns a dict with keys like ``dimensions_mm``, ``weight_kg``,
    ``max_power_w``, ``form_factor``, and ``rack_height_u``,
    or an empty dict if no specs are available.
    """
    entry = _find_entry(model)
    return entry.get("specs", {}) if entry else {}


def list_all_models() -> dict[str, dict[str, Any]]:
    """Return the complete model lookup table.

    Each key is a model code, and the value is a dict with keys like
    ``name``, ``url``, ``docs``, ``specs``, and ``firmware_changelog``.
    """
    return dict(_load_models())


def lookup_firmware_changelog(model: str) -> str:
    """Return the firmware release notes URL for a UniFi model code.

    Returns an empty string if no changelog is available.
    """
    entry = _find_entry(model)
    return entry.get("firmware_changelog", "") if entry else ""
